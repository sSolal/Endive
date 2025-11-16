import os
import sys
from ..engine import Engine


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class Cli:
    def __init__(self, debug=False, silent=False):
        self.engine = Engine()
        self.debug = debug
        self.silent = silent
        if not silent:
            self.show_welcome()
        self.commands = {":help": "Show help",
        ":exit": "Exit the CLI"}

    def show_welcome(self):
        """Display welcome message and available commands"""
        print(f"{Colors.BOLD}{Colors.CYAN}╔═══════════════════════════════════════════════════╗{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}║    Endive Proof Assistant - CLI Mode              ║{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}╚═══════════════════════════════════════════════════╝{Colors.RESET}")
    

    def show_help(self):
        """Display help information"""
        print(f"\n{Colors.BOLD}Endive Proof Assistant Commands:{Colors.RESET}")
        print()
        print(f"{Colors.BOLD}Available Commands:{Colors.RESET}")
        for command, description in self.commands.items():
            print(f"  {Colors.CYAN}{command}{Colors.RESET} - {description}")
        print()

    def process(self, line, silent=None):
        """Process a single proof directive line"""
        try:
            success, message = self.engine.process(line)
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

    def run(self):
        """Main REPL loop"""
        while True:
            try:
                command = input("> ").strip()

                if not command:
                    continue

                # Handle special commands
                if command == ":exit":
                    print(f"{Colors.CYAN}Goodbye!{Colors.RESET}")
                    break
                elif command == ":help":
                    self.show_help()
                elif command.startswith(":"):
                    print(f"{Colors.RED}✗ Unknown command: {command}{Colors.RESET}")
                    print(f"  Type {Colors.CYAN}:help{Colors.RESET} for available commands")
                else:
                    # Process as proof directive
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
