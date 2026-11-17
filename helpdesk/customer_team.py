"""Company-scoped customer collaboration without changing support-agent routing."""

import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import get_fullname
from html import escape

from helpdesk.utils import get_customers


def team_accounts(customer: str | None) -> list[str]:
    """Return project accounts explicitly linked to one company team."""
    if not customer:
        return []
    team = frappe.db.get_value("HD Customer", customer, "collaboration_team")
    if not team:
        return [customer]
    return frappe.get_all(
        "HD Customer", filters={"collaboration_team": team}, pluck="name"
    )


def is_team_member(customer: str | None, user: str | None = None) -> bool:
    """Membership in any linked project account grants company-team access."""
    accounts = set(team_accounts(customer))
    if not accounts:
        return False
    user = user or frappe.session.user
    return bool(accounts.intersection(get_customers(user)))


def visible_team_accounts(user: str) -> list[str]:
    """Only explicitly grouped accounts broaden ordinary member visibility."""
    memberships = get_customers(user)
    grouped = set()
    for customer in memberships:
        if frappe.db.get_value("HD Customer", customer, "collaboration_team"):
            grouped.update(team_accounts(customer))
    return sorted(grouped)


def project_accounts_for_user(user: str) -> list[str]:
    """Accounts whose tickets this portal user can see."""
    return sorted(set(get_customers(user)) | set(visible_team_accounts(user)))


def project_options(user: str) -> list[dict]:
    accounts = project_accounts_for_user(user)
    if not accounts:
        return []
    customers = frappe.get_all(
        "HD Customer",
        filters={"name": ["in", accounts]},
        fields=["name", "project_label"],
    )
    return sorted(
        (
            {"customer": row.name, "label": row.project_label or row.name}
            for row in customers
        ),
        key=lambda row: row["label"].casefold(),
    )


def team_members(customer: str | None) -> list[dict]:
    """Enabled portal users linked to contacts in this ticket's company team."""
    accounts = team_accounts(customer)
    if not accounts:
        return []
    contact_names = frappe.get_all(
        "HD Customer Member",
        filters={"parent": ["in", accounts], "parenttype": "HD Customer"},
        pluck="contact_name",
    )
    if not contact_names:
        return []
    contacts = frappe.get_all(
        "Contact",
        filters={"name": ["in", contact_names]},
        fields=["name", "user", "full_name"],
    )
    candidates = {row.user for row in contacts}
    candidates.discard(None)
    candidates.discard("")
    if not candidates:
        return []
    users = frappe.get_all(
        "User",
        filters={
            "name": ["in", list(candidates)],
            "enabled": 1,
            "user_type": "Website User",
        },
        fields=["name", "full_name", "user_image"],
    )
    return sorted(
        (
            {
                "user": row.name,
                "label": row.full_name or row.name,
                "image": row.user_image,
            }
            for row in users
        ),
        key=lambda row: row["label"].casefold(),
    )


def mentioned_users(customer: str | None, html: str) -> list[str]:
    """Accept only real mention nodes naming enabled members of this team."""
    mentions = {
        node.get("data-id")
        for node in BeautifulSoup(html or "", "html.parser").select(
            'span.mention[data-type="mention"]'
        )
    }
    mentions.discard(None)
    if not mentions:
        return []
    allowed = {member["user"] for member in team_members(customer)}
    if not mentions.issubset(allowed):
        frappe.throw(
            _("You can only mention members of this company team."),
            frappe.PermissionError,
        )
    return sorted(mentions)


def email_team_member(ticket, recipient: str, action: str, anchor: str = "") -> None:
    """Queue one transactional message linked to the relevant ticket event."""
    actor = escape(get_fullname(frappe.session.user))
    subject = escape(ticket.subject or "")
    url = ticket.portal_uri
    if anchor:
        url += f"#{anchor}"
    if action == "assignment":
        detail = _("{0} assigned ticket #{1} to you.").format(actor, ticket.name)
    else:
        detail = _("{0} mentioned you in ticket #{1}.").format(actor, ticket.name)
    frappe.sendmail(
        recipients=[recipient],
        subject=_("Ticket #{0}: {1}").format(ticket.name, ticket.subject),
        message=f'<p>{detail}</p><p>{subject}</p><p><a href="{escape(url)}">{_("Open ticket")}</a></p>',
        reference_doctype="HD Ticket",
        reference_name=ticket.name,
        delayed=True,
    )
