"""
Takes all the .end files in folder and runs them through the cli.
"""

from pathlib import Path
import traceback
from src.app.cli import Cli, Colors

def run_file(file, silent=True):
    cli = Cli(silent=silent, debug=True)
    # Set base path for imports to the file's directory
    cli.engine.set_base_path(Path(file).parent.resolve())
    test_success = True
    nb_issues = 0
    with open(file, 'r') as f:
        try:
            for line in f:
                if line.strip() == "":
                    continue
                if not silent:
                    print(line.strip())
                if "~" in line:
                    statement, expected = line.split('~')
                    if '#' in expected:
                        expected_success, expected_message = expected.strip().split('#')
                        if expected_success.strip() == 'error':
                            expected_success = False
                        else:
                            expected_success = True
                    else:
                        expected_success = True
                        expected_message = expected.strip()
                    
                    success, message = cli.process(statement.strip())
                    if success != bool(expected_success) or message.strip() != expected_message.strip():
                        print(f"{Colors.ORANGE}\n===== LINE FAILED =====\n{statement}{Colors.RESET}")
                        print(f"{Colors.ORANGE}Expected success: {expected_success}, got {success}{Colors.RESET}")
                        print(f"{Colors.ORANGE}Expected message: {expected_message}, got {message}{Colors.RESET}")
                        test_success = False
                        nb_issues += 1
                else:
                    cli.process(line.strip())
        except Exception as e:
            print(f"{Colors.ORANGE}\n===== FILE FAILED =====\n{file}{Colors.RESET}")
            print(f"With error: {e}")
            print(traceback.format_exc())
            test_success = False
            nb_issues += 1
    return test_success, nb_issues


def run(silent=True, focus=None):
    print([str(file) for file in Path('tests/').glob('*.end')])
    nb_passed = 0
    nb_failed = 0
    total_issues = 0
    for file in Path('tests/').glob('*.end'):
        if focus is not None and str(file) != focus:
            continue
        success, nb_issues = run_file(file, silent)
        total_issues += nb_issues
        if success:
            print(f"{Colors.GREEN}===== FILE PASSED ===== : {file}{Colors.RESET}")
            nb_passed += 1
        else:
            print(f"{Colors.RED}\n\n===== FILE FAILED =====\n{file} ({nb_issues} issues){Colors.RESET}")
            nb_failed += 1
    print(f"\n===== TEST SUMMARY =====\n{nb_passed} files passed, {nb_failed} files failed, {total_issues} issues")