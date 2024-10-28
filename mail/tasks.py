import frappe
from mail.utils import enqueue_job
from mail.mail.doctype.incoming_mail.incoming_mail import fetch_emails_from_mail_server
from mail.mail.doctype.outgoing_mail.outgoing_mail import (
	transfer_emails_to_mail_server,
	fetch_and_update_delivery_statuses,
)


def enqueue_transfer_emails_to_mail_server() -> None:
	"Called by the scheduler to enqueue the `transfer_emails_to_mail_server` job."

	frappe.session.user = "Administrator"
	enqueue_job(transfer_emails_to_mail_server, queue="long")


@frappe.whitelist()
def enqueue_fetch_and_update_delivery_statuses() -> None:
	"Called by the scheduler to enqueue the `fetch_and_update_delivery_statuses` job."

	frappe.session.user = "Administrator"
	enqueue_job(fetch_and_update_delivery_statuses, queue="long")


@frappe.whitelist()
def enqueue_fetch_emails_from_mail_server() -> None:
	"Called by the scheduler to enqueue the `fetch_emails_from_mail_server` job."

	frappe.session.user = "Administrator"
	for mail_domain in frappe.db.get_all(
		"Mail Domain", filters={"enabled": 1, "verified": 1}, pluck="name"
	):
		enqueue_job(fetch_emails_from_mail_server, queue="long", domain_name=mail_domain)
