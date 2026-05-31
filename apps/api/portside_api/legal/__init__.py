"""Legal citation subsystem (notes/architecture_weeks_5_to_8.md §1.6).

A small set of offline-by-default tools that let an LLM cite real maritime
authorities instead of hallucinating them. Used by the analyst (Agent 3) for
dispute argument citations and, later, by the EU ETS / FuelEU compliance
product for regulatory citations. Same tools, same schema, same verification
gate.

Public surface
--------------

- ``CitedAuthority``: the schema field every agent attaches to its output. The
  route layer rejects any item with ``verified_via_tool=False``.
- ``search_case_corpus(query, topic)`` / ``lookup_case(citation)``: BM25 over a
  committed curated JSONL. Offline. Fast. The first stop for any citation.
- ``lookup_imo_convention(name, article)``: local read of committed public-
  domain convention texts (Hague-Visby for now).
- ``eur_lex.search(query, doc_type)``: thin HTTP wrapper over the EUR-Lex
  CELLAR REST API. Behind ``settings.legal_eur_lex_live`` so tests stay
  hermetic.
- ``verify.validate_authorities(authorities, transcript)``: drops any
  ``CitedAuthority`` whose ``citation`` does not appear in the tool-call
  transcript. The slop killer.

The corpus and the convention texts live next to this module so a fresh clone
is fully functional offline. EUR-Lex requires network and stays off by default.
"""

from . import corpus, eur_lex, imo, models, outbound, verify

__all__ = [
    "corpus",
    "eur_lex",
    "imo",
    "models",
    "outbound",
    "verify",
]
