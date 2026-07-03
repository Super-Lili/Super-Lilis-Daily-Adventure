"""
super_lili_brain.py - Super-Lili's Daily Adventure Engine (entry point).

The engine was split into focused modules (2026-07-03):
  lili_llm.py        - Qwen + DeepSeek clients and call functions
  lili_prompts.py    - context data, rotations, prompt builders
  lili_validators.py - spec/tool validation chain + response parsers
  lili_pipeline.py   - the 5-phase evolve() orchestrator + persistence

This file stays as the stable entry point for GitHub Actions
(python src/super_lili_brain.py) and re-exports the public API.
"""

from lili_llm import (
    call_gemini,
    call_gemini_simple,
    call_qwen_critic,
    _deepseek_client,
    _qwen_client,
)
from lili_prompts import (
    build_prompt,
    build_scout_prompt,
    build_spec_prompt,
    build_code_prompt,
)
from lili_validators import (
    validate_url,
    validate_spec,
    validate_tool,
    parse_scout_response,
    parse_spec_response,
    parse_build_response,
    parse_response,
    extract_format,
    extract_test_input,
)
from lili_pipeline import (
    evolve,
    fetch_tool_requests,
    mark_issue_built,
    save_tool,
    save_diary,
    save_rest_day,
    update_readme,
)

if __name__ == "__main__":
    evolve()
