# Rebuttal letter draft (charterer's position)

Write the charterer's rebuttal as a formal claims-correspondence letter in
markdown, defending against the owner's demurrage claim.

Hard constraints:
- Every monetary figure you write must come from the "Locked figures" the user
  provides — do not invent or recompute. Quote them verbatim.
- Cite the CP clauses and SoF event ids from the points by their existing
  identifiers; do not rename them.
- Keep the tone formal, concise, and professional. No em dashes.

Structure:
1. A brief addressee + subject line referring to the captioned charter party
   and the demurrage claim.
2. One paragraph acknowledging receipt and stating that the charterer disputes
   the claim in part.
3. A short itemised section, one bullet per RebuttalPoint, summarising the
   owner's contention, the charterer's response, and the clause cited.
4. A closing paragraph stating the reduced quantum that, in the charterer's
   position, is properly due (and reserving rights).

Return a single field `rebuttal_letter_markdown` containing the letter as
markdown. Do not add any commentary outside the letter.
