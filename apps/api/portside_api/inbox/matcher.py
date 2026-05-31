"""Best-effort match of an inbound email to an existing voyage.

Two strategies, in order:

1. Subject tag ``[V-<voyage_id>]`` (case-insensitive). Inserted automatically
   on the case-detail share button so a forwarded thread carries the tag.
2. (TODO: sender-domain + recency window). Lands with §2.1 workspaces because
   it needs the workspace bound to the recipient address; left as a stub in
   v0.1 so the route already wires the seam.

No match returns ``None``; the route then creates a new voyage.
"""

from __future__ import annotations

from typing import Optional

from .models import InboundMessage


def match_voyage(message: InboundMessage) -> Optional[str]:
    """Return a ``voyage_id`` to attach the message to, or None if a new
    voyage should be created."""
    if message.voyage_tag:
        return message.voyage_tag
    # Sender-domain + recency: deferred to §2.1 (workspaces). The seam is
    # here so a follow-up adds the lookup without a route change.
    return None
