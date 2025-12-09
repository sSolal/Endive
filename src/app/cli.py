import os
import sys
import re
from pathlib import Path
from typing import Tuple, Optional, Dict
from ..engine import Engine
from ..engine.display import display
from ..core import get_child


def interpolate(obj, result_str: str) -> str:
    """
    Interpolate object references in a result string.

    Supports:
    - [] - Reference the object itself
    - [0.5.2] - Reference nested children using 0-based indices
    """
    def replace_reference(match):
        ref = match.group(1)

        if ref == '':
            return display(obj)

        # Parse dot notation into list of integers
        try:
            indices = tuple(int(idx) for idx in ref.split('.'))
        except ValueError:
            raise ValueError(f"Invalid path syntax: {ref}")

        child = get_child(obj, indices)
        if child is None:
            raise ValueError(f"Invalid path: {ref} in {obj}")
        return display(child)

    pattern = r'\[(\d+(?:\.\d+)*|)\]'
    return re.sub(pattern, replace_reference, result_str)


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    ORANGE = '\033[93m'
    RESET = '\033[0m'


class Cli:
    def __init__(self, debug: bool = False, silent: bool = False) -> None:
        self.engine = Engine()
        self.debug = debug
        self.silent = silent
        self.commands: Dict[str, str] = {
            ":help": "Show help",
            ":exit": "Exit the CLI",
            ":undo": "Undo last operation",
            ":checkpoint <name>": "Create named checkpoint",
            ":rollback <name>": "Rollback to checkpoint"
        }
        if not silent:
            self.show_welcome()

    def show_welcome(self) -> None:
        """Display welcome message and available commands"""
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║    Endive Proof Assistant - CLI Mode              ║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════════════════╝{Colors.RESET}")
    

    def show_help(self) -> None:
        """Display help information"""
        print(f"\n{Colors.BOLD}Endive Proof Assistant Commands:{Colors.RESET}")
        print()
        print(f"{Colors.BOLD}Available Commands:{Colors.RESET}")
        for command, description in self.commands.items():
            print(f"  {Colors.CYAN}{command}{Colors.RESET} - {description}")
        print()

    def handle_command(self, line: str) -> Optional[Tuple[bool, str]]:
        """Handle CLI commands starting with :. Returns None if not a command."""
        if not line.startswith(':'):
            return None

        # Parse command and arguments
        parts = line.split(None, 1)
        command = parts[0]
        arg = parts[1] if len(parts) > 1 else None

        # Handle each command
        if command == ":help":
            help_lines = ["\nEndive Proof Assistant Commands:", "", "Available Commands:"]
            for cmd, desc in self.commands.items():
                help_lines.append(f"  {cmd} - {desc}")
            help_lines.append("")
            return True, "\n".join(help_lines)

        elif command == ":exit":
            return False, "Cannot exit in non-interactive mode"

        elif command == ":undo":
            success, directive = self.engine.undo()
            if success:
                return True, f"{directive} undone"
            else:
                return False, "Nothing to undo"

        elif command == ":checkpoint":
            if not arg:
                return False, "Usage: :checkpoint <name>"
            self.engine.breakpoint(arg)
            return True, f"Checkpoint '{arg}' created"

        elif command == ":rollback":
            if not arg:
                return False, "Usage: :rollback <name>"
            if self.engine.rollback(arg):
                return True, f"Rolled back to '{arg}'"
            else:
                return False, f"Checkpoint '{arg}' not found"

        else:
            return False, f"Unknown command: {command}"

    def process(self, line: str, silent: Optional[bool] = None) -> Optional[Tuple[bool, str]]:
        """Process a single proof directive line"""
        try:
            # Check if this is a command
            cmd_result = self.handle_command(line)
            if cmd_result is not None:
                success, message = cmd_result
                if not self.silent or silent == False:
                    if success:
                        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
                    else:
                        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
                return success, message

            # Otherwise, process as proof directive
            success, result_objects = self.engine.process(line)

            # Extract display strings from result objects
            messages = []
            for obj in result_objects:
                if "result" in obj.data:
                    interpolated = interpolate(obj, obj.data["result"])
                    messages.append(interpolated)
                else:
                    messages.append(display(obj))

            message = "\n".join(messages) if messages else ""

            if not self.silent or silent == False:
                if success:
                    print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
                else:
                    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

            return success, message
        except Exception as e:
            print(f"{Colors.RED}✗ {str(e)}{Colors.RESET}")
            if self.debug:
                import traceback
                traceback.print_exc()

    def run(self) -> None:
        """Main REPL loop"""
        while True:
            try:
                command = input("> ").strip()

                if not command:
                    continue

                # Handle :exit specially (breaks the loop)
                if command == ":exit":
                    print(f"{Colors.CYAN}Goodbye!{Colors.RESET}")
                    break
                else:
                    # All other commands and directives handled by process()
                    self.process(command)

            except KeyboardInterrupt:
                print(f"\n{Colors.CYAN}Use :exit to quit{Colors.RESET}")
            except EOFError:
                print(f"\n{Colors.CYAN}Goodbye!{Colors.RESET}")
                break
            except Exception as e:
                print(f"{Colors.ORANGE}✗ Unexpected error: {str(e)}{Colors.RESET}")
                if self.debug:
                    import traceback
                    traceback.print_exc()
