"""Feature-local wire model for GET /workspaces/{id}/inbox-address (W7).

Moved out of ``main.py`` post-review (#15) to match the established
pattern: every other route surface lives in its own module
(``analyst_citations``, ``evidence_checklist``, ``claim_strength``).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


# Closed: the customer's mailbox forwards messages here and we never read
# the original. When OAuth-backed inbound lands (it might not — forwarding
# is the privacy story we actually want), this widens to a Literal union.
InboxFormat = Literal["forward_to"]


class InboxAddressResponse(BaseModel):
    address: str
    format: InboxFormat = "forward_to"
