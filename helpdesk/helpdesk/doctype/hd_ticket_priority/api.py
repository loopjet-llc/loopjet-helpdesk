import frappe


@frappe.whitelist()
def get_active():
    """Expose selectable priorities to authenticated helpdesk customers."""
    frappe.has_permission("HD Ticket", "read", throw=True)
    return frappe.get_all(
        "HD Ticket Priority",
        filters={"disabled": 0},
        fields=["name", "level", "description"],
    )
