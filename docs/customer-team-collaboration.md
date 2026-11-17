# Customer company teams

## Scope

An `HD Customer` may name another `HD Customer` in `collaboration_team`.
Accounts with the same value form one company team. Only a System Manager may
change this link. The customer records and their tickets stay separate.

All signed-in members of a linked account may read and work on tickets in that
company team, including tickets raised by colleagues in another linked project.
Without a company-team link, the existing rule remains: a regular customer
member sees their own tickets; a customer manager sees all tickets of that
customer. Ticket creation still uses one of the creator's own customer accounts.

## Ticket collaboration

The customer portal shows a `Customer Assignee` on existing tickets. The picker
lists enabled website users linked to contacts in the ticket's company team.
This field is separate from Frappe's `_assign`, which continues to route work to
support agents. Assigning the same person again sends no duplicate email.
Closed or rated tickets cannot be reassigned by customers.

The customer reply editor offers the same users after `@`. The server accepts
only mention nodes for current team members, deduplicates recipients within a
reply, and queues one email per mentioned colleague except the author. An
assignment also queues an email to the new assignee except on self-assignment.
Both messages link to the customer ticket; mention links include the specific
reply. Agent-only internal comments are unchanged.

Priority changes use the existing `Default` ticket-template permission row.
That row must expose `priority` to Everyone and allow edits after creation.

## Project names and filtering

Each `HD Customer` has an optional System-Manager-owned `project_label`.
The customer portal uses that short name as a tag on ticket cards, list rows,
the board drawer, and the ticket detail. Without a label, it uses the customer
record name. The customer ticket list has an `Alle Projekte` selector and one
option for every project account the signed-in user can see. The selector
filters both board and list on the server, including the total count; it does
not change saved views. The server validates each selected project against
the user's own and explicitly linked company-team accounts.

## Loopjet production configuration

After the release is deployed and migrated, set `collaboration_team` on both
`DHW-ERP` and `Deutsche Hochschulwerbung und -vertriebs GmbH` to the latter
record. That creates one company team for the DHW ERP and CloudMensa project
accounts. The current invoice-only contact without an enabled portal user does
not appear in the assignment or mention picker.

Set `project_label` on `DHW-ERP` to `DHW ERP` and on `Deutsche
Hochschulwerbung und -vertriebs GmbH` to `CloudMensa` after the schema
migration. The two customer records and their tickets remain separate.
