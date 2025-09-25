import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import List, Dict

class SimpleTerminal:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.system = platform.system().lower()
        self.history: List[str] = []
        self.history_index = -1
        self.aliases: Dict[str, str] = self.load_aliases()

    def load_aliases(self) -> Dict[str, str]:
        """Load command aliases"""
        aliases = {
            'll': 'ls -la',
            'la': 'ls -a',
            'cls': 'clear',
            'md': 'mkdir',
            'rd': 'rmdir',
            '..': 'cd ..',
            '...': 'cd ../..',
            '....': 'cd ../../..',
        }
        # Windows-specific aliases
        if self.system == 'windows':
            aliases.update({
                'ls': 'dir',
                'rm': 'del',
                'cp': 'copy',
                'mv': 'move',
                'cat': 'type',
                'pwd': 'cd',
                'mkdir -p': 'mkdir'  # map -p to Windows mkdir
            })
        return aliases

    def clear_screen(self):
        os.system('cls' if self.system == 'windows' else 'clear')

    def get_prompt(self) -> str:
        username = os.getlogin()
        hostname = platform.node()
        current_dir = os.path.basename(self.current_dir)
        if self.system == 'windows':
            return f"PS {current_dir}> "
        elif self.system == 'darwin':
            return f"{username}@{hostname} {current_dir} % "
        else:
            return f"{username}@{hostname}:{current_dir}$ "

    def expand_aliases(self, command: str) -> str:
        parts = command.split()
        if parts and parts[0] in self.aliases:
            return self.aliases[parts[0]] + ' ' + ' '.join(parts[1:])
        return command

    def change_directory(self, path: str) -> bool:
        try:
            if path == "~":
                path = str(Path.home())
            elif path == "-":
                previous = os.path.dirname(self.current_dir)
                if previous != self.current_dir:
                    path = previous
                else:
                    print("Already at root directory")
                    return True

            if path.startswith('~'):
                path = os.path.expanduser(path)

            if not os.path.isabs(path):
                path = os.path.join(self.current_dir, path)

            path = os.path.normpath(path)

            if os.path.exists(path) and os.path.isdir(path):
                os.chdir(path)
                self.current_dir = os.getcwd()
                return True
            else:
                print(f"Directory not found: {path}")
                return False
        except Exception as e:
            print(f"Error changing directory: {e}")
            return False

    def mkdir(self, path: str):
        try:
            full_path = path.replace('~', str(Path.home()))
            os.makedirs(full_path, exist_ok=True)
            print(f"Directory created: {full_path}")
        except Exception as e:
            print(f"Error creating directory: {e}")

    def execute_command(self, command: str) -> bool:
        if not command.strip():
            return True

        command = self.expand_aliases(command)
        cmd_lower = command.lower()

        # cd commands
        if cmd_lower.startswith('cd '):
            path = command[3:].strip()
            return self.change_directory(path)
        elif cmd_lower == 'cd':
            return self.change_directory(str(Path.home()))
        elif cmd_lower in ['exit', 'quit']:
            print("Goodbye!")
            return False
        elif cmd_lower in ['clear', 'cls']:
            self.clear_screen()
            return True
        elif cmd_lower == 'pwd':
            print(self.current_dir)
            return True
        elif cmd_lower.startswith('mkdir'):
            parts = command.split(maxsplit=1)
            if len(parts) > 1:
                self.mkdir(parts[1])
            else:
                print("mkdir: missing path")
            return True
        elif cmd_lower in ['ls', 'dir']:
            os.system(command)
            return True

        # external commands
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=self.current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout.strip())
            if stderr:
                print(stderr.strip(), file=sys.stderr)
            return True
        except Exception as e:
            print(f"Error executing command: {e}")
            return True

    def show_help(self):
        print("""
Simple Cross-Platform Terminal
------------------------------
Basic Commands:
  cd [directory]   - Change directory
  ls / dir         - List directory contents
  pwd              - Show current directory
  mkdir [dir]      - Create directory
  clear / cls      - Clear screen
  exit / quit      - Exit terminal
Aliases:
  ll  - ls -la / dir with details
  la  - ls -a
  ..  - cd ..
""")

    def run(self):
        print("="*50)
        print("Simple Cross-Platform Terminal")
        print(f"Running on: {platform.system()} {platform.release()}")
        print("Type 'help' for commands, 'exit' to quit")
        print("="*50)

        while True:
            try:
                command = input(self.get_prompt()).strip()
                if command:
                    self.history.append(command)
                    if not self.execute_command(command):
                        break
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue

def main():
    terminal = SimpleTerminal()
    terminal.run()

if __name__ == "__main__":
    main()
