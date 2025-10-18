# Claude Speaks

Give your AI coding assistant a voice! Claude Speaks adds real-time audio notifications to Claude Code using text-to-speech, so you can stay in flow while Claude works.

## What is Claude Speaks?

Claude Speaks consists of two production-grade TTS hooks for Claude Code:

1. **Notification Hook** - Announces when Claude needs your attention or starts using a tool
2. **Stop Hook** - Provides AI-generated summaries of completed tasks

Both hooks use Cartesia's Sonic API for natural-sounding speech and are designed to work together seamlessly without talking over each other.

## Demo

When you run a command in Claude Code:

```
[Audio] "Hey John, running Bash in Droids."
```

When Claude finishes a task:

```
[Audio, 3 seconds later] "Created sanitized versions of both TTS hooks without API keys.
Removed the inline keys and replaced them with environment variable placeholders.
The files are ready for open source distribution in the .claude/hooks directory."
```

## Why Use Claude Speaks?

- **Stay in flow** - Know what Claude is doing without constantly checking the terminal
- **Multitask effectively** - Work on other things while Claude codes
- **Context-aware** - Summaries are generated from the actual work Claude did
- **Natural speech** - Uses Cartesia Sonic for high-quality, human-like voice
- **Smart sequencing** - 3-second delay prevents hooks from talking over each other
- **Cross-platform** - Works on macOS, Linux, and Windows
- **Production-ready** - Robust error handling, secure logging, fail-closed design
- **Fully configurable** - 26+ environment variables for complete customization

## Features

### Notification Hook

- Announces tool usage in real-time
- Extracts project name from current directory
- Robust message parsing with regex fallbacks
- Configurable greeting via environment variable
- Cross-platform audio playback (afplay, ffplay, aplay, PowerShell)
- Platform-specific WAV encoding (16-bit PCM for Windows/Linux, 32-bit float for macOS)
- Non-blocking (doesn't interrupt Claude's workflow)
- Gated debug logging with API key redaction
- Proper temporary file handling with auto-cleanup

### Stop Hook

- Uses LLM (Gemini Flash via OpenRouter) to summarize completed tasks
- Analyzes the last 3 assistant messages for context
- Generates 2-3 sentence spoken updates with TTS-friendly formatting
- Provider routing for optimal API response times
- Increased token limit (300 tokens for detailed summaries)
- Includes specific details (files changed, features added, etc.)
- Notes if user action is required
- Waits 3 seconds after notification hook to prevent overlap
- TTS-optimized prompts (avoids acronyms getting spelled out)
- Memory-efficient transcript parsing (tail window with 200-line buffer)
- Fail-closed design (graceful degradation if APIs unavailable)
- Changed to sonic-turbo model for faster synthesis
- Cross-platform audio playback support

### Technical Features

- Written in Python 3.11+ with PEP 723 inline dependencies
- Runs via `uv run` for automatic dependency management
- Comprehensive debug logging to `~/.claude/tts_debug.log` and `~/.claude/tts_stop_debug.log`
- Robust error handling (never blocks Claude on TTS failures)
- API key redaction in all log output
- Restrictive log file permissions (0600)
- Parses Claude's JSONL transcript format
- Cross-platform compatible (macOS, Linux, Windows)
- All configuration driven by environment variables
- Timeout support with configurable defaults

## What's New - Production Grade Improvements

Based on GPT-5 code review feedback, both hooks have been significantly upgraded:

### Security & Privacy
- API key redaction in all logs
- Restrictive log file permissions (0600)
- Safe logging that never crashes the hook
- Environment-driven configuration (no hardcoded secrets)

### Cross-Platform Support
- macOS: afplay (32-bit float PCM)
- Linux: ffplay, SoX play, aplay (16-bit PCM for broader compatibility)
- Windows: PowerShell SoundPlayer (16-bit PCM)
- Platform-specific WAV encoding for optimal compatibility

### Configurability
- 26+ environment variables for complete control
- Configurable greeting, voice, model, delays, timeouts
- Debug logging can be enabled/disabled
- Provider routing for API optimization
- All Cartesia and OpenRouter settings configurable

### Performance & Reliability
- Memory-efficient transcript parsing (200-line tail window)
- Fail-closed design (graceful fallbacks)
- Robust SDK handling (supports both bytes and iterator returns)
- Proper temp file cleanup
- Timeout protection (default 30s, configurable)

### TTS Quality
- TTS-friendly prompt guidance (avoids acronyms)
- Increased token limit (300 tokens, up from 100)
- sonic-turbo model for faster synthesis
- Natural formatting guidelines in LLM prompt

## Prerequisites

- **Claude Code** - Get it from [claude.ai/code](https://claude.ai/code)
- **Python 3.11 or higher** - Check with `python3 --version`
- **UV package manager** - Install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Cartesia API key** - Sign up at [cartesia.ai](https://cartesia.ai)
- **OpenRouter API key** - For LLM summarization at [openrouter.ai](https://openrouter.ai)

### Platform-Specific Audio Players

The hooks will automatically detect and use the best available audio player:

- **macOS**: Built-in `afplay` (no installation needed)
- **Linux**: `ffplay` (recommended), `play` (SoX), or `aplay`
  ```bash
  # Install ffplay (Ubuntu/Debian)
  sudo apt install ffmpeg

  # Or install SoX
  sudo apt install sox
  ```
- **Windows**: PowerShell SoundPlayer (built-in, no installation needed)

## Installation

### Option A: Global Installation (Recommended)

Global installation means the hooks work in ALL your Claude Code projects.

#### Step 1: Copy Hook Files

```bash
# Create global hooks directory if it doesn't exist
mkdir -p ~/.claude/hooks

# Copy the hook files
cp .claude/hooks/notification_tts.py ~/.claude/hooks/
cp .claude/hooks/stop_tts.py ~/.claude/hooks/

# Make them executable
chmod +x ~/.claude/hooks/notification_tts.py
chmod +x ~/.claude/hooks/stop_tts.py
```

#### Step 2: Set Environment Variables (Recommended)

The cleanest approach is to set your API keys as environment variables. Add these to your shell profile (`~/.zshrc`, `~/.bashrc`, or `~/.profile`):

```bash
# Cartesia API key (required for TTS)
export CARTESIA_API_KEY="sk_car_your_key_here"

# OpenRouter API key (required for Stop hook summaries)
export OPENROUTER_API_KEY="sk-or-v1-your_key_here"

# Optional: Customize your name for greetings
export CLAUDE_TTS_NAME="John"
export STOP_TTS_USER_NAME="John"

# Optional: Enable debug logging
export CLAUDE_TTS_DEBUG=1
export STOP_TTS_DEBUG=1

# Optional: Customize voices (browse at cartesia.ai/voices)
export CARTESIA_VOICE_ID="f786b574-daa5-4673-aa0c-cbe3e8534c02"
export STOP_TTS_VOICE_ID="f786b574-daa5-4673-aa0c-cbe3e8534c02"
```

After editing, reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

**Alternative: Inline API Keys**

If you prefer not to use environment variables, you can edit the Python files directly:

**Notification Hook:** Edit `~/.claude/hooks/notification_tts.py` line 252:
```python
api_key = get_config('CARTESIA_API_KEY', 'sk_car_your_actual_key_here')
```

**Stop Hook:** Edit `~/.claude/hooks/stop_tts.py` lines 47 and 55:
```python
# Line 47
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "sk-or-v1-your_actual_key_here")

# Line 55
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY", "sk_car_your_actual_key_here")
```

**Get Your API Keys:**
- **Cartesia**: Sign up at [cartesia.ai](https://cartesia.ai) and navigate to your dashboard
- **OpenRouter**: Sign up at [openrouter.ai](https://openrouter.ai) and create an API key

#### Step 3: Configure Global Settings

Edit `~/.claude/settings.json` and add the hooks configuration:

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/notification_tts.py",
            "timeout": 60000
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run ~/.claude/hooks/stop_tts.py",
            "timeout": 60000
          }
        ]
      }
    ]
  }
}
```

**Note:** If you already have a `hooks` section, merge this configuration with your existing hooks.

#### Step 4: Test It

Start a new Claude Code session and run a simple command:

```bash
claude
```

Then ask Claude: "Run `ls` for me"

You should hear: "Hey John, running Bash in [your-project-name]."

When Claude finishes, you'll hear a summary of what was done.

### Option B: Project-Level Installation

Project-level installation means hooks only work in specific projects.

#### Step 1: Copy Files to Project

```bash
# From within your project directory
mkdir -p .claude/hooks
cp /path/to/notification_tts.py .claude/hooks/
cp /path/to/stop_tts.py .claude/hooks/
chmod +x .claude/hooks/notification_tts.py
chmod +x .claude/hooks/stop_tts.py
```

#### Step 2: Set API Keys

Follow the same approach as Option A, either via environment variables or by editing the files in `.claude/hooks/` within your project.

#### Step 3: Configure Project Settings

Create or edit `.claude/settings.json` in your project (not global):

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/notification_tts.py",
            "timeout": 60000
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run .claude/hooks/stop_tts.py",
            "timeout": 60000
          }
        ]
      }
    ]
  }
}
```

#### Step 4: Test

Same as Option A - start Claude and ask it to run a command.

## Configuration

### Environment Variables Reference

Both hooks are now fully configurable via environment variables:

#### Notification Hook Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_TTS_NAME` | `"there"` | Your name for greetings ("Hey [name]") |
| `CLAUDE_TTS_DEBUG` | `0` | Set to `1` to enable debug logging |
| `CARTESIA_API_KEY` | *(required)* | Your Cartesia API key |
| `CARTESIA_VOICE_ID` | *(see code)* | Voice ID from cartesia.ai/voices |
| `CARTESIA_MODEL_ID` | `"sonic-2"` | Cartesia model (sonic-2 or sonic-turbo) |
| `CARTESIA_LANGUAGE` | `"en"` | Language code (en, es, fr, etc.) |
| `CLAUDE_TTS_TIMEOUT` | `30` | Max seconds for audio playback |

#### Stop Hook Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STOP_TTS_USER_NAME` | `""` | Your name for personalized summaries |
| `STOP_TTS_DEBUG` | `1` | Set to `0` to disable debug logging |
| `OPENROUTER_API_KEY` | *(required)* | Your OpenRouter API key |
| `CARTESIA_API_KEY` | *(required)* | Your Cartesia API key |
| `STOP_TTS_CONTEXT_COUNT` | `3` | Number of messages to analyze |
| `STOP_TTS_MODEL` | `"google/gemini-2.5-flash"` | OpenRouter model for summaries |
| `STOP_TTS_PROVIDER` | `"google-vertex/global"` | Provider routing |
| `STOP_TTS_MAX_TOKENS` | `300` | Max tokens for LLM summary |
| `STOP_TTS_CARTESIA_MODEL` | `"sonic-turbo"` | Cartesia model for TTS |
| `STOP_TTS_VOICE_ID` | *(see code)* | Voice ID for summaries |
| `STOP_TTS_SAMPLE_RATE` | `44100` | Audio sample rate (Hz) |
| `STOP_TTS_STARTUP_DELAY` | `3.0` | Seconds to wait before speaking |
| `STOP_TTS_PLAYER` | `""` | Pin specific audio player |
| `STOP_TTS_APP_URL` | *(see code)* | OpenRouter attribution URL |
| `STOP_TTS_APP_TITLE` | `"Claude Speaks"` | OpenRouter attribution title |

### Quick Configuration Examples

**Example 1: Change Your Name**
```bash
export CLAUDE_TTS_NAME="Sarah"
export STOP_TTS_USER_NAME="Sarah"
```

**Example 2: Use Different Voice**
```bash
# Browse voices at cartesia.ai/voices
export CARTESIA_VOICE_ID="79a125e8-cd45-4c13-8a67-188112f4dd22"
export STOP_TTS_VOICE_ID="79a125e8-cd45-4c13-8a67-188112f4dd22"
```

**Example 3: Faster TTS (Use sonic-turbo for both)**
```bash
export CARTESIA_MODEL_ID="sonic-turbo"
export STOP_TTS_CARTESIA_MODEL="sonic-turbo"
```

**Example 4: More Context for Summaries**
```bash
export STOP_TTS_CONTEXT_COUNT=5  # Analyze last 5 messages instead of 3
```

**Example 5: Different LLM Model**
```bash
export STOP_TTS_MODEL="anthropic/claude-3.5-sonnet"  # More detailed summaries
```

**Example 6: Adjust Timing**
```bash
export STOP_TTS_STARTUP_DELAY=5.0  # Wait 5 seconds instead of 3
```

**Example 7: Disable Debug Logging**
```bash
export CLAUDE_TTS_DEBUG=0
export STOP_TTS_DEBUG=0
```

### Changing the Voice

Browse available voices at [cartesia.ai/voices](https://cartesia.ai/voices) and set via environment variables:

```bash
export CARTESIA_VOICE_ID="your_voice_id_here"
export STOP_TTS_VOICE_ID="your_voice_id_here"
```

Or edit the Python files directly as shown in the Installation section.

### Adjusting Context Depth

The Stop hook analyzes recent messages for context. Change how many messages it considers:

```bash
export STOP_TTS_CONTEXT_COUNT=5  # Analyze last 5 messages
```

- `1` = Only the latest message (fast, less context)
- `3` = Latest plus 2 previous (recommended balance)
- `5+` = More history (slower, better context for complex tasks)

### Using a Different LLM

The Stop hook defaults to Gemini Flash 2.5 via OpenRouter. Change the model:

```bash
export STOP_TTS_MODEL="anthropic/claude-3.5-sonnet"
```

**Popular alternatives:**
- `"anthropic/claude-3.5-sonnet"` - More detailed, higher quality
- `"openai/gpt-4o-mini"` - Faster, cheaper
- `"google/gemini-2.0-flash"` - Latest Gemini
- See all models at [openrouter.ai/models](https://openrouter.ai/models)

### Adjusting the Delay

The Stop hook waits 3 seconds to avoid overlapping with the Notification hook:

```bash
export STOP_TTS_STARTUP_DELAY=5.0  # Increase to 5 seconds
```

### Cross-Platform Audio Player Configuration

You can pin a specific audio player if needed:

```bash
# macOS
export STOP_TTS_PLAYER="afplay"

# Linux
export STOP_TTS_PLAYER="ffplay"

# Windows
export STOP_TTS_PLAYER="powershell"
```

Leave unset for automatic detection.

## How It Works

### Notification Hook Flow

1. Claude Code fires a `Notification` hook event when tools are used
2. Hook receives JSON payload with notification message
3. Extracts tool name using robust regex patterns
4. Gets project name from `CLAUDE_PROJECT_DIR` environment variable
5. Constructs concise message with configurable greeting
6. Detects platform and selects appropriate audio player
7. Calls Cartesia TTS API with platform-specific WAV encoding
8. Generates audio (either 16-bit PCM or 32-bit float based on platform)
9. Writes to temporary file with auto-cleanup
10. Plays audio via detected player (afplay, ffplay, aplay, or PowerShell)
11. Cleans up temporary file
12. Returns exit code 0 (non-blocking)

**Debug logging (if enabled):** All events logged to `~/.claude/tts_debug.log` with API keys redacted

### Stop Hook Flow

1. Claude Code fires `Stop` hook when assistant finishes responding
2. Hook waits 3 seconds (lets Notification hook finish)
3. Receives path to JSONL transcript file
4. Uses memory-efficient tail window parsing (last 200 lines)
5. Parses last N assistant messages (default: 3) using backwards traversal
6. Sends messages to LLM (Gemini Flash) with TTS-optimized prompt
7. LLM generates 2-3 sentence spoken summary with TTS-friendly formatting
8. Calls Cartesia TTS with sonic-turbo model (faster synthesis)
9. Uses 16-bit PCM WAV encoding for broad compatibility
10. Writes audio to temporary file
11. Plays audio via platform-appropriate player
12. Returns exit code 0 (non-blocking)

**Debug logging (if enabled):** All events logged to `~/.claude/tts_stop_debug.log` with API keys redacted

### Why 3 Seconds?

Testing showed that:
- Notification hook speaks for ~2 seconds average
- Adding 1 second buffer prevents overlap
- Total delay is acceptable for task completion announcements
- Ensures sequential playback for better comprehension
- Configurable via `STOP_TTS_STARTUP_DELAY` if your setup needs more time

### LLM Prompt Design

The Stop hook prompt is carefully designed to:

1. **Provide context** - Sends 3 messages so LLM understands the full task
2. **Focus on recency** - Latest message weighted more heavily
3. **Encourage specificity** - "Include file names, features added"
4. **Use spoken language** - "Be conversational and warm"
5. **Avoid attribution** - "Use past tense, not 'I created' or 'Claude created'"
6. **TTS-friendly formatting** - Explicit guidance to avoid acronyms
7. **Include examples** - Shows desired output format
8. **Increased token budget** - Max 300 tokens (up from 100) for detailed summaries

### TTS-Friendly Formatting

The Stop hook includes explicit prompt guidance to ensure natural-sounding speech:

- **Lowercase and normal case** - Avoids ALL CAPS (gets spelled out)
- **Expand acronyms** - "API" becomes "A P I" or "api"
- **Separate compound words** - "subagent" becomes "sub agent"
- **Natural file references** - "notification_tts.py" becomes "notification hook file"
- **Avoid underscores** - "claude_speaks" becomes "claude speaks"

This prevents TTS from spelling out technical terms letter-by-letter.

## Cross-Platform Support

### Audio Player Detection

The hooks automatically detect and use the best available audio player for your platform:

**Priority Order:**

1. **User-specified player** (via `STOP_TTS_PLAYER` env var)
2. **macOS**: `afplay` (built-in)
   - Uses 32-bit float PCM for optimal quality
3. **Linux**:
   - `ffplay` (from ffmpeg, recommended)
   - `play` (from SoX)
   - `aplay` (ALSA)
   - Uses 16-bit PCM for broader compatibility
4. **Windows**: PowerShell SoundPlayer (built-in)
   - Uses 16-bit PCM

**No Installation Required:**
- macOS: Works out of the box with afplay
- Windows: Works out of the box with PowerShell
- Linux: May need to install ffmpeg or SoX (see Prerequisites)

### Platform-Specific WAV Encoding

The hooks intelligently choose WAV encoding based on the audio player:

- **macOS (afplay)**: 32-bit float PCM (`pcm_f32le`) - higher quality
- **Linux/Windows**: 16-bit signed PCM (`pcm_s16le`) - broader compatibility

This ensures optimal audio quality while maintaining compatibility across all platforms.

## TTS Quality Tips

To get the best audio results:

### For Users

1. **Enable debug logging** to see what's being spoken:
   ```bash
   export CLAUDE_TTS_DEBUG=1
   export STOP_TTS_DEBUG=1
   ```

2. **Choose a good voice** - Browse [cartesia.ai/voices](https://cartesia.ai/voices)
   - Look for voices marked as "conversational" or "professional"
   - Test different voices to find one you like

3. **Adjust context depth** if summaries are too brief or too verbose:
   ```bash
   export STOP_TTS_CONTEXT_COUNT=5  # More context
   ```

### For Developers

The Stop hook prompt includes explicit TTS formatting guidelines:

- Converts acronyms to natural speech: "API" -> "A P I"
- Separates compound words: "subagent" -> "sub agent"
- Avoids underscores: "file_name" -> "file name"
- Uses normal case instead of ALL CAPS
- Prefers natural descriptions over technical jargon

If you find certain terms are being mispronounced, you can modify the prompt in `stop_tts.py` lines 208-249 to add specific formatting rules.

## Production Features

### Security

- **API key redaction** in all log output
- **Restrictive log file permissions** (0600 - owner read/write only)
- **Safe logging** that never crashes the hook on logging errors
- **Environment-driven secrets** (no hardcoded keys in code)

### Reliability

- **Fail-closed design** - Hooks never block Claude, even on errors
- **Graceful degradation** - Falls back to simple messages if APIs fail
- **Timeout protection** - Configurable timeouts prevent hanging
- **Memory-efficient parsing** - Tail window limits memory usage
- **Proper cleanup** - Temporary files are always deleted
- **Exit code 0** - Hooks always return success to avoid blocking

### Observability

- **Comprehensive debug logging** - Full request/response details
- **Redacted sensitive data** - API keys never appear in logs
- **Performance metrics** - Audio size, playback status
- **Error tracking** - Full exception traces in debug logs
- **Configuration logging** - See all active settings

### Error Handling

All errors are handled gracefully:

1. **Import errors** - Skip TTS if dependencies missing
2. **API errors** - Fall back to simple messages
3. **Audio errors** - Log but don't crash
4. **Parsing errors** - Skip malformed input
5. **Logging errors** - Never crash on log write failures

Every error path ensures the hook exits with code 0 so Claude is never blocked.

## Troubleshooting

### No Audio Playing

**Check 1: Verify audio player is working**

```bash
# macOS
afplay /System/Library/Sounds/Ping.aiff

# Linux
ffplay /usr/share/sounds/alsa/Front_Center.wav
# OR
play /usr/share/sounds/alsa/Front_Center.wav

# Windows (PowerShell)
(New-Object Media.SoundPlayer "C:\Windows\Media\notify.wav").PlaySync()
```

If system audio doesn't work, check your OS audio settings.

**Check 2: Verify hooks are executing**

```bash
# Check debug logs
tail -f ~/.claude/tts_debug.log
tail -f ~/.claude/tts_stop_debug.log
```

If logs aren't being written, hooks aren't firing. Verify your `settings.json` configuration.

**Check 3: Verify UV is installed**

```bash
uv --version
```

If not installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`

**Check 4: Test hooks manually**

```bash
# Test notification hook
echo '{"message":"Claude needs your permission to use Bash"}' | \
  CLAUDE_PROJECT_DIR="/tmp/TestProject" \
  CLAUDE_TTS_DEBUG=1 \
  uv run ~/.claude/hooks/notification_tts.py

# Test stop hook (create a test transcript first)
echo '{"type":"assistant","message":{"content":[{"type":"text","text":"I created a new file called test.py with a hello world function."}]}}' > /tmp/test_transcript.jsonl

echo '{"transcript_path":"/tmp/test_transcript.jsonl"}' | \
  CLAUDE_PROJECT_DIR="/tmp/TestProject" \
  STOP_TTS_DEBUG=1 \
  uv run ~/.claude/hooks/stop_tts.py
```

### API Key Errors

**Error: "Warning: CARTESIA_API_KEY not set"**

Your API key wasn't found. Check:

1. Did you set the environment variable? Run: `echo $CARTESIA_API_KEY`
2. Did you reload your shell after editing `~/.zshrc` or `~/.bashrc`?
3. If using inline keys, did you replace the placeholder exactly?
4. Did you use quotes around the key in the Python file?

```python
# Correct:
api_key = get_config('CARTESIA_API_KEY', 'sk_car_abc123...')

# Wrong:
api_key = get_config('CARTESIA_API_KEY', sk_car_abc123...)  # No quotes!
```

**Error: "Invalid API key"**

Your Cartesia or OpenRouter key is incorrect. Verify:

1. Log into [cartesia.ai](https://cartesia.ai) or [openrouter.ai](https://openrouter.ai)
2. Copy the key again (they're long!)
3. Make sure there are no extra spaces or newlines
4. Check that you're using the right key type:
   - Cartesia keys start with `sk_car_`
   - OpenRouter keys start with `sk-or-v1-`

### Hook Not Firing

**Check 1: Verify settings.json syntax**

```bash
# Validate JSON syntax
python3 -c "import json; json.load(open('~/.claude/settings.json'.replace('~', '$HOME')))"
```

If this errors, your JSON is malformed.

**Check 2: Verify hook paths**

Make sure the `command` path in `settings.json` matches where you installed the files:

```bash
ls -la ~/.claude/hooks/notification_tts.py
ls -la ~/.claude/hooks/stop_tts.py
```

**Check 3: Check permissions**

```bash
# Hooks must be executable
chmod +x ~/.claude/hooks/notification_tts.py
chmod +x ~/.claude/hooks/stop_tts.py
```

**Check 4: Check Claude Code hooks log**

```bash
tail -f ~/.claude/hooks.log
```

This shows all hook executions and errors from Claude Code itself.

### Hooks Talking Over Each Other

If you hear overlapping speech:

**Solution 1: Increase delay**

```bash
export STOP_TTS_STARTUP_DELAY=5.0  # Increase from 3 to 5 seconds
```

**Solution 2: Check notification hook timing**

Enable debug logging and check how long the notification takes:

```bash
export CLAUDE_TTS_DEBUG=1
tail -f ~/.claude/tts_debug.log
```

Look for "Playback Success" timestamp - if it's consistently over 2 seconds, increase the delay.

**Solution 3: Disable one hook temporarily**

Comment out one hook in `settings.json` to test:

```json
{
  "hooks": {
    // "Notification": [...],  // Commented out
    "Stop": [
      {
        "matcher": "*",
        "hooks": [...]
      }
    ]
  }
}
```

### Platform-Specific Issues

**Linux: No audio player found**

Install ffmpeg or SoX:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg
# OR
sudo apt install sox

# Fedora/RHEL
sudo dnf install ffmpeg
# OR
sudo dnf install sox
```

**Windows: PowerShell execution policy**

If PowerShell won't play audio, run as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned
```

**macOS: afplay not found**

This is extremely rare (afplay is built-in), but try:
```bash
which afplay
# Should output: /usr/bin/afplay
```

If not found, install ffmpeg via Homebrew:
```bash
brew install ffmpeg
```

### Debug Logging

**Notification Hook Logs:** `~/.claude/tts_debug.log`

Contains:
- Full notification payload
- Environment variables (with redacted API keys)
- Message being spoken
- Audio player selection
- Audio generation size
- Playback success/failure
- All errors with stack traces

**Stop Hook Logs:** `~/.claude/tts_stop_debug.log`

Contains:
- Stop hook payload
- Extracted assistant messages (with previews)
- LLM summary generated
- TTS synthesis status
- Playback success/failure
- All errors with stack traces

**View logs in real-time:**

```bash
# Terminal 1: Start Claude Code
claude

# Terminal 2: Watch notification logs
tail -f ~/.claude/tts_debug.log

# Terminal 3: Watch stop logs
tail -f ~/.claude/tts_stop_debug.log
```

**Clear logs:**

```bash
rm ~/.claude/tts_debug.log ~/.claude/tts_stop_debug.log
```

**Disable debug logging:**

```bash
export CLAUDE_TTS_DEBUG=0
export STOP_TTS_DEBUG=0
```

## API Costs

### Cartesia Pricing

**Notification Hook (sonic-2):**
- **Model:** Sonic 2
- **Rate:** ~$0.001 per 25 seconds of audio
- **Average duration:** ~2 seconds
- **Cost per notification:** ~$0.00008

**Stop Hook (sonic-turbo):**
- **Model:** Sonic Turbo (faster, same quality)
- **Rate:** ~$0.001 per 25 seconds of audio
- **Average duration:** ~5 seconds
- **Cost per summary:** ~$0.0002

**Combined per task:** ~$0.00028

**Monthly estimate:**
- 100 tasks/day = 3000 tasks/month
- 3000 × $0.00028 = **~$0.84/month**

### OpenRouter Pricing (Gemini Flash 2.5)

- **Input:** $0.0375 per 1M tokens
- **Output:** $0.15 per 1M tokens
- **Average Stop hook:** ~1500 input tokens, ~100 output tokens
- **Cost per summary:** ~$0.000071

**Monthly estimate:**
- 100 summaries/day = 3000/month
- 3000 × $0.000071 = **~$0.21/month**

### Total Monthly Cost

**Typical usage (100 tasks/day):** ~$1.05/month

Both services offer free tiers to start:
- **Cartesia:** $10 free credits on signup
- **OpenRouter:** Small free tier, then pay-as-you-go

### Cost Optimization

Want to reduce costs?

1. **Use sonic-turbo for both hooks** (faster, same price):
   ```bash
   export CARTESIA_MODEL_ID="sonic-turbo"
   export STOP_TTS_CARTESIA_MODEL="sonic-turbo"
   ```

2. **Reduce context messages** (fewer tokens to OpenRouter):
   ```bash
   export STOP_TTS_CONTEXT_COUNT=1  # Only latest message
   ```

3. **Use a cheaper LLM** (if quality is acceptable):
   ```bash
   export STOP_TTS_MODEL="openai/gpt-4o-mini"
   ```

4. **Disable notification hook** (keep only summaries):
   Comment out the Notification section in `settings.json`

## Development

### Testing Hooks Manually

**Test Notification Hook:**

```bash
# Simulate Claude notification with debug logging
echo '{"message":"Claude needs your permission to use Bash"}' | \
  CLAUDE_PROJECT_DIR="/Users/you/projects/TestProject" \
  CLAUDE_TTS_NAME="Test" \
  CLAUDE_TTS_DEBUG=1 \
  uv run ~/.claude/hooks/notification_tts.py
```

You should hear: "Hey Test, running Bash in TestProject."

Check `~/.claude/tts_debug.log` for detailed execution trace.

**Test Stop Hook:**

```bash
# Create a test transcript
cat > /tmp/test_transcript.jsonl << 'EOF'
{"type":"assistant","message":{"content":[{"type":"text","text":"I created a new file called test.py with a hello world function. The file is saved in the project root directory."}]}}
EOF

# Test the hook with debug logging
echo '{"transcript_path":"/tmp/test_transcript.jsonl"}' | \
  CLAUDE_PROJECT_DIR="/Users/you/projects/TestProject" \
  STOP_TTS_USER_NAME="Test" \
  STOP_TTS_DEBUG=1 \
  uv run ~/.claude/hooks/stop_tts.py
```

You should hear a summary after 3 seconds.

Check `~/.claude/tts_stop_debug.log` for:
- Message extraction
- LLM summary generation
- TTS synthesis
- Playback result

### Debug Log Locations

All hooks log to home directory:

```bash
# Notification hook logs
~/.claude/tts_debug.log

# Stop hook logs
~/.claude/tts_stop_debug.log

# Claude Code hooks execution log
~/.claude/hooks.log
```

### Environment Variable Testing

Test different configurations without editing files:

```bash
# Test with different voice
CARTESIA_VOICE_ID="79a125e8-cd45-4c13-8a67-188112f4dd22" \
  echo '{"message":"Test"}' | \
  uv run ~/.claude/hooks/notification_tts.py

# Test with different LLM
STOP_TTS_MODEL="anthropic/claude-3.5-sonnet" \
  echo '{"transcript_path":"/tmp/test_transcript.jsonl"}' | \
  uv run ~/.claude/hooks/stop_tts.py
```

### Contributing

This project is part of the **Droids** collection - production-ready Claude Code extensions.

**To contribute:**

1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly with debug logging
4. Add configuration options as environment variables
5. Update this README with new features
6. Ensure cross-platform compatibility
7. Add API key redaction for any new secrets
8. Submit a pull request

**Contribution ideas:**

- Additional audio players (PulseAudio, JACK, etc.)
- Alternative TTS providers (ElevenLabs, OpenAI TTS, Azure)
- Voice profiles (different voices for errors vs. success)
- Volume control via environment variable
- Speed adjustment for TTS
- Interrupt/cancel audio playback
- Web UI for configuration
- Metrics dashboard (tokens used, costs, etc.)
- Integration tests
- Docker support
- Audio caching (avoid re-generating identical messages)
- Emoji filtering in summaries
- Custom LLM prompt templates

### Code Structure

**notification_tts.py:**
- Lines 1-35: PEP 723 dependencies and documentation
- Lines 36-86: Helper functions (config, logging, redaction)
- Lines 87-132: Audio player detection (cross-platform)
- Lines 133-186: Audio playback handlers
- Lines 187-233: Cartesia TTS generation with SDK resilience
- Lines 234-361: Main hook logic with error handling

**stop_tts.py:**
- Lines 1-27: PEP 723 dependencies and changelog
- Lines 38-70: Configuration (all env-driven)
- Lines 72-110: Safe logging with API key redaction
- Lines 112-170: Memory-efficient transcript parser
- Lines 172-280: LLM summarization with TTS-friendly prompts
- Lines 282-336: Cartesia TTS synthesis (corrected sync usage)
- Lines 338-423: Cross-platform audio playback
- Lines 425-483: Main hook logic with fail-closed design

## License

MIT License - See LICENSE file for details

## Credits

Created by **John Curtis** as part of the Droids project.

**Powered by:**
- [Claude Code](https://claude.ai/code) - Anthropic's AI coding assistant
- [Cartesia Sonic](https://cartesia.ai) - Real-time text-to-speech
- [OpenRouter](https://openrouter.ai) - Unified LLM API
- [UV](https://astral.sh/uv) - Fast Python package manager

**Production improvements informed by GPT-5 code review.**

## Support

**Issues?** Open an issue on GitHub with:
- Your OS version and platform (macOS/Linux/Windows)
- Python version (`python3 --version`)
- UV version (`uv --version`)
- Relevant log files (`~/.claude/tts_debug.log`, `~/.claude/tts_stop_debug.log`)
- Steps to reproduce
- Environment variables being used (redact API keys!)

**Questions?** Check existing issues or start a discussion.

**Need help configuring?** See the Environment Variables Reference section above.

---

**Enjoy coding with Claude Speaks!** Now you can stay in flow while your AI assistant works.
