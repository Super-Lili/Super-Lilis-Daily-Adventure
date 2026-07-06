"""Spec Anchor Scaffold - validate a Lili tool's source code for runtime behavior.
Requirements: standard library only.
"""

import re
import builtins
from typing import Set, Tuple, Optional, Any

_SAFE_NAMES = (
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
    'callable', 'chr', 'classmethod', 'complex', 'delattr', 'dict', 'dir',
    'divmod', 'enumerate', 'filter', 'float', 'format', 'frozenset',
    'getattr', 'globals', 'hasattr', 'hash', 'hex', 'id', 'int',
    'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 'map',
    'max', 'memoryview', 'min', 'next', 'object', 'oct', 'ord', 'pow',
    'print', 'property', 'range', 'repr', 'reversed', 'round', 'set',
    'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super',
    'tuple', 'type', 'vars', 'zip',
    'Exception', 'ValueError', 'TypeError', 'IndexError', 'KeyError',
    'ImportError', 'AttributeError', 'ArithmeticError', 'ZeroDivisionError',
    'OverflowError', 'FloatingPointError', 'RuntimeError', 'NotImplementedError',
    'MemoryError', 'RecursionError', 'StopIteration', 'SystemExit',
    'True', 'False', 'None'
)
SAFE_BUILTINS = {n: getattr(builtins, n) for n in _SAFE_NAMES if hasattr(builtins, n)}

FILLER_REGEX = re.compile(
    r'\bhardcoded\b|\bsample\b|\blorem\sipsum\b', re.IGNORECASE
)

def tokenize(text: str) -> Set[str]:
    """Lowercase, strip punctuation, return set of words."""
    return set(re.findall(r'\b\w+\b', text.lower()))

def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    if not set1 and not set2:
        return 1.0
    union = set1 | set2
    if not union:
        return 0.0
    return len(set1 & set2) / len(union)

def compile_and_extract(src: str) -> Tuple[bool, Optional[Any], str]:
    try:
        code = compile(src, '<string>', 'exec')
    except Exception as e:
        return False, None, f"Compilation error: {e}"
    namespace: dict = {'__builtins__': SAFE_BUILTINS}
    try:
        exec(code, namespace)
    except Exception as e:
        return False, None, f"Execution error: {e}"
    func = namespace.get('process')
    if not callable(func):
        return False, None, "No callable 'process' function found"
    return True, func, ""

def has_filler(text: str) -> bool:
    return bool(FILLER_REGEX.search(text))

def process(text: str) -> str:
    """Validate a Lili tool's source code for runtime behaviour."""
    if not text.strip():
        return ("PARSER CHECK: FAIL - empty source code\n"
                "STATIC OUTPUT TEST: SKIPPED\n"
                "INPUT DEPENDENCE SCORE: N/A\n"
                "FALLBACK/ERROR HANDLING: SKIPPED\n"
                "FINAL VERDICT: FAIL")

    ok, func, err = compile_and_extract(text)
    if not ok:
        return (f"PARSER CHECK: FAIL\n- {err}\n"
                "STATIC OUTPUT TEST: SKIPPED (compilation failed)\n"
                "INPUT DEPENDENCE SCORE: N/A\n"
                "FALLBACK/ERROR HANDLING: SKIPPED\n"
                "FINAL VERDICT: FAIL")

    test_inputs = [
        "",
        "hello world this is a test",
        "a different test with unique words like aurora and cascade"
    ]
    results = []  # (idx, inp, [out1, out2], [exc1, exc2])
    for idx, inp in enumerate(test_inputs):
        outs = []
        excs = []
        for _ in range(2):
            try:
                o = func(inp)
                outs.append(o)
                excs.append(None)
            except Exception as e:
                outs.append(f"EXCEPTION: {e}")
                excs.append(str(e))
        results.append((idx, inp, outs, excs))

    # non-determinism detection
    non_det = any(
        (e1 is None and e2 is None and o1 != o2)
        for _, _, (o1, o2), (e1, e2) in results
    )

    # static output test
    first_ok = [outs[0] for _, _, outs, excs in results if excs[0] is None]
    if len(first_ok) >= 2 and all(o == first_ok[0] for o in first_ok[1:]):
        static_pass = False
        static_detail = "all successful inputs produced identical output"
    else:
        static_pass = True
        static_detail = "outputs differ across inputs"

    # input dependence score (Jaccard)
    jac_scores = []
    for _, inp, outs, excs in results:
        if excs[0] is None:
            jac_scores.append(jaccard_similarity(tokenize(inp), tokenize(outs[0])))
    if jac_scores:
        avg_jac = sum(jac_scores) / len(jac_scores)
        flag = "HIGH" if avg_jac > 0.3 else "MEDIUM" if avg_jac > 0.1 else "LOW"
    else:
        avg_jac = None

    # fallback / error detection
    any_exc = any(any(e for e in excs) for _, _, _, excs in results)
    filler_found = any(
        has_filler(outs[0]) for _, _, outs, excs in results if excs[0] is None
    )
    fallback_detected = False
    if len(first_ok) >= 2 and all(o == first_ok[0] for o in first_ok[1:]):
        common = first_ok[0]
        if len(common) < 20:
            all_inp_words = set()
            for _, inp, _, _ in results:
                all_inp_words.update(tokenize(inp))
            low_common = common.lower()
            if not any(w in low_common for w in all_inp_words):
                fallback_detected = True

    fallback_pass = not (any_exc or filler_found or fallback_detected)

    # build report with bullet points
    lines = []
    lines.append("PARSER CHECK: PASS")
    lines.append(f"STATIC OUTPUT TEST: {'PASS' if static_pass else 'FAIL'}")
    lines.append(f"- {static_detail}")
    if non_det:
        lines.append("- Non-determinism detected (same input gave different outputs)")

    if avg_jac is not None:
        lines.append(f"INPUT DEPENDENCE SCORE: {avg_jac:.3f} ({flag})")
    else:
        lines.append("INPUT DEPENDENCE SCORE: N/A (no successful calls)")

    lines.append(f"FALLBACK/ERROR HANDLING: {'PASS' if fallback_pass else 'FAIL'}")
    if any_exc:
        lines.append("- Exceptions occurred during process calls")
        for idx, _, outs, excs in results:
            errs = [e for e in excs if e]
            if errs:
                lines.append(f"  Input {idx+1}: {', '.join(errs)}")
    if filler_found:
        lines.append("- Filler phrase detected ('hardcoded', 'sample', etc.)")
    if fallback_detected:
        lines.append("- Fallback string detected (short identical output with no input words)")

    final_pass = static_pass and fallback_pass
    lines.append(f"FINAL VERDICT: {'PASS' if final_pass else 'FAIL'}")

    return "\n".join(lines)


_browser_input = globals().get('USER_INPUT', None)
if _browser_input is not None:
    print(process(_browser_input))
elif __name__ == "__main__":
    def _cli_main():
        print("Spec Anchor Scaffold: run with USER_INPUT environment variable.")
    _cli_main()