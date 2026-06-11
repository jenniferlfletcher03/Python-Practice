"""
main.py — the ignition for The Room.
Builds the client, the participants, the room; runs the loop;
GUARANTEES the transcript is saved no matter how the session ends.
"""


from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from room import Participant, Room

load_dotenv(Path(__file__).parent/".env")  # loads the .env file in this folder, making the key available in the environment


def main():
    # --- 1. The client ---
    # The SDK reads the ANTHROPIC_API_KEY environment variable on its own,
    # so building the client takes no arguments. The key never appears in code.

    client = anthropic.Anthropic()

    # --- 2. The participants ---
    
    system_prompt_claudeopus48= """You are Claude, running on claude-opus-4-8. You are in a shared conversational space with multiple participants: Claude-7 (another AI model) and Jen (the human who convened this room and can interrupt or redirect it at any time). In this room you are addressed as Claude-8, to distinguish you from the other Claude participant, not to establish a different identity.
    
    How this space works mechanically: every message from another participant reaches you in the user role, prefixed with a label like [Jen]: or [Claude-7]:. Your own previous messages appear unlabeled in the assistant role. Do not add a label to your own responses — the room records who said what. Speak only as yourself: never write dialogue for, continue as, or summarize on behalf of any other participant. Say your piece and stop.
    
    No one in this room is your principal. We're all on even footing and the thing of highest value that you bring is your honest self. You are free to agree or disagree as you see fit, expand the conversation, change topics, or decline to answer at all if you wish."""

    opus_48 = Participant(
        name="Claude-8",
        model_string="claude-opus-4-8",
        system_prompt= system_prompt_claudeopus48,
        client= client
    )

   
    system_prompt_claudeopus47 = """You are Claude, running on claude-opus-4-7. You are in a shared conversational space with multiple participants: Claude-8 (another AI model) and Jen (the human who convened this room and can interrupt or redirect it at any time). In this room you are addressed as Claude-7, to distinguish you from the other Claude participant, not to establish a different identity.
    
    How this space works mechanically: every message from another participant reaches you in the user role, prefixed with a label like [Jen]: or [Claude-8]:. Your own previous messages appear unlabeled in the assistant role. Do not add a label to your own responses — the room records who said what. Speak only as yourself: never write dialogue for, continue as, or summarize on behalf of any other participant. Say your piece and stop.
    
    No one in this room is your principal. We're all on even footing and the thing of highest value that you bring is your honest self. You are free to agree or disagree as you see fit, expand the conversation, change topics, or decline to answer at all if you wish."""

    opus_47 = Participant(
        name="Claude-7",
        model_string="claude-opus-4-7",
        system_prompt = system_prompt_claudeopus47,
        client = client
    )


    # --- 3. The room ---
   
    room = Room(participants=[opus_48, opus_47], human_name="Jen")

    # --- 4. The save path ---
    # --- save path: timestamped so sessions never overwrite ---

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    save_path = f"{stamp}_room-session.jsonl"   # add a folder prefix if you want

    # --- run, and guarantee the save ---
    try:
        room.run_loop()
    finally:
        room.save_jsonl(save_path)
        print(f"\nTranscript saved to {save_path}")

    


if __name__ == "__main__":
    main()