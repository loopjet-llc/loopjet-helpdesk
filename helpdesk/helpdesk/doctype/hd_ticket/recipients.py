from __future__ import annotations

from email.utils import parseaddr
import re
from typing import Any

import frappe
from frappe import _


EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def normalize_email(value: Any) -> str:
    """Return a normalized email address or an empty string."""
    if not value:
        return ""
    email = parseaddr(str(value))[1].strip().lower()
    return email if EMAIL_PATTERN.fullmatch(email) else ""


def _requester_for_ticket(ticket) -> dict[str, Any] | None:
    email = normalize_email(ticket.raised_by)
    contact = None
    if ticket.contact:
        contact = frappe.db.get_value(
            "Contact",
            ticket.contact,
            ["full_name", "email_id", "user"],
            as_dict=True,
        )
        if not email and contact:
            email = normalize_email(contact.user or contact.email_id)

    if not email:
        return None

    full_name = frappe.db.get_value("User", email, "full_name")
    contact_email = normalize_email(contact.user or contact.email_id) if contact else ""
    label = (
        full_name or (contact.full_name if contact_email == email else None) or email
    )
    return {
        "email": email,
        "label": label,
        "is_requester": True,
    }


def get_public_comment_recipients(ticket) -> dict[str, Any]:
    """Resolve the mandatory requester and selectable users of the same customer."""
    requester = _requester_for_ticket(ticket)
    if not requester:
        frappe.throw(
            _("The ticket creator has no valid email address."),
            frappe.ValidationError,
        )

    additional: list[dict[str, Any]] = []
    if not ticket.customer:
        return {"requester": requester, "additional": additional}

    contact_names = frappe.get_all(
        "Dynamic Link",
        filters={
            "parenttype": "Contact",
            "parentfield": "links",
            "link_doctype": "HD Customer",
            "link_name": ticket.customer,
        },
        pluck="parent",
    )
    if not contact_names:
        return {"requester": requester, "additional": additional}

    contacts = frappe.get_all(
        "Contact",
        filters={"name": ["in", contact_names]},
        fields=["name", "full_name", "email_id", "user"],
    )
    user_names = [contact.user for contact in contacts if contact.user]
    users = (
        frappe.get_all(
            "User",
            filters={
                "name": ["in", user_names],
                "enabled": 1,
                "user_type": "Website User",
            },
            fields=["name", "full_name", "user_image"],
        )
        if user_names
        else []
    )
    users_by_name = {user.name: user for user in users}
    seen = {requester["email"]}

    for contact in contacts:
        user = users_by_name.get(contact.user)
        if not user:
            continue
        email = normalize_email(user.name or contact.email_id)
        if not email or email in seen:
            continue
        seen.add(email)
        additional.append(
            {
                "email": email,
                "label": user.full_name or contact.full_name or email,
                "image": user.user_image,
                "is_requester": False,
            }
        )

    additional.sort(key=lambda recipient: recipient["label"].casefold())
    return {"requester": requester, "additional": additional}


def validate_additional_recipients(
    recipient_options: dict[str, Any], selected: list[str] | None
) -> list[str]:
    allowed = {
        recipient["email"]
        for recipient in recipient_options.get("additional", [])
        if recipient.get("email")
    }
    normalized = []
    for value in selected or []:
        email = normalize_email(value)
        if not email or email not in allowed:
            frappe.throw(
                _("One or more selected recipients are not part of this customer."),
                frappe.PermissionError,
            )
        if email not in normalized:
            normalized.append(email)
    return normalized
