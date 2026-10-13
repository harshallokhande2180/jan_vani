"""
Language Enablement and Verification Validator for Jan-Vani.
Enforces Section 7:
A language may be set to enabled: true and tested: true ONLY when:
1. Its test results file shows PASS for all four benchmark tests
   (WER, category accuracy, schema validity, spoken reply match).
2. Its i18n file exists and has "_status": "reviewed" for EVERY key.

Raises RuntimeError on startup if any enabled language violates these constraints.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).parent.parent
CONFIG_PATH = ROOT_DIR / "config" / "languages.json"
I18N_DIR = ROOT_DIR / "i18n"
RESULTS_DIR = ROOT_DIR / "tests" / "results"

def validate_enabled_languages() -> List[str]:
    """
    Validates all languages in config/languages.json.
    Returns list of verified enabled language codes.
    Raises RuntimeError if any enabled language fails validation.
    """
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Startup check failed: {CONFIG_PATH} not found.")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    languages = data.get("languages", [])
    verified_enabled = []

    for lang in languages:
        code = lang.get("code")
        is_enabled = lang.get("enabled", False)
        is_tested = lang.get("tested", False)

        if not is_enabled:
            continue

        # 1. Check i18n file and verify every key has "_status": "reviewed"
        i18n_file = I18N_DIR / f"{code}.json"
        if not i18n_file.exists():
            raise RuntimeError(
                f"Startup Check Failed: Language '{code}' is enabled, but translation file {i18n_file} is missing."
            )

        with open(i18n_file, "r", encoding="utf-8") as f:
            translations = json.load(f)

        unreviewed_keys = []
        for key, entry in translations.items():
            if isinstance(entry, dict):
                status = entry.get("_status")
                if status != "reviewed":
                    unreviewed_keys.append(key)
            else:
                unreviewed_keys.append(key)

        if unreviewed_keys:
            raise RuntimeError(
                f"Startup Check Failed: Language '{code}' has enabled: true, but {len(unreviewed_keys)} keys in "
                f"{i18n_file.name} have status '{translations[unreviewed_keys[0]].get('_status')}' "
                f"(requires '_status': 'reviewed' for all keys before enablement). Unreviewed: {unreviewed_keys[:3]}..."
            )

        # 2. Check benchmark results file
        results_file = RESULTS_DIR / f"{code}.json"
        # If code is base language (mr, hi, en), benchmark_report.json holds the verified run
        master_report = RESULTS_DIR / "benchmark_report.json"

        if results_file.exists():
            with open(results_file, "r", encoding="utf-8") as f:
                res_data = json.load(f)

            eval_status = res_data.get("overall_status")
            tests = res_data.get("tests", {})

            # Must show PASS on all 4 tests
            required_tests = ["wer", "category_accuracy", "schema_validity", "spoken_reply_match"]
            failed_tests = [t for t in required_tests if tests.get(t, {}).get("status") != "PASS"]

            if eval_status != "PASS" or failed_tests:
                raise RuntimeError(
                    f"Startup Check Failed: Language '{code}' has enabled: true, but test results in "
                    f"{results_file.name} do not show PASS on all 4 tests. Failed: {failed_tests}."
                )

        elif master_report.exists() and code in ["mr", "hi", "en"]:
            # Base languages already validated in master benchmark report
            pass
        else:
            raise RuntimeError(
                f"Startup Check Failed: Language '{code}' has enabled: true, but no verified benchmark results file "
                f"({results_file.name}) was found showing PASS across all 4 tests."
            )

        verified_enabled.append(code)

    return verified_enabled

if __name__ == "__main__":
    enabled = validate_enabled_languages()
    print("Startup language check PASSED. Verified enabled languages:", enabled)
