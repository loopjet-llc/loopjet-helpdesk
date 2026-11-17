"""Fill legacy customer ownership when the original sender belongs to the team."""

import frappe

from helpdesk.customer_team import team_member_for_raiser


def execute():
    tickets = frappe.get_all(
        "HD Ticket",
        filters={"customer_assignee": ["is", "not set"], "customer": ["is", "set"]},
        fields=["name", "customer", "raised_by"],
        limit_page_length=0,
    )
    for ticket in tickets:
        assignee = team_member_for_raiser(ticket.customer, ticket.raised_by)
        if assignee:
            frappe.db.set_value(
                "HD Ticket",
                ticket.name,
                "customer_assignee",
                assignee,
                update_modified=False,
            )
