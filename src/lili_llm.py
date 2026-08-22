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

# Signatures that mean "this provider has no money/quota left", not "the model
# had trouble with this prompt". A rest day caused by this is an infrastructure
# outage requiring a human to top up billing - it must never be diarized or
# ledgered as if SCOUT/BUILD made a creative or quality judgment call, or a
# real billing outage silently gets buried as an ordinary "quiet day" (see
# 2026-08-06/07: both Qwen and DeepSeek were out of funds for 2+ days and the
# diary just said "Phase 1 failed", indistinguishable from a normal rest day).
_BILLING_ERROR_SIGNATURES = (
    "arrearage", "overdue payment", "insufficient balance", "insufficient_quota",
    "insufficient quota", "account is in good standing", "exceeded your current quota",
    "billing", "payment required",
)


def is_billing_error(msg: str) -> bool:
    m = (msg or "").lower()
    return any(sig in m for sig in _BILLING_ERROR_SIGNATURES)


_last_qwen_scout_error = ""


def get_last_qwen_scout_error() -> str:
    return _last_qwen_scout_error


def check_provider_health() -> dict:
    """Cheap (~1 token) probe of both providers BEFORE spending a real
    SCOUT->SPEC->BUILD cycle. A billing outage previously cost 2+ full days of
    wasted attempts (2026-08-06/07) because the pipeline only discovered "no
    money" after already burning SCOUT/SPEC/BUILD calls on a doomed run - this
    check is a single minimal call per provider (max_tokens=1) so a bad day
    costs almost nothing to detect instead of a full cycle's worth of tokens.

    Returns {"qwen": (ok, detail), "deepseek": (ok, detail)}. Never raises -
    an unexpected error is treated as "not ok" with the exception as detail,
    so a probe bug can never crash the pipeline, only skip unnecessarily.
    """
    result = {}
    if _qwen_client:
        try:
            _qwen_client.chat.completions.create(
                model="qwen-plus", messages=[{"role": "user", "content": "hi"}], max_tokens=1,
            )
            result["qwen"] = (True, "")
        except Exception as e:
            result["qwen"] = (False, str(e))
    else:
        result["qwen"] = (False, "no client configured")

    if _deepseek_client:
        try:
            _deepseek_client.chat.completions.create(
                model="deepseek-v4-pro", messages=[{"role": "user", "content": "hi"}], max_tokens=1,
            )
            result["deepseek"] = (True, "")
        except Exception as e:
            result["deepseek"] = (False, str(e))
    else:
        result["deepseek"] = (False, "no client configured")

    return result


def call_with_retry(fn, label: str, max_attempts: int = 3, base_wait: int = 15,
                    on_error=None) -> str | None:
    """Shared retry-with-backoff primitive (deepseek-harness calls this a
    'capability seam' - one adapter contract every provider call goes
    through, instead of each call site hand-rolling its own retry loop with
    its own, inevitably-drifting behavior).

    Real incident this closes (2026-08-19/20): Qwen's SCOUT search has always
    retried 3x with backoff on failure - but DeepSeek's SCOUT FALLBACK path
    was a single bare call with no retry at all, so a transient empty
    response (a known, established DeepSeek behavior - see FINDINGS F-003)
    cost a full rest day instead of succeeding on a retry. Every provider
    call in this module should go through this one primitive so a fix to
    retry behavior (or a new provider) doesn't need to be re-derived at each
    call site.

    `fn` is a zero-arg callable that returns text on success, "" or None on
    an empty response (retried, same as a real error), or raises on a hard
    failure (also retried, with backoff). `on_error` is called with the
    exception text on each failed attempt (e.g. to record the last error for
    later billing-outage classification) - optional, since not every call
    site needs to track it.
    """
    for attempt in range(max_attempts):
        try:
            print(f"  ↳ Trying {label} attempt {attempt + 1}...")
            text = fn()
            if text:
                print(f"  [OK] {label} succeeded ({len(text)} chars).")
                return text
            print(f"  [NO] {label} attempt {attempt + 1} empty response.")
        except Exception as e:
            if on_error:
                on_error(str(e))
            wait = base_wait * (2 ** attempt)
            print(f"  [NO] {label} attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                print(f"  ⏳ Waiting {wait}s before retry...")
                time.sleep(wait)
    return None


def _call_qwen_search(prompt: str) -> tuple[str | None, list[str]]:
    """Call Qwen with web search via DashScope OpenAI-compatible API.

    DashScope web search is enabled via extra_body only - do NOT pass tools=[].
    Returns (response_text, source_urls).
    """
    global _last_qwen_scout_error
    if not _qwen_client:
        return None, []

    def _do_call():
        resp = _qwen_client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            extra_body={"enable_search": True},
            max_tokens=4096,
        )
        return resp.choices[0].message.content if resp.choices else None

    def _record_error(err_text):
        global _last_qwen_scout_error
        _last_qwen_scout_error = err_text

    text = call_with_retry(_do_call, "Qwen (qwen-plus) search", on_error=_record_error)
    return text, []


_last_deepseek_scout_error = ""


def get_last_deepseek_scout_error() -> str:
    return _last_deepseek_scout_error


def call_deepseek_scout_fallback(prompt: str) -> str | None:
    """DeepSeek's role as SCOUT's fallback when Qwen is unavailable - now
    goes through the same retry primitive Qwen's own search always has, so a
    transient empty response gets retried instead of immediately giving up
    (see call_with_retry's docstring for the incident this fixes). No web
    search grounding available here (DeepSeek has no equivalent to Qwen's
    enable_search), so SCOUT quality is lower on this path - this only fixes
    "gave up after one empty response," not the grounding gap itself.
    """
    global _last_deepseek_scout_error
    if not _deepseek_client:
        return None

    def _do_call():
        resp = _deepseek_client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return resp.choices[0].message.content if resp.choices else None

    def _record_error(err_text):
        global _last_deepseek_scout_error
        _last_deepseek_scout_error = err_text

    return call_with_retry(_do_call, "DeepSeek SCOUT fallback", on_error=_record_error)


def call_gemini(prompt: str) -> tuple[str | None, list[str]]:
    """SCOUT web search via Qwen. Returns (response_text, source_urls)."""
    return _call_qwen_search(prompt)


def call_gemini_simple(prompt: str, deepseek_prompt: str | None = None, use_reasoner: bool = False) -> str | None:
    """Call the SPEC/BUILD model chain. Never dies from one provider's hiccup.

    Chain: [deepseek-reasoner (SPEC only)] -> deepseek-v4-pro -> qwen3.7-max.
    Empty responses are RETRIED (DeepSeek empties are transient server issues,
    unlike Gemini where empty meant quota exhausted), then fall to next model.
    """
    ds_prompt = deepseek_prompt if deepseek_prompt else prompt

    chain: list[tuple[object, str]] = []
    if _deepseek_client:
        if use_reasoner:
            chain.append((_deepseek_client, "deepseek-reasoner"))
        chain.append((_deepseek_client, "deepseek-v4-pro"))
    if _qwen_client:
        chain.append((_qwen_client, "qwen3.7-max"))
    if not chain:
        print("  [NO] No model client available.")
        return None

    for client, model in chain:
        for attempt in range(3):
            try:
                print(f"  ↳ {model} attempt {attempt + 1}...")
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": ds_prompt}],
                    max_tokens=16384,  # Mode 3 HTML tools are long; 8192 was truncating (finish_reason=length)
                )
                text = resp.choices[0].message.content if resp.choices else None
                if text and text.strip():
                    print(f"  [OK] {model} succeeded.")
                    return text
                try:
                    finish = resp.choices[0].finish_reason if resp.choices else "no choices"
                except Exception:
                    finish = "unknown"
                print(f"  [NO] {model} empty response (finish_reason={finish}).")
            except Exception as e:
                print(f"  [NO] {model} attempt {attempt + 1} failed: {type(e).__name__}: {e}")
            if attempt < 2:
                wait = 10 * (attempt + 1)
                print(f"  ⏳ Waiting {wait}s before retry...")
                time.sleep(wait)
        print(f"  ↳ {model} exhausted, trying next model in chain...")
    print("  [NO] All models in chain exhausted.")
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


