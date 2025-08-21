#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for consistent styling"""
    RESET = '\033[0m'
    CYAN = '\033[96m'      # Bright branch name (better for black background)
    GREEN = '\033[92m'     # Clean status
    YELLOW = '\033[93m'    # Modified/ahead behind
    RED = '\033[91m'       # Error states
    PURPLE = '\033[95m'    # Prompt section
    WHITE = '\033[97m'     # Bright "no prompt" text (better for black background)
    GRAY = '\033[90m'      # Separator


def run_git_command(cmd):
    """Run git command and return output, handling errors gracefully"""
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=os.getcwd(),
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return None


def get_git_info():
    """Get git repository information"""
    # Check if we're in a git repo
    if not run_git_command(['git', 'rev-parse', '--git-dir']):
        return None
    
    info = {}
    
    # Get current branch
    branch = run_git_command(['git', 'branch', '--show-current'])
    if not branch:
        # Fallback for detached HEAD
        branch = run_git_command(['git', 'rev-parse', '--short', 'HEAD'])
        if branch:
            branch = f"HEAD@{branch}"
        else:
            branch = "unknown"
    info['branch'] = branch
    
    # Get status (clean/dirty)
    status_output = run_git_command(['git', 'status', '--porcelain'])
    info['is_clean'] = status_output == "" if status_output is not None else True
    
    # Get diff stats (lines added/removed)
    diff_stats = run_git_command(['git', 'diff', '--numstat'])
    if diff_stats:
        added, removed = 0, 0
        for line in diff_stats.split('\n'):
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2 and parts[0] != '-' and parts[1] != '-':
                    try:
                        added += int(parts[0])
                        removed += int(parts[1])
                    except ValueError:
                        pass
        info['lines_added'] = added
        info['lines_removed'] = removed
    else:
        info['lines_added'] = 0
        info['lines_removed'] = 0
    
    # Get ahead/behind info
    upstream = run_git_command(['git', 'rev-parse', '--abbrev-ref', '@{upstream}'])
    if upstream:
        ahead_behind = run_git_command(['git', 'rev-list', '--left-right', '--count', f'{upstream}...HEAD'])
        if ahead_behind:
            try:
                behind, ahead = ahead_behind.split('\t')
                info['ahead'] = int(ahead)
                info['behind'] = int(behind)
            except (ValueError, IndexError):
                info['ahead'] = 0
                info['behind'] = 0
        else:
            info['ahead'] = 0
            info['behind'] = 0
    else:
        info['ahead'] = 0
        info['behind'] = 0
    
    return info


def format_git_section(git_info):
    """Format git information with colors and emoji"""
    if not git_info:
        return f"{Colors.WHITE}🌳 no git{Colors.RESET}"
    
    branch = git_info['branch']
    
    # Status indicator
    if git_info['is_clean']:
        status_color = Colors.GREEN
        status_indicator = "✓"
    else:
        status_color = Colors.YELLOW  
        status_indicator = "●"
    
    # Ahead/behind indicators
    sync_info = ""
    if git_info['ahead'] > 0:
        sync_info += f" ↑{git_info['ahead']}"
    if git_info['behind'] > 0:
        sync_info += f" ↓{git_info['behind']}"
    
    # Diff stats
    diff_info = ""
    if git_info['lines_added'] > 0 or git_info['lines_removed'] > 0:
        diff_parts = []
        if git_info['lines_added'] > 0:
            diff_parts.append(f"+{git_info['lines_added']}")
        if git_info['lines_removed'] > 0:
            diff_parts.append(f"-{git_info['lines_removed']}")
        diff_info = f" ({','.join(diff_parts)})"
    
    # Build git details section
    git_details = f"{status_color}{status_indicator}{sync_info}{diff_info}{Colors.RESET}"
    
    # Only add separator if there are git details to show
    if git_details.strip() != f"{Colors.RESET}":
        separator = f" {Colors.GRAY}|{Colors.RESET} "
        return f"{Colors.CYAN}🌳 {branch}{Colors.RESET}{separator}{git_details}"
    else:
        return f"{Colors.CYAN}🌳 {branch}{Colors.RESET}"


def get_session_prompt(session_id):
    """Get the most recent prompt from session data"""
    try:
        if not session_id:
            return None
            
        session_dir = Path.home() / '.claude' / 'session_data' / session_id
        prompt_file = session_dir / 'most-recent-prompt.txt'
        
        if prompt_file.exists():
            return prompt_file.read_text().strip()
        
        return None
        
    except Exception:
        return None


def format_cwd_section(cwd):
    """Format current working directory with color and truncation"""
    if not cwd:
        return f"{Colors.WHITE}📁 unknown{Colors.RESET}"
    
    # Use the full path
    dir_path = cwd
    
    # If it's too long, truncate it from the beginning
    if len(dir_path) > 50:
        dir_path = "..." + dir_path[-47:]
    
    return f"{Colors.CYAN}📁 {dir_path}{Colors.RESET}"


def format_cost_section(cost_data):
    """Format cost information with money bag emoji"""
    cost = 0.0
    if cost_data:
        cost = cost_data.get('total_cost_usd', 0.0)
    
    # Format cost as currency (always show at least $0.00)
    cost_str = f"${cost:.2f}"
    
    return f"{Colors.YELLOW}💰 {cost_str}{Colors.RESET}"


def format_prompt_section(prompt):
    """Format prompt with truncation and color"""
    if not prompt:
        return f"{Colors.WHITE}💭 no prompt{Colors.RESET}"
    
    # Clean up the prompt (remove excessive whitespace, newlines)
    clean_prompt = ' '.join(prompt.split())
    
    # Truncate if too long
    if len(clean_prompt) > 200:
        clean_prompt = clean_prompt[:197] + "..."
    
    return f"{Colors.PURPLE}💭 {clean_prompt}{Colors.RESET}"


def main():
    """Main status line function"""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())
        session_id = input_data.get('session_id')
        cwd = input_data.get('cwd')
        cost_data = input_data.get('cost')
        
        # Get directory information
        cwd_section = format_cwd_section(cwd)
        
        # Get git information
        git_info = get_git_info()
        git_section = format_git_section(git_info)
        
        # Get cost information (always displayed)
        cost_section = format_cost_section(cost_data)
        
        # Get prompt information  
        prompt = get_session_prompt(session_id)
        prompt_section = format_prompt_section(prompt)
        
        # Combine with separator
        separator = f" {Colors.GRAY}|{Colors.RESET} "
        sections = [cwd_section, git_section, cost_section, prompt_section]
        
        status_line = separator.join(sections)
        
        print(status_line)
        
    except Exception as e:
        # Fallback output in case of unexpected errors
        print(f"{Colors.RED}📁 dir error | 🌳 git error | 💭 prompt error{Colors.RESET}")


if __name__ == "__main__":
    main()