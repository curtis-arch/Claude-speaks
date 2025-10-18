# Changelog

All notable changes to Claude Speaks will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-18

### Added
- **Context-Aware Notifications**: Notification hook now parses the transcript JSONL file to extract detailed tool call information
  - Reads tool descriptions (e.g., "Stage hook files", "Check recent TTS logs") and speaks them naturally
  - Falls back gracefully to regex extraction if transcript parsing fails
  - Performance optimized: <10ms parsing time by reading only last 50 lines
- **Enhanced Tool Intelligence**:
  - Context7 calls now announce the specific library being fetched (e.g., "fetching react dev docs from Context7")
  - Bash commands announce the main command being run
  - File operations (Write/Edit/Read) announce the specific filename
- **Audio Sample Saving**: Optional feature to save TTS audio samples to disk
  - New env var: `SAVE_AUDIO_SAMPLES=1` to enable
  - Configurable directory: `AUDIO_SAMPLES_DIR` (default: `~/.claude/tts_samples`)
  - Auto-cleanup: `MAX_SAVED_SAMPLES` (default: 10) keeps only recent samples
  - Separate notification and stop samples with timestamps

### Changed
- Notification messages now prioritize human-readable descriptions over generic tool names
- Message hierarchy: Description field → Library/file names → Main command → Tool name → Generic fallback

### Fixed
- Transcript parsing handles malformed JSONL lines gracefully
- API keys properly sanitized in repository version

## [1.0.0] - 2025-10-17

### Added
- Initial release: Claude Speaks - TTS for Claude Code
- Notification hook: Announces when Claude needs permission to run tools
- Stop hook: Provides intelligent summaries when tasks complete
- Cross-platform audio support (macOS, Linux, Windows)
- Cartesia Sonic API integration for ultra-low latency TTS (40ms)
- OpenRouter + Gemini Flash for intelligent task summaries
- Configurable greeting and personalization
- Debug logging with API key redaction
- Production-grade error handling and graceful degradation

[1.1.0]: https://github.com/curtis-arch/Claude-speaks/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/curtis-arch/Claude-speaks/releases/tag/v1.0.0
