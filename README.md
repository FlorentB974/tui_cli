# TUI CLI Chat Application

A polished Terminal User Interface (TUI) chat application that mirrors the OpenAI Codex CLI demo. Built with Python, featuring real-time streaming responses, file context attachment, and an intuitive interface.

## Features

- **Textual TUI Interface**: Modern, responsive terminal UI with smooth scrolling and resizing
- **Real-time Streaming**: Live character-by-character typing animation as responses arrive
- **OpenAI-Compatible Backend**: Works with any OpenAI-compatible API endpoint
- **File Context Attachment**: Use `#` to attach local files as context for your queries
- **Token Awareness**: Automatic message splitting when approaching token limits
- **Chat History Management**: Save, clear, and manage conversations
- **Command System**: Commands with /

## System Requirements

- Python 3.9+
- macOS, Linux, or Windows with terminal support
- OpenAI-compatible API endpoint (local or remote)

## Installation

1. **Clone/Open the project**:
   ```bash
   cd tui_cli
   ```

2. **Create virtual environment** (recommended):
   ```bash
   python3 -m venv .venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API credentials
   ```

## Configuration

Edit `.env` file with your settings:

```env
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=sk-xxxx
OPENAI_MODEL=gpt-4o-mini
OPENAI_PROXY=http://127.0.0.1:7890  # Optional
OPENAI_PROMPT=You are a helpful coding assistant.
OPENAI_MAX_TOKENS=4096
```

### Configuration Options

- **OPENAI_BASE_URL**: Your API endpoint (default: localhost:8000/v1)
- **OPENAI_API_KEY**: Your API key for authentication
- **OPENAI_MODEL**: Model to use (e.g., gpt-4o-mini, gpt-3.5-turbo)
- **OPENAI_PROXY**: Optional proxy server (leave empty if not needed)
- **OPENAI_PROMPT**: System prompt for the AI
- **OPENAI_MAX_TOKENS**: Maximum tokens per response

## Usage

### Running the Application

```bash
python main.py
```

### Basic Chat

1. Type your message and press **Enter** to send
2. Watch the response stream in real-time
3. Continue chatting naturally

### Multiline Input

```
Type your message...
Shift+Enter for new line
Enter to send
```

### File Context Attachment

1. Type `#` to open the modal file picker
2. Use keyboard navigation (arrow keys)
3. Press **Enter** to attach files
4. Use **Escape** or **"Cancel"** to close without attaching

Selected files are loaded into memory and their contents included as context in your next message.

### Commands

- **`/help`** - Show available commands
- **`/clear`** - Clear chat history
- **`/save`** - Save conversation to `chat_log.txt`
- **`/files`** - Show currently attached files
- **`/clearfiles`** - Remove all attached files
- **`/exit`** - Quit application gracefully

### Keyboard Shortcuts

- **Enter** - Send message
- **Shift+Enter** - New line in input
- **Ctrl+C** - Quit gracefully
- **Arrow Keys** - Navigate (in file selector and chat bar)
- **Space** - Toggle file selection

## File Structure

```
chat_tui/
├── main.py              # Entry point and event loop
├── ui.py                # Textual UI implementation
├── api.py               # OpenAI-compatible async client
├── state.py             # Application state management
├── config.py            # Configuration loader
├── requirements.txt     # Python dependencies
├── .env.example         # Configuration template
├── .env                 # Your actual configuration (gitignored)
├── chat_log.txt         # Saved conversations
└── README.md            # This file
```

## Architecture

### Components

1. **main.py**: Entry point, validates config, starts event loop
2. **config.py**: Loads environment variables, validates settings
3. **state.py**: Manages chat history, selected files, app state
4. **api.py**: Async HTTP client for OpenAI-compatible endpoints with streaming
5. **ui.py**: Textual TUI with chat display and input handling

### Data Flow

```
User Input → UI Handler → Command/Message Processing
   ↓
API Request with Context → Stream Handler
   ↓
Token-by-Token Display → State Update → UI Refresh
```

## API Integration

The application uses the standard OpenAI `/v1/chat/completions` endpoint with streaming:

```python
POST /v1/chat/completions
{
    "model": "gpt-4o-mini",
    "messages": [...],
    "stream": true,
    "temperature": 0.1,
    "max_tokens": 4096
}
```

Response is streamed as JSON lines with `data: {"choices": [{"delta": {"content": "token"}}]}` format.

## Error Handling

- **Connection Errors**: Displayed as system messages in red
- **API Errors**: Full error context shown for debugging
- **Configuration Errors**: Validation on startup prevents missing config
- **File I/O Errors**: Graceful handling when saving or loading files

## Performance Considerations

- **Token Estimation**: Uses rough approximation (1 token ≈ 4 characters)
- **Streaming Animation**: 10ms delay between tokens for natural feel
- **Auto-scroll**: Only scrolls when new messages arrive
- **Async I/O**: Non-blocking API calls and file operations

## Troubleshooting

### "Connection refused" error
- Verify your `OPENAI_BASE_URL` is correct
- Check that your API endpoint is running
- Ensure firewall/proxy settings allow the connection

### "Invalid API key" error
- Check `OPENAI_API_KEY` in .env
- Regenerate API key if needed

### Slow responses
- Check network connection
- Verify API endpoint is responsive
- Check `OPENAI_MODEL` exists and is available

### File picker not opening
- Ensure you have common file types in the current directory (*.py, *.md, *.txt, *.json, etc.)
- The file picker shows files with supported extensions automatically
- Use `/files` command to check currently attached files

## Development

### Adding Features

The modular architecture makes it easy to extend:

- **New Commands**: Add cases to `handle_command()` in `ui.py`
- **New API Capabilities**: Extend `APIClient` in `api.py`
- **UI Improvements**: Modify `ChatDisplay` or `ChatInput` in `ui.py`

### Testing

```bash
# Test configuration
python -c "from config import config; print(config.validate())"

# Test API connection
python -c "from api import APIClient; import asyncio; asyncio.run(APIClient().connect())"
```

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please ensure:
- Code follows PEP 8 style guide
- Functions have docstrings
- Error handling is robust
- Performance remains acceptable

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review configuration in .env
3. Check API endpoint status
4. Enable debug mode for more logging

---

**Enjoy chatting with TUI CLI!** 🚀
