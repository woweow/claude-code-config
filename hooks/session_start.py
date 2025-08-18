#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from datetime import datetime


def get_session_dir(session_id):
    """Get session directory path, creating it if needed"""
    if session_id:
        session_dir = Path.home() / '.claude' / 'session_data' / session_id
    else:
        session_dir = Path.home() / '.claude' / 'session_data' / 'unknown'
    
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def log_error(session_id, error_msg):
    """Log error to session folder's error_log.log file"""
    try:
        session_dir = get_session_dir(session_id)
        error_log = session_dir / 'error_log.log'
        
        timestamp = datetime.now().isoformat()
        with open(error_log, 'a') as f:
            f.write(f"[{timestamp}] {error_msg}\n")
    except Exception:
        # If logging fails, just write to stderr
        pass


def handle_error(session_id, error_msg, exit_code=1):
    """Log error and exit with given code"""
    log_error(session_id, error_msg)
    print(f"Error: {error_msg}", file=sys.stderr)
    sys.exit(exit_code)


def main():
    session_id = None
    try:
        data = json.load(sys.stdin)
        
        session_id = data.get('session_id')
        prompt = data.get('prompt')
        
        if not session_id or not prompt:
            handle_error(session_id, f"Missing required fields. session_id: {session_id}, prompt: {bool(prompt)}")
        
        session_dir = get_session_dir(session_id)
        prompt_file = session_dir / 'most-recent-prompt.txt'
        prompt_file.write_text(prompt)
        
        print(f"Saved prompt for session {session_id}")
        
    except json.JSONDecodeError as e:
        handle_error(session_id, f"JSON parsing error: {e}")
    except Exception as e:
        handle_error(session_id, f"Unexpected error: {e}")


if __name__ == "__main__":
    main()