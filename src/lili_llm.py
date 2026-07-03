"""
lili_llm.py - Model clients and call functions (Qwen + DeepSeek).
Qwen: SCOUT web search + independent Critic. DeepSeek: SPEC (R1) + BUILD (v4-pro).
"""

import os
import time

# DeepSeek client - primary engine for SPEC/BUILD (Gemini fully removed)
_DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
try:
    from openai import OpenAI as _OpenAI
    _deepseek_client = _OpenAI(api_key=_DEEPSEEK_KEY, base_url="https://api.deepseek.com") if _DEEPSEEK_KEY else None
except ImportError:
    _deepseek_client = None

# Qwen client for SCOUT web search (primary; Gemini search is fallback)
_QWEN_KEY = os.environ.get("QWEN_API_KEY", "")
try:
    from openai import OpenAI as _QwenOpenAI
    _qwen_client = _QwenOpenAI(
        api_key=_QWEN_KEY,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    ) if _QWEN_KEY else None
except Exception:
    _qwen_client = None


# ─────────────────────────────────────────────────────────────
# MODEL CALLS (Qwen + DeepSeek)
# ─────────────────────────────────────────────────────────────

def _call_qwen_search(prompt: str) -> tuple[str | None, list[str]]:
    """Call Qwen with web search via DashScope OpenAI-compatible API.

    DashScope web search is enabled via extra_body only - do NOT pass tools=[].
    Returns (response_text, source_urls).
    """
    if not _qwen_client:
        return None, []
    for attempt in range(3):
        try:
            print(f"  ↳ Trying Qwen (qwen-plus) search attempt {attempt + 1}...")
            resp = _qwen_client.chat.completions.create(
                model="qwen-plus",
                messages=[{"role": "user", "content": prompt}],
                extra_body={"enable_search": True},
                max_tokens=4096,
            )
            text = resp.choices[0].message.content if resp.choices else None
            if text:
                print(f"  [OK] Qwen search succeeded ({len(text)} chars).")
                return text, []
            print(f"  [NO] Qwen attempt {attempt + 1} empty response.")
        except Exception as e:
            wait = 15 * (2 ** attempt)
            print(f"  [NO] Qwen attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                print(f"  ⏳ Waiting {wait}s before retry...")
                time.sleep(wait)
    return None, []


def call_gemini(prompt: str) -> tuple[str | None, list[str]]:
    """SCOUT web search via Qwen. Returns (response_text, source_urls)."""
    return _call_qwen_search(prompt)


def call_gemini_simple(prompt: str, deepseek_prompt: str | None = None, use_reasoner: bool = False) -> str | None:
    """Call DeepSeek for SPEC/BUILD tasks.
    use_reasoner=True -> deepseek-reasoner (R1) with automatic fallback to deepseek-v4-pro
    use_reasoner=False -> deepseek-v4-pro
    """
    if not _deepseek_client:
        print("  [NO] No DeepSeek client available.")
        return None
    ds_prompt = deepseek_prompt if deepseek_prompt else prompt
    models_to_try = ["deepseek-reasoner", "deepseek-v4-pro"] if use_reasoner else ["deepseek-v4-pro"]
    for model in models_to_try:
        succeeded = False
        for attempt in range(3):
            try:
                print(f"  ↳ DeepSeek ({model}) attempt {attempt + 1}...")
                resp = _deepseek_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": ds_prompt}],
                    max_tokens=8192,
                )
                text = resp.choices[0].message.content if resp.choices else None
                if text:
                    print(f"  [OK] DeepSeek ({model}) succeeded.")
                    return text
                print(f"  [NO] DeepSeek ({model}) returned empty response.")
                break
            except Exception as e:
                wait = 15 * (2 ** attempt)
                print(f"  [NO] DeepSeek ({model}) attempt {attempt + 1} failed: {type(e).__name__}: {e}")
                if attempt < 2:
                    print(f"  ⏳ Waiting {wait}s before retry...")
                    time.sleep(wait)
        if succeeded:
            break
        if use_reasoner and model == "deepseek-reasoner":
            print(f"  ↳ R1 exhausted, falling back to deepseek-v4-pro...")
    return None


def call_qwen_critic(prompt: str) -> str | None:
    """Independent Critic review via Qwen-Max.
    Using a different model from BUILD (DeepSeek) breaks the self-grading echo chamber.
    """
    if not _qwen_client:
        print("  [NO] No Qwen client for Critic, falling back to DeepSeek.")
        return call_gemini_simple(prompt)
    for attempt in range(3):
        try:
            print(f"  ↳ Qwen Critic (qwen3.7-max) attempt {attempt + 1}...")
            resp = _qwen_client.chat.completions.create(
                model="qwen3.7-max",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
            )
            text = resp.choices[0].message.content if resp.choices else None
            if text:
                print(f"  [OK] Qwen Critic succeeded.")
                return text
            print(f"  [NO] Qwen Critic empty response.")
        except Exception as e:
            wait = 15 * (2 ** attempt)
            print(f"  [NO] Qwen Critic attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(wait)
    return None


