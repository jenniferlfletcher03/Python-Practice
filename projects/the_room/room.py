"""
The Room — a shared conversational space for multiple Claude instances,
with Jen holding the thread.

Built engine-first in plain Python: the pure data-structure objects (Turn,
Transcript) come first, then Participant, which is the first object that
actually reaches out to the API.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import uuid

import anthropic


@dataclass
class Turn:
    """
    One utterance — the atomic provenance unit.

    A Turn is pure data: it holds who spoke, what they said, and when.
    It has no behavior of its own. Everything that *interprets* a Turn
    (like deciding how it should look to a given reader) lives elsewhere,
    in Transcript. That separation is deliberate — the Turn just records
    what happened; the Transcript decides how to present it.

    Fields:
        speaker:   who spoke. e.g. "jen", "claude-4.7", "claude-4.8"
        content:   the text of the utterance
        timestamp: when it was created (defaults to now, in UTC)
        turn_id:   unique id for addressing this turn later (auto-generated)
    """
    speaker: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    turn_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])


class Transcript:
    """
    The room's shared memory: an ordered list of Turns.

    Holds turns in order, lets you add to them, and — via render_for —
    produces the message history as a specific reader should see it.
    """

    def __init__(self):
        # The ordered record of everything said in the room.
        self._turns: list[Turn] = []

    def add(self, turn: Turn) -> None:
        """Append one Turn to the shared record."""
        self._turns.append(turn)

    def __len__(self) -> int:
        """How many turns the room holds. Lets us write len(transcript)."""
        return len(self._turns)

    def __iter__(self):
        """Lets us loop: `for turn in transcript`. Read-only walk in order."""
        return iter(self._turns)

    def render_for(self, reader: str, label_own: bool = False) -> list[dict]:
        """
        Produce the message history as a SPECIFIC reader should see it.

        The same Transcript renders differently depending on who's reading —
        that's the whole point. A reader's own past turns come back as the
        'assistant' role; everyone else's come back as 'user', with a
        [speaker] label in the content so identity survives the lossy role.

        Args:
            reader:    whose POV to render for, e.g. "claude-4.7"
            label_own: the strip-vs-uniform toggle.
                       False (default) = strip-own: reader's own turns are bare.
                       True            = uniform: reader's own turns keep their label too.

        Returns:
            A list of {"role": ..., "content": ...} dicts, one per Turn,
            ready to hand to the API as the messages array.
        """
        messages = []
        for turn in self:

            if turn.speaker == reader:
                role = "assistant"
            else:
                role = "user"

            if turn.speaker == reader and not label_own:
                content = turn.content
            else:
                content = f"[{turn.speaker}]: {turn.content}"

            messages.append({"role": role, "content": content})

        return messages


class Participant:
    """
    Wraps one model in the room.

    A Participant knows three things: its name (the speaker label used in the
    transcript), which model string to call, and its orientation prompt (how
    it's oriented to the room — the contract-definition layer). Its one real
    job is respond(): take the shared transcript, render it from THIS
    participant's point of view, send it to the API, and hand back a new Turn.

    Note on "two instances, one key": each API call is stateless, so two
    Participants pointing at two model strings — sharing a single client and
    API key — already gives you two distinct voices. The distinctness comes
    from the separate histories rendered for each, not from separate keys.
    """

    def __init__(
        self,
        name: str,
        model_string: str,
        system_prompt: str,
        client: anthropic.Anthropic,
        max_tokens: int = 1024,
        label_own: bool = False,
    ):
        self.name = name
        self.model_string = model_string
        self.system_prompt = system_prompt
        self.client = client          # shared across participants — one key
        self.max_tokens = max_tokens
        self.label_own = label_own    # this participant's view preference

    def respond(self, transcript: "Transcript") -> Turn:
        """
        Take a turn: render the transcript from my POV, call the API,
        and return what I said as a new Turn (not yet added to the
        transcript — the Room decides when to add it).
        """
        # The transcript, seen through MY eyes: my own turns as 'assistant',
        # everyone else's as labeled 'user'. This is why render_for takes a
        # reader — the same shared history becomes my personal message list.
        messages = transcript.render_for(self.name, label_own=self.label_own)

        # Call the model. The orientation prompt rides in `system`, separate
        # from the conversation itself.
        response = self.client.messages.create(
            model=self.model_string,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            messages=messages,
        )

        # The response content is a list of blocks; for plain text we want
        # the text from each text block, joined. (Being defensive: only pull
        # blocks that actually have text, so tool/other blocks don't break us.)
        text = "".join(
            block.text for block in response.content
            if getattr(block, "type", None) == "text"
        )

        # Hand back a Turn stamped with MY name, so provenance is preserved.
        return Turn(speaker=self.name, content=text)


class Room:
    """
    The orchestrator: holds the transcript and the participants, and runs
    the turn-taking loop.

    Two modes, with Jen at the center:
      - REST STATE (the warm seat): Jen types, one model responds, control
        returns to Jen. The default.
      - GO MODE: on a signal, the models volley with each other freely until
        Jen breaks in. On-demand, not the default.

    Jen holds the dial. The interrupt out of GO MODE is deliberately strong,
    since free-running is the riskier mode (the bromance failure: two
    same-lineage instances converging because it's comfortable, not because
    it's true).
    """

    def __init__(self, participants: list[Participant], human_name: str = "Jen"):
        self.transcript = Transcript()
        # Map name -> Participant, so we can look one up by who Jen addressed.
        self.participants = {p.name: p for p in participants}
        self.human_name = human_name
        self._next_responder_idx = 0  # for round-robin in REST STATE 

    def human_says(self, text: str) -> Turn:
        """Record something the human said. Returns the Turn (for convenience)."""
        turn = Turn(speaker=self.human_name, content=text)
        self.transcript.add(turn)
        return turn

    def let_respond(self, name: str) -> Turn:
        """
        Have one named participant take a turn: they produce a Turn, we add
        it to the shared transcript, and we return it so the caller can show it.
        """
        participant = self.participants[name]
        turn = participant.respond(self.transcript)
        self.transcript.add(turn)
        return turn

    def run_loop(self):
        """
        The Jen-centered control loop.

        Rest state is the warm seat: Jen types and one model answers. Typing
        the GO signal ('/run') flips into free-running mode, where the models
        volley until Jen interrupts (here, an empty line).
        """
        # The order models speak in during GO MODE.
        model_names = [name for name in self.participants]

        while True:
            user_input = input(f"[{self.human_name}] > ").strip()

            # --- exit the whole room ---
            if user_input in ("/quit", "/exit"):
                break

            # --- GO MODE: models volley until interrupted ---
            elif user_input == "/run":
                print("  (free-running — press Enter on an empty line to break in)")
                while True:
                    for name in model_names:
                        turn = self.let_respond(name)
                        print(f"[{turn.speaker}]: {turn.content}\n")

                    # The strong interrupt: after each full round, Jen can
                    # break in. An empty line returns her to the warm seat.
                    interrupt = input("  (press Enter to continue, or type to break in) > ").strip()
                    if interrupt:
                        # Jen broke in — record it and hand control back to her.
                        self.human_says(interrupt)
                        break

            # --- REST STATE: Round Robin ---
            elif user_input:
                self.human_says(user_input)
                # rotate through participant - turned based
                responder = model_names[self._next_responder_idx]
                self._next_responder_idx = (self._next_responder_idx + 1) % len(model_names)
                turn = self.let_respond(responder)
                print(f"[{turn.speaker}]: {turn.content}\n")

    def save_jsonl(self, path: str) -> None:
        """
        Write the whole transcript to a JSONL file: one JSON object per line,
        one line per Turn. This makes the session analyzable research data —
        the data structure IS the field-journal entry.

        Each line should capture the turn's provenance: at least
        speaker, content, timestamp, and turn_id.
        """
        with open(path, "w") as f:
            for turn in self.transcript:
                record = {
                    "speaker": turn.speaker,
                    "content": turn.content,
                    "timestamp": turn.timestamp.isoformat(),
                    "turn_id": turn.turn_id,
                }

                f.write(json.dumps(record) + "\n")