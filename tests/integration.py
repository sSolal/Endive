"""
Takes all the .end files in folder and runs them through the cli.
"""

from main import Cli
from pathlib import Path
import traceback

def run_file(file):
    try:
        cli = Cli(silent=True, debug=True)
        with open(file, 'r') as f:
            for line in f:
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
                        print(f"Test failed: {statement}")
                        print(f"Expected success: {expected_success}, got {success}")
                        print(f"Expected message: {expected_message}, got {message}")
                        return False
                else:
                    cli.process(line.strip())
        return True
    except Exception as e:
        print(f"Test failed: {file}")
        print(f"With error: {e}")
        print(traceback.format_exc())
        return False

def run():
    for file in Path('tests/').glob('*.end'):
        if run_file(file):
            print(f"Test passed: {file}")
        else:
            print(f"Test failed: {file}")
            exit(1)