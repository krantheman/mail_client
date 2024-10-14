# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re
import frappe
import socket
from frappe import _
from typing import Literal
from email import message_from_string
from mail.utils import get_host_by_ip
from frappe.query_builder import Interval
from frappe.model.document import Document
from email.mime.multipart import MIMEMultipart
from frappe.query_builder.functions import Now
from frappe.utils import now, time_diff_in_seconds


class SpamCheckLog(Document):
	@staticmethod
	def clear_old_logs(days=14):
		log = frappe.qb.DocType("Spam Check Log")
		frappe.db.delete(log, filters=(log.creation < (Now() - Interval(days=days))))

	def validate(self) -> None:
		if self.is_new():
			self.set_source_ip_address()
			self.set_source_host()
			self.scan_message()

	def set_source_ip_address(self) -> None:
		"""Sets the source IP address"""

		self.source_ip_address = frappe.local.request_ip

	def set_source_host(self) -> None:
		"""Sets the source host"""

		self.source_host = get_host_by_ip(self.source_ip_address)

	def scan_message(self) -> None:
		"""Scans the message for spam"""

		mail_settings = frappe.get_cached_doc("Mail Settings")

		if not mail_settings.enable_spam_detection:
			frappe.throw(_("Spam Detection is disabled"))

		spamd_host = mail_settings.spamd_host
		spamd_port = mail_settings.spamd_port
		scanning_mode = mail_settings.scanning_mode
		hybrid_scanning_threshold = mail_settings.hybrid_scanning_threshold

		response = None
		self.started_at = now()

		if scanning_mode == "Hybrid Approach":
			message_without_attachments = get_message_without_attachments(self.message)
			initial_response = scan_message(spamd_host, spamd_port, message_without_attachments)
			initial_spam_score = extract_spam_score(initial_response)

			if initial_spam_score < hybrid_scanning_threshold:
				response = initial_response

		elif scanning_mode == "Exclude Attachments":
			self.message = get_message_without_attachments(self.message)

		response = response or scan_message(spamd_host, spamd_port, self.message)
		self.spamd_response = response
		self.scanning_mode = scanning_mode
		self.hybrid_scanning_threshold = hybrid_scanning_threshold
		self.spam_score = extract_spam_score(response)
		self.completed_at = now()
		self.duration = time_diff_in_seconds(self.completed_at, self.started_at)

	def is_spam(self, message_type: Literal["Inbound", "Outbound"]) -> bool:
		"""Returns True if the message is spam else False"""

		max_spam_score_field = (
			"max_spam_score_for_outbound"
			if message_type == "Outbound"
			else "max_spam_score_for_inbound"
		)
		max_spam_score = frappe.db.get_single_value(
			"Mail Settings", max_spam_score_field, cache=True
		)

		return self.spam_score > max_spam_score


def create_spam_check_log(message: str) -> SpamCheckLog:
	"""Creates a Spam Check Log document"""

	doc = frappe.new_doc("Spam Check Log")
	doc.message = message
	doc.insert(ignore_permissions=True)

	return doc


def get_message_without_attachments(message: str) -> str:
	"""Returns the message without attachments"""

	parsed_message = message_from_string(message)
	message_without_attachments = MIMEMultipart()

	for header, value in parsed_message.items():
		message_without_attachments[header] = value

	for part in parsed_message.walk():
		if part.get_content_maintype() == "multipart":
			continue
		if part.get("Content-Disposition") is None:
			message_without_attachments.attach(part)

	return message_without_attachments.as_string()


def scan_message(host: str, port: int, message: str) -> str:
	"""Scans the message for spam"""

	try:
		with socket.create_connection((host, port), timeout=30) as sock:
			sock.settimeout(10)
			command = "SYMBOLS SPAMC/1.5\r\n\r\n"
			sock.sendall(command.encode("utf-8"))
			sock.sendall(message.encode("utf-8"))
			sock.shutdown(socket.SHUT_WR)

			response = ""
			while True:
				try:
					data = sock.recv(4096)
					if not data:
						break
					response += data.decode("utf-8")
				except socket.timeout:
					frappe.throw(
						_("Timed out waiting for response from SpamAssassin."),
						title=_("Spam Detection Failed"),
					)

	except ConnectionRefusedError:
		frappe.throw(
			_(
				"Could not connect to SpamAssassin (spamd). Please ensure it's running on {0}:{1}"
			).format(host, port),
			title=_("Spam Detection Failed"),
		)

	if not response:
		error_steps = [
			_("1. Ensure the correct IP address is allowed to connect to SpamAssassin."),
			_(
				"2. Verify that the SpamAssassin service is running and accepting connections on port {0}."
			).format(port),
			_(
				"3. Review SpamAssassin logs for any unauthorized connection attempts or permission errors."
			),
		]
		formatted_error_steps = "".join(f"<hr/>{step}" for step in error_steps)
		frappe.throw(
			_(
				"SpamAssassin did not return the expected response. This may indicate a permission issue or an unauthorized connection. Please check the following: {0}"
			).format(formatted_error_steps),
			title=_("Spam Detection Failed"),
			wide=True,
		)

	return response


def extract_spam_score(spamd_response: str) -> float:
	"""Extracts the spam score from the spamd response"""

	if match := re.search(r"Spam:.*?;\s*(-?\d+\.\d+)\s*/", spamd_response):
		return float(match.group(1))

	frappe.throw(_("Spam score not found in output."), title=_("Spam Detection Failed"))