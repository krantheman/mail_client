// Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mail Agent", {
	refresh(frm) {
		frm.trigger("add_actions");
	},

	add_actions(frm) {
		if (frm.doc.outgoing) {
			frm.add_custom_button(__("Get Delivery Status"), () => {
                frm.trigger("get_delivery_status");
            }, __("Actions"));
		}

		if (frm.doc.incoming) {
			frm.add_custom_button(__("Get Incoming Mails"), () => {
                frm.trigger("get_incoming_mails");
            }, __("Actions"));

            frm.add_custom_button(__("Update Virtual Domains"), () => {
                frm.trigger("update_virtual_domains");
            }, __("Actions"));

            frm.add_custom_button(__("Update Virtual Mailboxes"), () => {
                frm.trigger("update_virtual_mailboxes");
            }, __("Actions"));

			frm.add_custom_button(__("Update Virtual Aliases"), () => {
                frm.trigger("update_virtual_aliases");
            }, __("Actions"));
        }
    },

	get_delivery_status(frm) {
		frappe.call({
			method: "mail.mail.doctype.outgoing_mail.outgoing_mail.get_delivery_status",
			args: {
				agents: frm.doc.agent,
			},
			freeze: true,
			freeze_message: __("Getting Delivery Status..."),
			callback: () => {
				frappe.show_alert({
					message: __("Get Delivery Status Job has been started in the background."),
					indicator: "green",
				});
			}
		});
	},

	get_incoming_mails(frm) {
        frappe.call({
			method: "mail.mail.doctype.incoming_mail.incoming_mail.get_incoming_mails",
			args: {
				agents: frm.doc.agent,
			},
			freeze: true,
			freeze_message: __("Receiving Mails..."),
			callback: () => {
				frappe.show_alert({
					message: __("Get Incoming Mails Job has been started in the background."),
					indicator: "green",
				});
			}
		});
    },

	update_virtual_domains(frm) {
        frappe.call({
			method: "mail.mail.doctype.mail_domain.mail_domain.update_virtual_domains",
			args: {
				agents: frm.doc.agent,
			},
			freeze: true,
			freeze_message: __("Updating Virtual Domains..."),
			callback: () => {
				frappe.show_alert({
					message: __("Update Virtual Domains Job has been started in the background."),
					indicator: "green",
				});
			}
		});
    },

	update_virtual_mailboxes(frm) {
        frappe.call({
			method: "mail.mail.doctype.mailbox.mailbox.update_virtual_mailboxes",
			args: {
				agents: frm.doc.agent,
			},
			freeze: true,
			freeze_message: __("Updating Virtual Mailboxes..."),
			callback: () => {
				frappe.show_alert({
					message: __("Update Virtual Mailboxes Job has been started in the background."),
					indicator: "green",
				});
			}
		});
    },

	update_virtual_aliases(frm) {
        frappe.call({
			method: "mail.mail.doctype.mail_alias.mail_alias.update_virtual_aliases",
			args: {
				agents: frm.doc.agent,
			},
			freeze: true,
			freeze_message: __("Updating Virtual Aliases..."),
			callback: () => {
				frappe.show_alert({
					message: __("Update Virtual Aliases Job has been started in the background."),
					indicator: "green",
				});
			}
		});
    },
});