"""Customer portal team picker and customer-side ticket assignment."""

import frappe
from frappe import _

from helpdesk.customer_team import email_team_member, is_team_member, team_members


@frappe.whitelist()
def get_members(ticket: str) -> list[dict]:
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)
    customer = frappe.db.get_value("HD Ticket", ticket, "customer")
    if not is_team_member(customer):
        frappe.throw(
            _("You are not a member of this company team."), frappe.PermissionError
        )
    return team_members(customer)


@frappe.whitelist()
def assign(ticket: str, assignee: str | None = None) -> dict:
    frappe.has_permission("HD Ticket", "read", ticket, throw=True)
    doc = frappe.get_doc("HD Ticket", ticket)
    if not is_team_member(doc.customer):
        frappe.throw(
            _("You are not a member of this company team."), frappe.PermissionError
        )
    assignee = assignee or None
    if assignee and assignee not in {
        member["user"] for member in team_members(doc.customer)
    }:
        frappe.throw(
            _("The assignee must belong to this company team."), frappe.PermissionError
        )
    if doc.customer_assignee == assignee:
        return {"assignee": assignee}
    doc.customer_assignee = assignee
    doc.flags.ignore_customer_edit_guard = True
    doc.flags.ignore_permlevel_for_fields = ["customer_assignee"]
    doc.save(ignore_permissions=True)
    if assignee and assignee != frappe.session.user:
        email_team_member(doc, assignee, "assignment")
    return {"assignee": assignee}
