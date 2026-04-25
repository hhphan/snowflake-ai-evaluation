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
from langchain_google_genai import ChatGoogleGenerativeAI

# from langchain_anthropic import ChatAnthropic

AGENT_REGISTRY: dict[str, callable] = {
    "openai": lambda: ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"), temperature=0
    ),
    "gemini": lambda: ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"), temperature=0
    ),
    # "claude": lambda: ChatAnthropic(model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6"), temperature=0),
}

DEFAULT_AGENT = "openai"
