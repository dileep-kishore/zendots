# Interview: pointed questions before and during the build

Ask only questions whose answers change the deck. First read every source the
user named (agenda, notes, earlier decks, data) and draft an answer to each
question below. Ask about what the sources leave open, which is usually three
to five questions. If the user says to skip the questions, write your
assumptions into `brief.md` and go on.

## How to ask

Use the host's structured question tool when it has one:

- `AskUserQuestion` in Claude Code;
- `request_user_input` in Codex;
- `ask_user` in Gemini CLI.

T3 Code and other hosts show these tools as a form. When no such tool exists,
ask in chat in the same shape.

- Ask one question at a time. Ask the next one after the answer, since an
  answer often changes the next question or settles it.
- Give two to four options. Put the recommended option first, mark it
  "(Recommended)", and give a one-line reason. The form adds a free-text
  "Other" option, so do not add one.
- Make each question stand on its own. The form can hide your earlier
  message, so name what you found in the question itself.
- For choices about how something looks (layout, template, chart form), add a
  preview to each option, such as a small ASCII mockup or the path to a
  rendered sample slide. Showing a choice beats describing it.

## Before the outline

| Question | Why it matters | Typical options |
|---|---|---|
| Who is in the room, and what do they already know? | Depth, jargon, background slides | Domain experts · Leadership or funders · Mixed team · Outside audience |
| What should they do after the talk? | The ending, and how hard the deck argues | Decide something · Approve a plan · Give feedback · Learn |
| How will the deck be used? | Words per slide: a deck sent ahead needs more text than one presented live | Presented live from a shared browser · Projected in a room · Sent to read · Both |
| How long is the slot, and how much of it is discussion? | Slide count, roughly one to two minutes per content slide | Draft from the agenda; confirm |
| What one sentence should they remember? | The talk's spine; every slide serves it | Two or three drafts from the sources |
| What is the hardest question this room will ask? | One slide must answer it | Two or three candidates from the sources |
| What evidence can we show? | Real numbers beat invented ones | Named dataset or project · Demo or screenshots · Illustrative, marked as such |
| Is anything sensitive? | Avoids rework | Unshared results · Claims about partners · Credit and branding · Nothing |
| Which template and how much motion? | Look and pace | Default · KBase · Another organisation's template; builds per click · Minimal motion |

For the template question, render one sample slide in each candidate
template into a scratch folder with `deck.py new` and `deck.py check`. Show
the screenshots as the option previews, or open them for the user.

## After the outline

Show the outline as one line per slide: its title, its purpose and its layout
(diagram, text, bullets, table or comparison). Then ask:

- Which slide is weakest, or could be cut?
- Does the order match how this room thinks about the topic?
- Is any slide missing that the room will expect?

An outline costs little to change, and built slides cost much more.

## After the first render

Ask only about facts you cannot check yourself, and tie each question to a
slide. For example: "Slide 4 shows routine fixes skipping human review. Is
that right for your pipeline?" Settle what the sources can settle without
asking.

## brief.md

Keep the answers in `brief.md` in the deck folder, so a later session knows
them without asking again. Record:

- the audience;
- the goal;
- how the deck will be used;
- the slot length;
- the one sentence to remember;
- the hard question;
- the evidence sources;
- anything sensitive;
- the template;
- each assumption you made without asking.

Update the file when an answer changes. The bundle and PDF leave it out.
