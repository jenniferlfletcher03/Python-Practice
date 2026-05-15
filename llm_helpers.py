"""
llm_helpers.py — Reusable helper functions for calling Claude.

A transparent replacement for course-provided helpers.
Built by Jen, May 2026.
"""

from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables from .env file
load_dotenv()

# Create the Anthropic client
# (Automatically reads ANTHROPIC_API_KEY from os.environ)
client = Anthropic()

# Default settings used across helpers
DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_TOKENS = 1024


def print_llm_response(prompt):
    """
    Send a single prompt to Claude and print the response.
    Use this for simple, one-shot queries where you just want to see output.
    """
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print(response.content[0].text)


def get_llm_response(prompt):
    """
    Send a single prompt to Claude and return the response as a string.
    Use this when you need to store, manipulate, or pass along the response.
    """
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.content[0].text


def print_llm_conversation(messages):
    """
    Send a multi-turn conversation to Claude and print the response.
    `messages` should be a list of dicts with 'role' and 'content' keys.
    Use this when you want Claude to have context from earlier exchanges.
    """
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=messages
    )
    print(response.content[0].text)


def print_llm_response_with_system(system_prompt, user_prompt):
    """
    Send a prompt to Claude with a system prompt that sets behavior/role.
    The system prompt shapes how Claude responds throughout (persona, format, constraints).
    """
    response = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    print(response.content[0].text)