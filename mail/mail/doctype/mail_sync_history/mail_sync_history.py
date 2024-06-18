# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from typing import Optional
from frappe.model.document import Document


class MailSyncHistory(Document):
	def before_insert(self) -> None:
		self.validate_duplicate()

	def validate_duplicate(self) -> None:
		"""Validate if the Mail Sync History already exists."""

		if frappe.db.exists(
			"Mail Sync History",
			{"source": self.source, "user": self.user, "mailbox": self.mailbox},
		):
			frappe.throw(_("Mail Sync History already exists for this source, user and mailbox"))


def create_mail_sync_history(
	source: str,
	user: str,
	mailbox: str,
	last_sync_at: Optional[str] = None,
	commit: bool = False,
) -> "MailSyncHistory":
	"""Create a Mail Sync History."""

	doc = frappe.new_doc("Mail Sync History")
	doc.source = source
	doc.user = user
	doc.mailbox = mailbox
	doc.last_sync_at = last_sync_at
	doc.insert(ignore_permissions=True)

	if commit:
		frappe.db.commit()

	return doc


def get_mail_sync_history(source: str, user: str, mailbox: str) -> "MailSyncHistory":
	"""Returns the Mail Sync History for the given source, user and mailbox."""

	if name := frappe.db.exists(
		"Mail Sync History", {"source": source, "user": user, "mailbox": mailbox}
	):
		return frappe.get_doc("Mail Sync History", name)

	return create_mail_sync_history(source, user, mailbox, commit=True)