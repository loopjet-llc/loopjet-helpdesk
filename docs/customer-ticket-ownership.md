# Ticket ownership

Every new ticket has separate customer and support owners.

- When the ticket sender is an enabled website user in the ticket's company team, `customer_assignee` starts as that user. A customer or agent may subsequently choose another member of the same company team. An explicit assignee on creation is preserved.
- The migration `backfill_customer_assignee_from_raiser` fills empty customer assignees on existing tickets if the original sender is an enabled team member. It does not overwrite manual choices or change ticket modification timestamps, and it does not send assignment emails.
- Company team members may change the customer assignee through the portal while the ticket is open. Agent Managers and System Managers may do the same on tickets they can read, including closed tickets, both in the customer portal and in the agent details sidebar. The picker offers only members of that ticket's company team. Manual assignment emails the chosen person unless they assigned themselves.
- The support owner remains Frappe's `_assign`/ToDo assignment. Managers can change it from the customer portal as well as from the agent view; ordinary customers do not see that control. On Loopjet's site, the base `Support Rotation` assignment rule is enabled with only `a@loopjet.io` as a user, so every new unresolved ticket initially goes to Ahmad. Frappe's assignment rules apply only when no assignment exists, so a later manual assignment is retained.

If an email sender has no enabled website user in the company team, the customer assignee remains empty until a team member or manager selects one.
