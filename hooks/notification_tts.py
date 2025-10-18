#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "cartesia",
# ]
# ///

"""
Claude Code Notification TTS Hook - Production Grade
Speaks Claude's notification messages using Cartesia Sonic API

CHANGELOG (GPT-5 Code Review - 2025-10-18):
- Added configurable greeting via CLAUDE_TTS_NAME env var (default: "there")
- Added cross-platform audio playback (macOS, Linux, Windows)
- Added gated debug logging via CLAUDE_TTS_DEBUG=1
- Added API key redaction in logs for security
- Added proper temp file handling with auto-cleanup
- Added robust message parsing with regex fallback
- Added SDK resilience for bytes vs iterator returns
- Added platform-specific WAV encoding (16-bit PCM for Windows/Linux)
- Added restrictive log file permissions (0600)
- Added timeout support with configurable default
- Kept John's API key inline for personal global setup
- Kept John's project-aware messaging pattern

ENV VARS:
- CLAUDE_TTS_NAME: Name for greeting (default: "there")
- CLAUDE_TTS_DEBUG: Set to "1" to enable debug logging
- CARTESIA_API_KEY: API key (falls back to inline default)
- CARTESIA_VOICE_ID: Voice ID (default: f786b574-daa5-4673-aa0c-cbe3e8534c02)
- CARTESIA_MODEL_ID: Model ID (default: sonic-2)
- CARTESIA_LANGUAGE: Language code (default: en)
- CLAUDE_TTS_TIMEOUT: Max seconds for playback (default: 30)
"""

import json
import sys
import os
import subprocess
import tempfile
import re
import platform
import stat
from pathlib import Path
from typing import Optional, Iterator, Union

def get_config(key: str, default: str) -> str:
    """Get configuration from environment with fallback."""
    return os.getenv(key, default)

def redact_secret(value: str) -> str:
    """Redact API keys and secrets for safe logging."""
    if not value or len(value) < 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"

def log_debug(message: str, log_file: Path, sensitive_data: Optional[dict] = None):
    """Write debug logs only if CLAUDE_TTS_DEBUG=1 is set."""
    if get_config('CLAUDE_TTS_DEBUG', '0') != '1':
        return

    try:
        # Create log file with restrictive permissions if it doesn't exist
        if not log_file.exists():
            log_file.touch(mode=0o600)
        else:
            # Ensure existing file has restrictive permissions
            os.chmod(log_file, stat.S_IRUSR | stat.S_IWUSR)

        with open(log_file, 'a') as f:
            f.write(message)

            # Redact sensitive data if provided
            if sensitive_data:
                f.write("\n=== Configuration (Redacted) ===\n")
                for key, value in sensitive_data.items():
                    if 'key' in key.lower() or 'secret' in key.lower() or 'token' in key.lower():
                        f.write(f"{key}={redact_secret(value)}\n")
                    else:
                        f.write(f"{key}={value}\n")
                f.write("\n")
    except Exception as e:
        # Never fail hook due to logging issues
        print(f"Warning: Could not write debug log: {e}", file=sys.stderr)

def extract_tool_name(message: str) -> Optional[str]:
    """Extract tool name from notification message using robust regex."""
    # Pattern 1: "Claude needs your permission to use ToolName"
    match = re.search(r'to use\s+([A-Z][a-zA-Z0-9_]+)', message)
    if match:
        return match.group(1)

    # Pattern 2: "ToolName requires permission"
    match = re.search(r'^([A-Z][a-zA-Z0-9_]+)\s+requires', message)
    if match:
        return match.group(1)

    # Pattern 3: Generic tool mention
    match = re.search(r'\b([A-Z][a-zA-Z0-9_]+)\b', message)
    if match:
        return match.group(1)

    return None

def find_audio_player() -> Optional[tuple[str, bool]]:
    """
    Find best available audio player for current platform.
    Returns (command, needs_16bit_pcm) or None if no player found.
    """
    system = platform.system()

    # macOS - afplay (supports float32)
    if system == 'Darwin':
        if subprocess.run(['which', 'afplay'], capture_output=True).returncode == 0:
            return ('afplay', False)

    # Linux - prefer ffplay, then SoX play, then aplay
    elif system == 'Linux':
        if subprocess.run(['which', 'ffplay'], capture_output=True).returncode == 0:
            return ('ffplay', False)
        if subprocess.run(['which', 'play'], capture_output=True).returncode == 0:
            return ('play', False)
        if subprocess.run(['which', 'aplay'], capture_output=True).returncode == 0:
            return ('aplay', True)  # aplay prefers 16-bit PCM

    # Windows - PowerShell
    elif system == 'Windows':
        return ('powershell', True)  # Windows Media Player wants 16-bit PCM

    return None

def play_audio(audio_path: Path, player: str, timeout: int = 30) -> bool:
    """
    Play audio file using specified player.
    Returns True on success, False on failure.
    """
    try:
        if player == 'afplay':
            result = subprocess.run(
                ['afplay', str(audio_path)],
                capture_output=True,
                timeout=timeout
            )
        elif player == 'ffplay':
            result = subprocess.run(
                ['ffplay', '-nodisp', '-autoexit', str(audio_path)],
                capture_output=True,
                timeout=timeout
            )
        elif player == 'play':
            result = subprocess.run(
                ['play', str(audio_path)],
                capture_output=True,
                timeout=timeout
            )
        elif player == 'aplay':
            result = subprocess.run(
                ['aplay', str(audio_path)],
                capture_output=True,
                timeout=timeout
            )
        elif player == 'powershell':
            # PowerShell command to play audio on Windows
            ps_cmd = f'(New-Object Media.SoundPlayer "{audio_path}").PlaySync()'
            result = subprocess.run(
                ['powershell', '-Command', ps_cmd],
                capture_output=True,
                timeout=timeout
            )
        else:
            return False

        if result.returncode != 0:
            print(f"{player} error: {result.stderr.decode()}", file=sys.stderr)
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"Error: Audio playback timeout (>{timeout}s)", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error playing audio: {e}", file=sys.stderr)
        return False

def generate_speech(client, message: str, voice_id: str, model_id: str,
                   language: str, use_16bit: bool) -> bytes:
    """
    Generate speech using Cartesia API with resilient SDK handling.
    Supports both bytes and chunk iterator returns.
    """
    # Configure WAV encoding based on platform requirements
    if use_16bit:
        output_format = {
            "container": "wav",
            "sample_rate": 44100,
            "encoding": "pcm_s16le"  # 16-bit signed PCM for Windows/Linux
        }
    else:
        output_format = {
            "container": "wav",
            "sample_rate": 44100,
            "encoding": "pcm_f32le"  # 32-bit float PCM for macOS
        }

    # Call API
    response = client.tts.bytes(
        model_id=model_id,
        transcript=message,
        voice={
            "mode": "id",
            "id": voice_id
        },
        language=language,
        output_format=output_format
    )

    # Handle both bytes and iterator returns
    if isinstance(response, bytes):
        return response
    elif isinstance(response, Iterator):
        audio_data = b""
        for chunk in response:
            audio_data += chunk
        return audio_data
    else:
        # Assume it's an iterable of some kind
        audio_data = b""
        for chunk in response:
            audio_data += chunk
        return audio_data

def main():
    log_file = Path.home() / ".claude/tts_debug.log"

    try:
        # Parse hook input
        input_data = json.load(sys.stdin)

        # Debug logging: Full payload
        log_debug(
            f"\n=== Notification Hook Payload ===\n{json.dumps(input_data, indent=2)}\n",
            log_file
        )

        # Extract original message
        original_message = input_data.get('message', '')

        # Get configuration
        user_name = get_config('CLAUDE_TTS_NAME', 'there')
        api_key = get_config('CARTESIA_API_KEY', 'YOUR_CARTESIA_API_KEY_HERE')
        voice_id = get_config('CARTESIA_VOICE_ID', 'YOUR_VOICE_ID_HERE')
        model_id = get_config('CARTESIA_MODEL_ID', 'sonic-2')
        language = get_config('CARTESIA_LANGUAGE', 'en')
        timeout = int(get_config('CLAUDE_TTS_TIMEOUT', '30'))

        # Debug logging: Configuration (with redaction)
        log_debug("", log_file, {
            'CLAUDE_TTS_NAME': user_name,
            'CARTESIA_API_KEY': api_key,
            'CARTESIA_VOICE_ID': voice_id,
            'CARTESIA_MODEL_ID': model_id,
            'CARTESIA_LANGUAGE': language,
            'CLAUDE_TTS_TIMEOUT': str(timeout)
        })

        # Check for project context
        project_dir = os.getenv('CLAUDE_PROJECT_DIR', '')
        project_name = os.path.basename(project_dir) if project_dir else None

        # Extract tool name using robust regex
        tool_name = extract_tool_name(original_message)

        # Build message with configurable greeting
        greeting = f"Hey {user_name}" if user_name else "Hey there"

        if tool_name and project_name:
            message = f"{greeting}, running {tool_name} in {project_name}."
        elif tool_name:
            message = f"{greeting}, running {tool_name}."
        elif project_name:
            message = f"{greeting}, Claude needs your attention in {project_name}."
        else:
            message = f"{greeting}, Claude needs your attention."

        # Debug logging: TTS message
        log_debug(
            f"=== TTS Message ===\n{message}\nLength: {len(message)} characters\n\n",
            log_file
        )

        # Find audio player
        player_info = find_audio_player()
        if not player_info:
            print("Warning: No audio player found. Skipping TTS.", file=sys.stderr)
            sys.exit(0)

        player, use_16bit = player_info
        log_debug(f"=== Audio Player ===\n{player} (16-bit: {use_16bit})\n\n", log_file)

        # Import Cartesia (after we know we have what we need)
        from cartesia import Cartesia

        # Initialize Cartesia client
        client = Cartesia(api_key=api_key)

        # Generate speech with resilient SDK handling
        audio_data = generate_speech(
            client=client,
            message=message,
            voice_id=voice_id,
            model_id=model_id,
            language=language,
            use_16bit=use_16bit
        )

        log_debug(f"=== Audio Generated ===\n{len(audio_data)} bytes\n\n", log_file)

        # Use proper temporary file with auto-cleanup
        with tempfile.NamedTemporaryFile(
            suffix='.wav',
            delete=False,
            mode='wb'
        ) as temp_file:
            temp_path = Path(temp_file.name)
            temp_file.write(audio_data)

        try:
            # Play audio
            success = play_audio(temp_path, player, timeout)
            log_debug(f"=== Playback ===\nSuccess: {success}\n\n", log_file)
        finally:
            # Cleanup temp file
            try:
                temp_path.unlink()
            except Exception:
                pass  # Best effort cleanup

        # Cleanup client
        client.close()

        # Exit 0: Allow notification to proceed normally
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on parse errors

    except ImportError as e:
        print(f"Error: Missing dependency: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block if cartesia not installed

    except Exception as e:
        print(f"Error in TTS hook: {e}", file=sys.stderr)
        log_debug(f"=== ERROR ===\n{e}\n\n", log_file)
        sys.exit(0)  # Don't block Claude on TTS errors

if __name__ == "__main__":
    main()
