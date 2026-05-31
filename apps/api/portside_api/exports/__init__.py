"""Export adapters for the claim packet.

Each module renders one binary artifact from a `VoyageState` and returns the
bytes (or a streaming Response in the route layer). Adapters are pure and
synchronous; the route handler runs them in `asyncio.to_thread` so we never
block the event loop on a large workbook render.

- ``excel.render_laytime_workbook(state) -> bytes``
  Three-sheet `.xlsx` (Calculation + Summary + Letter). See
  `notes/architecture_weeks_5_to_8.md` §1.1.

Future:
- ``pdf.render_letter_pdf(state) -> bytes`` (server-side PDF, distinct from the
  client-side `html2pdf.js` path that lives in apps/web). Held until SES email
  send asks for a server-rendered attachment that is not the client snapshot.
"""

from . import excel

__all__ = ["excel"]
