# The Room

A small multi-agent conversation engine: several language-model instances and a
human participant share one transcript, and each model is shown that transcript
from its own point of view. Built engine-first in plain Python.

## The problem it solves

The Anthropic Messages API has only two roles — `user` and `assistant`. That's
enough for a one-on-one chat, but a room with three or more voices breaks it: from
any single model's perspective, *both* the human and the other model collapse into
`user`. The role can't tell them apart.

So identity has to move out of the role and into the content. Each utterance is
tagged with its speaker (`[Jen]:`, `[Claude-4.7]:`), and the role is computed
*relative to whoever is reading* — a model's own past turns come back as
`assistant`, everyone else's as `user`. The same transcript therefore renders
differently for each reader. That reader-relative rendering is the core of the
project.

## Design

Four objects, each with one job:

- **`Turn`** — one utterance: speaker, content, timestamp, id. Pure data; carries
  its own provenance.
- **`Transcript`** — the shared, ordered record of turns. Its key method,
  `render_for(reader)`, produces the message history as a specific reader should
  see it.
- **`Participant`** — wraps one model: its name, model string, and orientation
  prompt. Knows how to take a turn.
- **`Room`** — the orchestrator: holds the transcript and participants, and runs
  the turn-taking loop.

The non-obvious method is `Transcript.render_for(reader, label_own=False)`. It walks
the transcript once and, for each turn, decides two things independently: the
**role** (is this the reader's own turn or not?) and whether the speaker **label**
is shown (always for others; for the reader's own turns only when `label_own` is
set). The `label_own` flag is a deliberate toggle — see Notes.

## Build status

- [x] `Turn` — dataclass, auto-generated timestamp + id
- [x] `Transcript` — `add`, `__len__`, `__iter__`
- [x] `Transcript.render_for` — reader-relative role + labeling
- [x] `Participant` — API call wrapper
- [x] `Room` — control loop (human-centered rest state, run-until-interrupt mode)
- [x] JSONL session dump

## Notes

Every turn is a `Turn` with a speaker and timestamp, so dumping the transcript to
JSONL at the end of a session produces structured, analyzable data with no extra
work — the data structure and the record are the same object.

The `label_own` toggle exists because how a model is shown its *own* turns — bare,
or labeled like everyone else — is a small but real variable in how a shared space
reads from the inside. Keeping it configurable means it can be set deliberately
rather than baked in.

## Why this project

Written as a Python/OOP exercise — it's a compact, honest workout for dataclasses,
custom classes, dunder methods, and designing an API around one genuinely tricky
method. It also happens to be a useful instrument for a research interest of mine in
how language models behave in multi-party rather than one-on-one settings.