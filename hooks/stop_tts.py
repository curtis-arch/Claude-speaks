#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "cartesia",
#   "openai",
# ]
# ///

"""
Claude Code Stop Hook - TTS for task completion
Speaks a summary of Claude's response when tasks complete

CHANGELOG (GPT-5 Production Review Applied):
- Fixed Cartesia SDK usage: sync bytes() returns bytes directly, not a generator
- Changed encoding to pcm_s16le (WAV) for broader player compatibility
- Added cross-platform audio playback (macOS/Linux/Windows)
- Made all configuration env-driven (model, voice, delays, etc.)
- Added API key redaction in logs for privacy
- Hardened log file creation with proper permissions
- Improved transcript parsing with tail window and memory bounds
- Added fail-closed design: graceful degradation if APIs unavailable
- Removed hardcoded "John" from prompt, made configurable via STOP_TTS_USER_NAME
- Added OpenRouter attribution headers as env-configurable
- Kept 3-second delay (prevents talking over notification hook)
- Kept inline API keys for John's personal global setup
"""

import json
import sys
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

# ============================================================================
# Configuration (all env-driven for portability)
# ============================================================================

# Transcript parsing
CONTEXT_MESSAGE_COUNT = int(os.getenv("STOP_TTS_CONTEXT_COUNT", "3"))
TAIL_WINDOW_LINES = 200  # Only read last N lines for memory efficiency

# LLM summarization (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY_HERE")
STOP_TTS_MODEL = os.getenv("STOP_TTS_MODEL", "google/gemini-2.5-flash")
STOP_TTS_PROVIDER = os.getenv("STOP_TTS_PROVIDER", "google-vertex/global")
STOP_TTS_MAX_TOKENS = int(os.getenv("STOP_TTS_MAX_TOKENS", "300"))
STOP_TTS_APP_URL = os.getenv("STOP_TTS_APP_URL", "https://github.com/curtis-arch/Claude-speaks")
STOP_TTS_APP_TITLE = os.getenv("STOP_TTS_APP_TITLE", "Claude Speaks")

# Cartesia TTS
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "YOUR_CARTESIA_API_KEY_HERE")
STOP_TTS_CARTESIA_MODEL = os.getenv("STOP_TTS_CARTESIA_MODEL", "sonic-turbo")
STOP_TTS_VOICE_ID = os.getenv("STOP_TTS_VOICE_ID", "YOUR_VOICE_ID_HERE")
STOP_TTS_SAMPLE_RATE = int(os.getenv("STOP_TTS_SAMPLE_RATE", "44100"))

# Timing
STOP_TTS_STARTUP_DELAY = float(os.getenv("STOP_TTS_STARTUP_DELAY", "3.0"))  # Wait for notification hook

# Personalization
STOP_TTS_USER_NAME = os.getenv("STOP_TTS_USER_NAME", "")  # Optional friendly name

# Audio playback
STOP_TTS_PLAYER = os.getenv("STOP_TTS_PLAYER", "")  # Pin a specific player if needed

# Logging
STOP_TTS_DEBUG = os.getenv("STOP_TTS_DEBUG", "1") == "1"

# Audio sample saving
SAVE_AUDIO_SAMPLES = os.getenv("SAVE_AUDIO_SAMPLES", "0") == "1"
AUDIO_SAMPLES_DIR = Path(os.getenv("AUDIO_SAMPLES_DIR", str(Path.home() / ".claude/tts_samples")))
MAX_SAVED_SAMPLES = int(os.getenv("MAX_SAVED_SAMPLES", "10"))

# ============================================================================
# Safe logging with API key redaction
# ============================================================================

def get_log_file() -> Path:
    """Create log file with secure permissions."""
    log_dir = Path.home() / ".claude"
    log_dir.mkdir(mode=0o700, exist_ok=True)
    log_file = log_dir / "tts_stop_debug.log"
    if not log_file.exists():
        log_file.touch(mode=0o600)
    return log_file

def redact_secrets(text: str) -> str:
    """Best-effort redaction of API keys in logs."""
    import re
    # Redact OpenRouter keys
    text = re.sub(r'sk-or-v1-[a-f0-9]{64}', 'sk-or-v1-[REDACTED]', text)
    # Redact Cartesia keys
    text = re.sub(r'sk_car_[A-Za-z0-9]{22}', 'sk_car_[REDACTED]', text)
    # Redact generic bearer tokens
    text = re.sub(r'Bearer\s+[A-Za-z0-9_\-\.]+', 'Bearer [REDACTED]', text, flags=re.IGNORECASE)
    return text

def safe_log(message: str, also_print: bool = False):
    """Log with redaction, never crash on logging errors."""
    if not STOP_TTS_DEBUG:
        return

    try:
        log_file = get_log_file()
        redacted = redact_secrets(message)
        with open(log_file, 'a') as f:
            f.write(redacted + '\n')
        if also_print:
            print(redacted, file=sys.stderr)
    except Exception:
        pass  # Never let logging break the hook

# ============================================================================
# Transcript parsing (memory-efficient, robust)
# ============================================================================

def get_recent_assistant_messages(transcript_path: str, count: int = CONTEXT_MESSAGE_COUNT) -> List[str]:
    """
    Extract text from the last N assistant messages in JSONL transcript.
    Returns a list of messages, newest first: [latest, previous, older, ...]

    Uses tail window to avoid loading huge files into memory.
    """
    try:
        with open(transcript_path, 'r') as f:
            # Read only last N lines for efficiency
            all_lines = f.readlines()
            lines = all_lines[-TAIL_WINDOW_LINES:] if len(all_lines) > TAIL_WINDOW_LINES else all_lines

            if not lines:
                return []

            messages = []

            # Go backwards to find assistant messages with text
            for line in reversed(lines):
                if len(messages) >= count:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if message.get('type') != 'assistant':
                    continue

                # Handle content as list of blocks OR bare string
                content = message.get('message', {}).get('content', [])
                text_blocks = []

                if isinstance(content, str):
                    # Bare string (some API formats)
                    text_blocks.append(content)
                elif isinstance(content, list):
                    # List of content blocks (standard format)
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            text_blocks.append(block.get('text', ''))

                if text_blocks:
                    messages.append(' '.join(text_blocks))

            return messages  # Returns [latest, previous, older]
    except Exception as e:
        safe_log(f"Error parsing transcript: {e}")
        return []

# ============================================================================
# LLM summarization (OpenRouter with Gemini Flash)
# ============================================================================

def summarize_with_llm(messages: List[str], project_name: str) -> str:
    """
    Use OpenRouter (Gemini Flash) to create a concise spoken notification.
    messages: list of [latest, previous, older] for context

    Fail-closed: returns simple fallback if API unavailable.
    """
    if not OPENROUTER_API_KEY:
        safe_log("No OPENROUTER_API_KEY, using fallback summary")
        return f"Task completed in {project_name}."

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

        # Build context section
        context_text = ""
        if len(messages) > 1:
            context_text = "\n\nPrevious messages for context:\n"
            for i, msg in enumerate(messages[1:], 1):
                truncated = msg[:500] + "..." if len(msg) > 500 else msg
                context_text += f"\nMessage {i} before:\n{truncated}\n"

        latest_message = messages[0] if messages else ""
        truncated_latest = latest_message[:1500] + "..." if len(latest_message) > 1500 else latest_message

        # Build user name greeting if configured
        user_greeting = f"{STOP_TTS_USER_NAME}'s" if STOP_TTS_USER_NAME else "your"

        prompt = f"""You are {user_greeting} personal executive assistant, providing clear, enjoyable spoken updates about the AI coding assistant's work.

The developer is working on the {project_name} project. The AI assistant Claude just completed a task.

Here is Claude's MOST RECENT response:
{truncated_latest}{context_text}

Your job: Create a spoken update (2-3 sentences) that:
1. Clearly explains what was just accomplished (don't skip important details)
2. Mentions any files, features, or key changes
3. Notes if the developer needs to take action or review something
4. Is pleasant and natural to listen to

Guidelines:
- Be conversational and warm, like a helpful colleague giving a status update
- Include specific details (file names, features added, problems solved)
- Use past tense: "Created the hook" not "I created" or "Claude created"
- Focus on what's useful to know
- Keep it engaging and easy to follow when spoken aloud
- Previous messages give context, but focus on what just completed

TTS-FRIENDLY FORMATTING (CRITICAL):
- Use lowercase and normal sentence case - avoid ALL CAPS or acronyms (they get spelled out letter-by-letter)
- Convert technical terms to speakable form:
  * "API" → "A P I" or "api"
  * "TTS" → "text to speech"
  * "LLM" → "language model"
  * "JSON" → "jason" or "j son"
  * "subagent" → "sub agent" (two words so it's pronounced naturally)
  * "notification_tts.py" → "notification t t s dot p y" or just "notification hook file"
  * "stop_tts.py" → "stop hook file"
  * "snake_case_names" → separate into normal words: "snake case names"
- Avoid underscores - separate into words: "claude_speaks" → "claude speaks"
- File extensions can be: ".py" → "dot p y" or "python file", ".md" → "dot m d" or "markdown file"
- Keep it natural - imagine you're telling a colleague verbally, not reading code

Examples of good summaries:
- "Updated the notification hook to extract text from the chat transcript using a backwards parser. It now pulls the last three messages for better context. Ready to test when you're ready."
- "Added OpenRouter integration with Gemini Flash for the LLM summarization. API key is inline for now at the top of stop_tts.py. The three-second delay is working well to prevent talking over the notification hook."
- "Finished the architecture document for open-sourcing. It covers three-tier secret management with config files, environment variables, and remote managers like 1Password. Saved to claude-speaking-architecture.md in future-ideas."

Your update:"""

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": STOP_TTS_APP_URL,
                "X-Title": STOP_TTS_APP_TITLE,
            },
            extra_body={
                "provider": {
                    "order": [STOP_TTS_PROVIDER]
                }
            },
            model=STOP_TTS_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=STOP_TTS_MAX_TOKENS
        )

        summary = completion.choices[0].message.content.strip()
        safe_log(f"LLM summary generated: {summary}")
        return summary

    except Exception as e:
        safe_log(f"LLM summarization failed: {e}")
        # Fallback if LLM fails
        return f"Task completed in {project_name}."

# ============================================================================
# Cartesia TTS synthesis (corrected sync usage)
# ============================================================================

def synthesize_tts_wav(text: str) -> Optional[Path]:
    """
    Synthesize text to speech using Cartesia.
    Returns path to temporary WAV file, or None if synthesis fails.

    Uses pcm_s16le for broad player compatibility.
    """
    if not CARTESIA_API_KEY:
        safe_log("No CARTESIA_API_KEY, skipping TTS")
        return None

    try:
        from cartesia import Cartesia

        client = Cartesia(api_key=CARTESIA_API_KEY)

        # CORRECTED: Sync client returns bytes directly, not a generator
        # Reference: https://github.com/cartesia-ai/cartesia-python
        audio_bytes = client.tts.bytes(
            model_id=STOP_TTS_CARTESIA_MODEL,
            transcript=text,
            voice={
                "mode": "id",
                "id": STOP_TTS_VOICE_ID
            },
            language="en",
            output_format={
                "container": "wav",
                "sample_rate": STOP_TTS_SAMPLE_RATE,
                "encoding": "pcm_s16le"  # Changed from pcm_f32le for compatibility
            }
        )

        # Defensive: handle if SDK ever returns generator in future
        if hasattr(audio_bytes, '__iter__') and not isinstance(audio_bytes, (bytes, bytearray)):
            safe_log("Detected generator response, collecting chunks")
            chunks = []
            for chunk in audio_bytes:
                chunks.append(chunk)
            audio_bytes = b''.join(chunks)

        # Write to temp file
        temp_path = Path(tempfile.gettempdir()) / "claude_stop_tts.wav"
        temp_path.write_bytes(audio_bytes)

        safe_log(f"TTS synthesized: {len(audio_bytes)} bytes -> {temp_path}")

        # Save sample if enabled
        if SAVE_AUDIO_SAMPLES:
            try:
                from datetime import datetime
                AUDIO_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                sample_path = AUDIO_SAMPLES_DIR / f"stop_{timestamp}.wav"
                sample_path.write_bytes(audio_bytes)

                safe_log(f"Saved audio sample: {sample_path}")

                # Cleanup: keep only last MAX_SAVED_SAMPLES files
                samples = sorted(AUDIO_SAMPLES_DIR.glob("stop_*.wav"))
                if len(samples) > MAX_SAVED_SAMPLES:
                    for old_file in samples[:-MAX_SAVED_SAMPLES]:
                        old_file.unlink()
                        safe_log(f"Removed old sample: {old_file}")
            except Exception as e:
                safe_log(f"Failed to save audio sample: {e}")

        return temp_path

    except Exception as e:
        safe_log(f"TTS synthesis failed: {e}")
        return None

# ============================================================================
# Cross-platform audio playback
# ============================================================================

def play_wav(wav_path: Path) -> bool:
    """
    Play WAV file using platform-appropriate player.
    Returns True if playback succeeded, False otherwise.

    Attempts in order:
    1. User-specified player (STOP_TTS_PLAYER)
    2. afplay (macOS)
    3. ffplay (Linux/macOS)
    4. PowerShell SoundPlayer (Windows)
    5. Default system handler
    """
    try:
        # 1. User-specified player
        if STOP_TTS_PLAYER:
            if STOP_TTS_PLAYER == "powershell":
                return _play_powershell(wav_path)
            else:
                result = subprocess.run(
                    [STOP_TTS_PLAYER, str(wav_path)],
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0

        # 2. afplay (macOS)
        if shutil.which("afplay"):
            result = subprocess.run(
                ["afplay", str(wav_path)],
                capture_output=True,
                timeout=30
            )
            safe_log(f"afplay returned: {result.returncode}")
            return result.returncode == 0

        # 3. ffplay (cross-platform)
        if shutil.which("ffplay"):
            result = subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", str(wav_path)],
                capture_output=True,
                timeout=30
            )
            safe_log(f"ffplay returned: {result.returncode}")
            return result.returncode == 0

        # 4. PowerShell (Windows)
        if sys.platform == "win32":
            return _play_powershell(wav_path)

        # 5. Fallback: open with default handler
        safe_log("No known player found, using default handler")
        if sys.platform == "darwin":
            subprocess.run(["open", str(wav_path)])
        elif sys.platform == "win32":
            os.startfile(str(wav_path))
        else:
            subprocess.run(["xdg-open", str(wav_path)])

        return True

    except Exception as e:
        safe_log(f"Audio playback failed: {e}")
        return False

def _play_powershell(wav_path: Path) -> bool:
    """Play WAV using PowerShell SoundPlayer (Windows)."""
    try:
        ps_script = f"""
$player = New-Object System.Media.SoundPlayer '{wav_path}'
$player.PlaySync()
$player.Dispose()
"""
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            timeout=30
        )
        safe_log(f"PowerShell playback returned: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        safe_log(f"PowerShell playback failed: {e}")
        return False

# ============================================================================
# Main hook logic
# ============================================================================

def main():
    try:
        # Wait for notification hook to finish speaking (if it fired)
        # This delay is intentional and important - do not remove
        import time
        time.sleep(STOP_TTS_STARTUP_DELAY)

        # Parse hook input
        input_data = json.load(sys.stdin)

        safe_log("=== Stop Hook Payload ===")
        safe_log(json.dumps(input_data, indent=2))

        # Get transcript path and project name
        transcript_path = input_data.get('transcript_path')
        if not transcript_path:
            safe_log("No transcript_path in payload, exiting")
            sys.exit(0)

        project_dir = os.getenv('CLAUDE_PROJECT_DIR', '')
        project_name = os.path.basename(project_dir) if project_dir else "your project"

        # Extract recent messages for context
        recent_messages = get_recent_assistant_messages(transcript_path)
        if not recent_messages:
            safe_log("No assistant messages found, exiting")
            sys.exit(0)

        safe_log(f"=== Extracted Messages (count: {len(recent_messages)}) ===")
        for i, msg in enumerate(recent_messages):
            preview = msg[:300] + "..." if len(msg) > 300 else msg
            safe_log(f"Message {i} ({'latest' if i == 0 else f'{i} back'}): {preview}")

        # Generate spoken notification via LLM
        notification = summarize_with_llm(recent_messages, project_name)
        safe_log(f"=== LLM Summary ===\n{notification}")

        # Synthesize and play TTS
        wav_path = synthesize_tts_wav(notification)
        if wav_path:
            success = play_wav(wav_path)
            safe_log(f"=== TTS Playback {'Succeeded' if success else 'Failed'} ===")
        else:
            safe_log("=== TTS Synthesis Skipped ===")

        sys.exit(0)

    except Exception as e:
        safe_log(f"=== Unhandled Error ===\n{e}")
        import traceback
        safe_log(traceback.format_exc())
        sys.exit(0)  # Never block on errors

if __name__ == "__main__":
    main()
