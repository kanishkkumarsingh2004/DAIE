#!/usr/bin/env python3
"""Example demonstrating OpenRouter LLM integration with streaming"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from daie.core.llm_manager import get_llm_manager, LLMType

# Get OpenRouter API key from environment variable
OPEN_ROUTER_KEY = os.getenv("OPEN_ROUTER")

if not OPEN_ROUTER_KEY:
    print("Error: OPEN_ROUTER environment variable not found. Please check your .env file.")
    sys.exit(1)

# Configure OpenRouter LLM
llm_manager = get_llm_manager()
llm_manager.set_llm(
    llm_type=LLMType.OPENROUTER,
    model_name="deepseek/deepseek-r1-0528:free",
    api_key=OPEN_ROUTER_KEY,
    temperature=0.7,
    max_tokens=1000,
)

# Get LLM instance and use it with streaming
print("Getting response from OpenRouter LLM (streaming):")
print("=" * 50)
llm = llm_manager.get_llm()
response = llm.invoke("Explain what artificial intelligence is in simple terms.", stream=True)
print("\n" + "=" * 50)
print(f"\nFull response length: {len(response)} characters")
