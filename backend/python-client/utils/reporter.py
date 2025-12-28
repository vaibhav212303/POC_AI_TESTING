import json
import os
import webbrowser
import platform

def parse_test_results(server_dir):
    """
    Reads the Playwright 'test-results.json' and returns a summary dictionary.
    """
    json_path = os.path.join(server_dir, "test-results.json")
    
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "failures": [],
        "status": "unknown"
    }

    if not os.path.exists(json_path):
        print(f"⚠️ Warning: No JSON report found at {json_path}")
        return summary

    try:
        with open(json_path, "r") as f:
            data = json.load(f)
            
        # Iterate through the nested structure of Playwright reports
        # Root -> Suites -> Specs -> Tests -> Results
        for suite in data.get("suites", []):
            _process_suite(suite, summary)
            
        summary["status"] = "success" if summary["failed"] == 0 and summary["total"] > 0 else "failure"
            
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in test results.")
    except Exception as e:
        print(f"❌ Error parsing results: {e}")

    return summary

def _process_suite(suite, summary):
    """Recursive helper to traverse suites."""
    # Process specs in this suite
    for spec in suite.get("specs", []):
        summary["total"] += 1
        
        # Check the result of the last run of this test
        if spec.get("tests"):
            last_run = spec["tests"][0]["results"][-1]
            status = last_run["status"]
            
            if status == "passed":
                summary["passed"] += 1
            elif status == "skipped":
                summary["skipped"] += 1
            else:
                summary["failed"] += 1
                # Extract clean error message
                error_obj = last_run.get("error", {})
                error_msg = error_obj.get("message", "Unknown Error")
                # Remove ANSI color codes if present
                clean_error = _strip_ansi(error_msg)
                
                summary["failures"].append({
                    "file": spec.get("file"),
                    "title": spec.get("title"),
                    "error": clean_error
                })

    # Recursively process child suites
    for child_suite in suite.get("suites", []):
        _process_suite(child_suite, summary)

def _strip_ansi(text):
    """Removes ANSI escape codes (colors) from Playwright error output."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def open_html_report(server_dir):
    """
    Opens the Playwright HTML report in the default browser.
    """
    report_path = os.path.join(server_dir, "playwright-report", "index.html")
    
    if os.path.exists(report_path):
        print(f"📊 Opening Report: {report_path}")
        # Handle file protocol based on OS
        if platform.system() == 'Windows':
            webbrowser.open(f"file:///{report_path.replace(os.sep, '/')}")
        else:
            webbrowser.open(f"file://{report_path}")
    else:
        print("❌ HTML Report not found. Ensure 'reporter: [['html']]' is in playwright.config.ts")