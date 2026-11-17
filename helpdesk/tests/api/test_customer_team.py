"""Company team visibility, customer assignment, and portal mentions."""

from unittest.mock import patch

import frappe
from frappe.client import set_value as client_set_value
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.customer_team import assign, get_members, get_projects
from helpdesk.api.doc import get_list_data
from helpdesk.customer_team import mentioned_users
from helpdesk.patches.backfill_customer_assignee_from_raiser import (
    execute as backfill_owners,
)
from helpdesk.test_utils import (
    create_contact,
    create_customer,
    default_template_rows,
    make_ticket,
    make_agent_manager,
    other_priority,
    set_default_template_rows,
    unique_email,
    unique_name,
)


class TestCustomerTeam(FrappeTestCase):
    def test_grouped_projects_can_collaborate_without_leaking_other_customers(self):
        frappe.set_user("Administrator")
        a = create_contact("Team A", "team-a@example.com")
        b = create_contact("Team B", "team-b@example.com")
        outsider = create_contact("Other Team", "other-team@example.com")
        company = create_customer("Team Company", [{"contact_name": a["contact"]}])
        project = create_customer("Team Project", [{"contact_name": b["contact"]}])
        other = create_customer(
            "Other Company", [{"contact_name": outsider["contact"]}]
        )
        company.collaboration_team = company.name
        company.save()
        project.collaboration_team = company.name
        project.project_label = "CloudMensa"
        project.save()
        company.project_label = "DHW ERP"
        company.save()

        ticket = make_ticket(
            customer=project.name,
            contact=b["contact"],
            raised_by=b["user"],
            via_customer_portal=1,
        )
        self.assertEqual(ticket.customer_assignee, b["user"])
        unrelated = make_ticket(
            customer=other.name,
            contact=outsider["contact"],
            raised_by=outsider["user"],
            via_customer_portal=1,
        )

        frappe.set_user(a["user"])
        project_as_customer = frappe.get_doc("HD Customer", project.name)
        project_as_customer.collaboration_team = other.name
        with self.assertRaises(frappe.PermissionError):
            project_as_customer.save(ignore_permissions=True)
        project_as_customer.reload()
        project_as_customer.project_label = "Other name"
        with self.assertRaises(frappe.PermissionError):
            project_as_customer.save(ignore_permissions=True)
        self.assertEqual(
            {row["label"] for row in get_projects()}, {"DHW ERP", "CloudMensa"}
        )
        project_list = get_list_data(
            "HD Ticket",
            filters=[["customer", "=", company.name]],
            project_customer=project.name,
            show_customer_portal_fields=True,
            is_default=True,
        )
        self.assertIn(ticket.name, {row.name for row in project_list["data"]})
        self.assertEqual(project_list["total_count"], 1)
        self.assertEqual(project_list["data"][0].customer, project.name)
        all_projects = get_list_data(
            "HD Ticket",
            filters=[["customer", "=", other.name]],
            project_customer="",
            show_customer_portal_fields=True,
        )
        self.assertIn(ticket.name, {row.name for row in all_projects["data"]})
        self.assertNotIn(unrelated.name, {row.name for row in all_projects["data"]})
        with self.assertRaises(frappe.PermissionError):
            get_list_data(
                "HD Ticket",
                project_customer=other.name,
                show_customer_portal_fields=True,
            )
        visible = set(frappe.get_list("HD Ticket", pluck="name"))
        self.assertIn(ticket.name, visible)
        self.assertNotIn(unrelated.name, visible)
        self.assertTrue(frappe.has_permission("HD Ticket", "read", ticket.name))
        self.assertEqual(
            {row["user"] for row in get_members(ticket.name)},
            {a["user"], b["user"]},
        )

        with patch("helpdesk.api.customer_team.email_team_member") as mail:
            assign(ticket.name, a["user"])
            assign(ticket.name, b["user"])
            assign(ticket.name, b["user"])
        self.assertEqual(mail.call_count, 1)
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "customer_assignee"),
            b["user"],
        )
        with self.assertRaises(frappe.PermissionError):
            assign(ticket.name, outsider["user"])

        frappe.set_user("Administrator")
        manager = make_agent_manager("customer-owner-manager")
        with self.set_user(manager):
            self.assertEqual(
                {member["user"] for member in get_members(ticket.name)},
                {a["user"], b["user"]},
            )
            with patch("helpdesk.api.customer_team.email_team_member") as mail:
                assign(ticket.name, a["user"])
            mail.assert_called_once()
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "customer_assignee"),
            a["user"],
        )
        frappe.set_user(a["user"])

        mention = f'<p><span class="mention" data-type="mention" data-id="{b["user"]}">@Team B</span></p>'
        self.assertEqual(mentioned_users(project.name, mention), [b["user"]])
        with self.assertRaises(frappe.PermissionError):
            mentioned_users(
                project.name,
                f'<span class="mention" data-type="mention" data-id="{outsider["user"]}">@Other</span>',
            )
        with patch(
            "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.email_team_member"
        ) as mail:
            communication = frappe.get_doc(
                "HD Ticket", ticket.name
            ).create_communication_via_contact(mention)
        self.assertTrue(frappe.db.exists("Communication", communication))
        mail.assert_called_once()
        self.assertEqual(mail.call_args.args[1], b["user"])

        frappe.set_user("Administrator")
        previous_rows = default_template_rows()
        self.addCleanup(set_default_template_rows, previous_rows)
        self.addCleanup(frappe.set_user, "Administrator")
        set_default_template_rows(
            [row for row in previous_rows if row["fieldname"] != "priority"]
            + [
                {
                    "fieldname": "priority",
                    "visible_to": "Everyone",
                    "editable_after_creation": 1,
                }
            ]
        )
        frappe.set_user(a["user"])
        new_priority = other_priority(ticket.priority)
        client_set_value("HD Ticket", ticket.name, "priority", new_priority)
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "priority"), new_priority
        )

        frappe.set_user("Administrator")
        frappe.db.set_value("HD Ticket", ticket.name, "status", "Closed")
        frappe.set_user(a["user"])
        with self.assertRaises(frappe.PermissionError):
            assign(ticket.name, None)

        with self.set_user(manager):
            with patch("helpdesk.api.customer_team.email_team_member"):
                assign(ticket.name, b["user"])
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "customer_assignee"),
            b["user"],
        )

        frappe.set_user(outsider["user"])
        self.assertEqual({row["customer"] for row in get_projects()}, {other.name})
        with self.assertRaises(frappe.PermissionError):
            get_members(ticket.name)
        self.assertFalse(frappe.has_permission("HD Ticket", "read", ticket.name))

    def test_backfill_uses_original_team_member_without_overwriting_manual_owner(self):
        frappe.set_user("Administrator")
        self.addCleanup(frappe.set_user, "Administrator")
        creator = create_contact("Creator", unique_email("creator"))
        colleague = create_contact("Colleague", unique_email("colleague"))
        customer = create_customer(
            unique_name("Customer"),
            [
                {"contact_name": creator["contact"]},
                {"contact_name": colleague["contact"]},
            ],
        )
        missing = make_ticket(customer=customer.name, raised_by=creator["user"])
        chosen = make_ticket(
            customer=customer.name,
            raised_by=creator["user"],
            customer_assignee=colleague["user"],
        )
        self.assertEqual(missing.customer_assignee, creator["user"])
        self.assertEqual(chosen.customer_assignee, colleague["user"])
        frappe.db.set_value(
            "HD Ticket",
            missing.name,
            "customer_assignee",
            None,
            update_modified=False,
        )

        backfill_owners()

        self.assertEqual(
            frappe.db.get_value("HD Ticket", missing.name, "customer_assignee"),
            creator["user"],
        )
        self.assertEqual(
            frappe.db.get_value("HD Ticket", chosen.name, "customer_assignee"),
            colleague["user"],
        )
