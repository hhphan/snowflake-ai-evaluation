"""
Agent registry — maps agent names to factory functions returning a LangChain chat model.

To add a new agent:
  1. Install the provider package  (e.g. pip install langchain-google-genai)
  2. Add it to requirements.txt
  3. Uncomment or add an entry below
  4. Set AGENT_NAME=<key> in .env  or pass --agent <key> on the CLI
"""
import os
from langchain_openai import ChatOpenAI

AGENT_REGISTRY: dict[str, callable] = {
    "openai": lambda: ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0
    ),
}

DEFAULT_AGENT = "openai"
