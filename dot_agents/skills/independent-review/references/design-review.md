# Design review

Use this target for a spec or design document before planning or
implementation. There is no code to trace yet, so the finding and verifier
gates below replace the code-centred ones in the shared briefs. The reviewer
choice, verification and triage steps in `SKILL.md` still apply.

## Pin the target

Pin the spec, the intent file beside it (`<spec>-intent.md`: the user's
messages verbatim, each beside the question and options it answers, the
consequential defaults they never discussed, and an amendment log), the `REVIEW.md` files and earlier specs for the areas the spec
touches, and the code those areas live in, read-only. Hash them like any other
target. Give finders and verifiers the spec and the intent file, never the
planning conversation. Without an intent file, run the intent trace against
the spec's own stated goals and mark that lens partial under coverage.

## Reviewers

Default to one fresh Claude finder and one Codex finder, each covering every
lens below, with Claude verifiers. A fresh same-model reviewer and a
cross-model reviewer find partly different errors, so the pair beats two
reviewers from one vendor. For deep review, split the lenses across vendors as
[lenses.md](lenses.md) assigns them.

## Lenses

Fill `{LENS}` with all five for a pair, or one each for deep review.

1. **Intent trace.** Every request in the intent file is met by the spec. An
   exclusion of an explicit request counts only when the intent file shows the
   user approved it; otherwise it is a finding. List each consequential choice
   the spec makes that the intent file does not record, in a separate
   "Undiscussed defaults" section of the report.
2. **Done-check walk.** Each done check could pass with what the spec
   describes, has a command that produces it, and has the inputs it needs
   (a screen, data, a reference value). Name any goal that no done check would
   catch failing.
3. **Zoom-out.** Existing code, a library, or a capability the platform
   already provides would make part of the design unnecessary or wrong.
   Search the code first. When a capability is in doubt, such as whether a
   runtime inherits existing authentication, run a cheap read-only probe in the
   scratch directory and report its output.
4. **Pre-mortem.** Assume the feature failed in its first month of real use
   and list causes the spec does not address. Report only causes with
   evidence; there is no minimum count.
5. **Drift.** In the areas the spec touches, code that already breaks a
   `REVIEW.md` rule or an earlier spec's stated behaviour, which the new design
   would build on.

## What counts as a finding

These replace items 1 and 2 of the review brief's list. A finding names the
spec section and at least one of:

- an intent-file quote the spec contradicts or drops;
- two spec statements that conflict;
- a done check that cannot pass, and what is missing;
- a code `file:line` or probe output showing the design is wrong or redundant;
- an earlier spec or `REVIEW.md` rule the design or the code it builds on breaks.

Severity: P0, the design as specified loses data or opens a security hole;
P1, it would not do what the intent file asks; P2, a realistic case breaks or
a done check cannot pass; P3, real but low impact.

## Verifier gates

Tell the verifier the target is a design review. These replace its
"Introduced or in audit scope" and "Reachable" gates:

- **In scope:** the problem lies in the pinned spec, or in code the spec builds
  on.
- **Reachable:** a realistic use of the feature as specified meets the
  problem. A missing capability is proven by its absence from the spec plus the
  intent quote or done check that needs it; no faulty code line is required.

The other gates apply unchanged, with "the spec" read in place of "the code".

## After triage

When the planning workflow ran the review, apply CONFIRMED fixes to the spec
without waiting and settle each PLAUSIBLE one by fixing it or recording why
not. Log each fix in one line in the intent file's amendment log. Never edit
the user's quoted messages. A correction to a done check, or an exclusion of
an explicit request, keeps the original, the replacement and the evidence, and
goes on the feature summary page together with the undiscussed defaults and
any finding that contradicts the user's words. A standalone review request
reports findings as `SKILL.md` describes and does not edit the spec.
