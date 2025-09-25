import os
import sys
import subprocess
import platform
import glob
import threading
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
        # Add Windows-specific aliases
        if self.system == 'windows':
            aliases.update({
                'ls': 'dir',
                'rm': 'del',
                'cp': 'copy',
                'mv': 'move',
                'cat': 'type',
                'pwd': 'cd',
            })
        return aliases
    
    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if self.system == 'windows' else 'clear')
    
    def get_prompt(self) -> str:
        """Generate the command prompt"""
        username = os.getlogin()
        hostname = platform.node()
        current_dir = os.path.basename(self.current_dir)
        
        # Simple prompt without colors for maximum compatibility
        if self.system == 'windows':
            return f"PS {current_dir}> "
        elif self.system == 'darwin':
            return f"{username}@{hostname} {current_dir} % "
        else:
            return f"{username}@{hostname}:{current_dir}$ "
    
    def expand_aliases(self, command: str) -> str:
        """Expand command aliases"""
        parts = command.split()
        if parts and parts[0] in self.aliases:
            return self.aliases[parts[0]] + ' ' + ' '.join(parts[1:])
        return command
    
    def change_directory(self, path: str) -> bool:
        """Change directory"""
        try:
            # Handle special paths
            if path == "~":
                path = str(Path.home())
            elif path == "-":
                # Simple back navigation - go to previous directory
                previous = os.path.dirname(self.current_dir)
                if previous != self.current_dir:
                    path = previous
                else:
                    print("Already at root directory")
                    return True
            
            # Expand home directory
            if path.startswith('~'):
                path = os.path.expanduser(path)
            
            # Handle relative paths
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
    
    def list_directory(self, command: str):
        """Handle directory listing"""
        try:
            if self.system == 'windows':
                os.system(f'dir {command[3:] if command.lower().startswith("dir ") else ""}')
            else:
                os.system(f'ls {command[3:] if command.lower().startswith("ls ") else ""}')
        except Exception as e:
            print(f"Error listing directory: {e}")
    
    def execute_command(self, command: str) -> bool:
        """Execute a command"""
        if not command.strip():
            return True
            
        # Expand aliases first
        command = self.expand_aliases(command)
        cmd_lower = command.lower()
        
        # Handle internal commands
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
            
        elif cmd_lower in ['ls', 'dir']:
            self.list_directory(command)
            return True
            
        elif cmd_lower == 'history':
            print("Command History:")
            for i, cmd in enumerate(self.history[-10:], 1):
                print(f"  {i}: {cmd}")
            return True
            
        elif cmd_lower == 'help':
            self.show_help()
            return True
        
        # Execute external command
        try:
            # Use system shell for maximum compatibility
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
            
            # Read output
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
        """Show help information"""
        help_text = """
        Simple Cross-Platform Terminal
        ------------------------------
        
        Basic Commands:
          cd [directory]  - Change directory (use ~ for home, .. for parent)
          ls / dir       - List directory contents
          pwd            - Show current directory
          clear / cls    - Clear screen
          history        - Show command history
          exit / quit    - Exit terminal
        
        File Operations:
          cat [file]     - Show file content (type on Windows)
          cp [src] [dst] - Copy files (copy on Windows)
          mv [src] [dst] - Move files (move on Windows)
          rm [file]      - Remove files (del on Windows)
          mkdir [dir]    - Create directory
          rmdir [dir]    - Remove directory
        
        System Info:
          python --version  - Python version
          pip list         - Installed packages
          ver / systeminfo - System info (Windows)
          uname -a         - System info (Unix)
        
        Aliases:
          ll  - ls -la / dir with details
          la  - ls -a  / show hidden files
          ..  - cd ..
          ... - cd ../..
        """
        print(help_text)
    
    def run(self):
        """Main terminal loop"""
        print("=" * 50)
        print("Simple Cross-Platform Terminal")
        print(f"Running on: {platform.system()} {platform.release()}")
        print("Type 'help' for available commands")
        print("Type 'exit' or 'quit' to exit")
        print("=" * 50)
        
        while True:
            try:
                prompt = self.get_prompt()
                command = input(prompt).strip()
                
                if command:
                    self.history.append(command)
                    
                    if not self.execute_command(command):
                        break
                        
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit the terminal")
                continue
                
            except EOFError:
                print("\nGoodbye!")
                break
                
            except Exception as e:
                print(f"Error: {e}")
                continue

# Even simpler version if you want minimal code
class MinimalTerminal:
    def __init__(self):
        self.current_dir = os.getcwd()
        self.system = platform.system().lower()
    
    def run(self):
        """Super simple terminal"""
        print("Minimal Terminal - Type commands or 'exit' to quit")
        
        while True:
            try:
                # Simple prompt
                prompt = f"{os.path.basename(self.current_dir)}> "
                command = input(prompt).strip()
                
                if command.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break
                
                elif command.lower() == 'cd':
                    self.current_dir = str(Path.home())
                    os.chdir(self.current_dir)
                
                elif command.lower().startswith('cd '):
                    new_dir = command[3:].strip()
                    if new_dir == "~":
                        new_dir = str(Path.home())
                    try:
                        os.chdir(new_dir)
                        self.current_dir = os.getcwd()
                    except:
                        print(f"Directory not found: {new_dir}")
                
                elif command:
                    # Execute any other command
                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            cwd=self.current_dir,
                            text=True,
                            capture_output=True
                        )
                        if result.stdout:
                            print(result.stdout)
                        if result.stderr:
                            print(result.stderr)
                    except Exception as e:
                        print(f"Error: {e}")
            
            except KeyboardInterrupt:
                print("\nUse 'exit' to quit")
            except EOFError:
                break

def main():
    """Main function"""
    print("Choose terminal mode:")
    print("1. Full featured terminal")
    print("2. Minimal terminal")
    print("3. Auto-detect (recommended)")
    
    choice = input("Enter choice (1/2/3, default 3): ").strip()
    
    if choice == "1":
        terminal = SimpleTerminal()
    elif choice == "2":
        terminal = MinimalTerminal()
    else:
        # Auto-detect: use simple terminal for maximum compatibility
        terminal = SimpleTerminal()
    
    terminal.run()

if __name__ == "__main__":
    main()