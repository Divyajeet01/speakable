"""The browser engine in docs/index.html must match the Python library.

docs/index.html ships a hand-written JavaScript port of `speakable`, so the
web tool and `pip install speakable` can disagree without anyone noticing.
This runs both over every case in the suite and diffs them.

Needs node on PATH; without it the check reports as skipped rather than
failing, so `python tests/test_parity.py` still works on a bare machine.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from speakable import normalize  # noqa: E402
from test_normalize import CASES  # noqa: E402

# Every case the Python suite covers, plus the two acronym options, which are
# the only behaviour the flags change.
PARITY_CASES = (
    [{"text": src, "spell_acronyms": False, "strip_emoji": True}
     for src, _ in CASES]
    + [{"text": "The API is up", "spell_acronyms": True, "strip_emoji": True},
       {"text": "JSON only", "spell_acronyms": True, "strip_emoji": True},
       {"text": "Ready \U0001F680 to go", "spell_acronyms": False,
        "strip_emoji": False}]
)


def _run_js(cases):
    handle, case_file = tempfile.mkstemp(suffix=".json")
    os.close(handle)
    try:
        with open(case_file, "w", encoding="utf-8") as f:
            json.dump(cases, f)
        result = subprocess.run(
            ["node", str(ROOT / "tests" / "parity.js"), case_file],
            capture_output=True, check=True)
        return json.loads(result.stdout.decode("utf-8"))
    finally:
        os.unlink(case_file)


def test_parity():
    if not shutil.which("node"):
        print("node not on PATH - skipping the browser-engine parity check")
        return
    js = _run_js(PARITY_CASES)
    assert len(js) == len(PARITY_CASES), "node returned the wrong case count"

    failures = []
    for case, got_js in zip(PARITY_CASES, js):
        got_py = normalize(case["text"], case["spell_acronyms"],
                           case["strip_emoji"])
        if got_py != got_js:
            failures.append((case["text"], got_py, got_js))
    for src, got_py, got_js in failures:
        print("INPUT:  %r" % src)
        print("PYTHON: %r" % got_py)
        print("JS:     %r" % got_js)
        print()
    assert not failures, "%d/%d cases differ between Python and the page" % (
        len(failures), len(PARITY_CASES))
    print("python and the browser engine agree on all %d cases"
          % len(PARITY_CASES))


if __name__ == "__main__":
    test_parity()
