# PR prose

Applies to PR titles, descriptions, review replies, and PR comments an agent
writes. The global writing rules still hold; these add what review text needs.

- Lead with the conclusion: fixed, not applicable, or needs a decision.
- Cite the evidence: the commit SHA, `file:line`, check, or command output.
  Separate what you verified from what you judge.
- No thanks, apologies, status narration ("I have now..."), or restating the
  finding back to the reviewer.
- Keep commit SHAs, file references, commands, and results exactly as they
  are. Never turn a rebuttal into agreement or invent a claim.
- Before posting, read the whole text, quotes and attachments included, for
  secrets, tokens, private paths, and personal details; remove them.
- Preview the Markdown once so quotes, lists, and code render as intended.

Apply `humanizer` only when the user asks for it.
