"""Textual UI for the chat application."""
import asyncio
from pathlib import Path
from typing import List

from textual.app import ComposeResult
from textual.widgets import Static, Input, Button, Label
from textual.containers import ScrollableContainer, Horizontal, Vertical
from textual.screen import ModalScreen

from state import app_state
from config import config


class ChatContent(Static):
    """Inner static widget for chat display content."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _render_markdown(self, text: str) -> str:
        """
        Render markdown text to plain text with basic markup styling.
        Handles incomplete markdown gracefully during streaming.
        """
        if not text:
            return text

        try:
            import re

            result = text

            # Tables - must be done before other replacements
            # Find table blocks and style them
            def style_table_rows(match):
                table_text = match.group(0)
                lines = table_text.split('\n')
                styled_lines = []
                for i, line in enumerate(lines):
                    if i == 0:  # Header row
                        styled_lines.append(f'[bold cyan]{line}[/bold cyan]')
                    elif re.match(r'^\|[ \-\|:]+\|$', line):  # Separator row
                        styled_lines.append(f'[dim cyan]{line}[/dim cyan]')
                    else:  # Data rows
                        styled_lines.append(line)
                return '\n'.join(styled_lines)

            # Find markdown tables (identified by | delimiters)
            result = re.sub(
                r'(\|.+\|\n(?:\|[ \-\|:]+\|\n)?(?:\|.+\|\n?)*)',
                style_table_rows,
                result,
                flags=re.MULTILINE
            )

            # Headers
            result = re.sub(r'^### (.*?)$', r'[bold]\1[/bold]', result, flags=re.MULTILINE)
            result = re.sub(r'^## (.*?)$', r'[bold blue]\1[/bold blue]', result, flags=re.MULTILINE)
            result = re.sub(r'^# (.*?)$', r'[bold cyan]\1[/bold cyan]', result, flags=re.MULTILINE)

            # Bold and italic
            result = re.sub(r'\*\*\*(.*?)\*\*\*', r'[bold italic]\1[/bold italic]', result)
            result = re.sub(r'\*\*(.*?)\*\*', r'[bold]\1[/bold]', result)
            result = re.sub(r'\*(.*?)\*', r'[italic]\1[/italic]', result)
            result = re.sub(r'___(.*?)___', r'[bold italic]\1[/bold italic]', result)
            result = re.sub(r'__(.*?)__', r'[bold]\1[/bold]', result)
            result = re.sub(r'_(.*?)_', r'[italic]\1[/italic]', result)

            # Code (backticks) - use cyan color
            result = re.sub(r'`([^`]+)`', r'[cyan]\1[/cyan]', result)

            # Code blocks
            result = re.sub(r'```([^`]*?)```', r'[dim cyan]\1[/dim cyan]', result, flags=re.DOTALL)

            return result
        except Exception:
            # If markdown rendering fails, just return the original text
            return text

    def render(self):
        """Render chat messages."""
        # If there is no history, show the welcome message
        if not app_state.chat_history:
            welcome = (
                "Welcome to TUI CLI v1.0\n\n"
                "Type your message and press Enter to chat.\n"
                "Press Ctrl+C to stop streaming or quit.\n"
                "Type /help for commands."
            )
            return welcome

        # Try to use Rich renderables for better Markdown (tables, code blocks,
        # etc.). If rich isn't available or an error occurs, fall back to the
        # existing string-based renderer (_render_markdown).
        try:
            from rich.console import Group
            from rich.markdown import Markdown
            from rich.text import Text

            renderables = []

            for msg in app_state.chat_history:
                prefix = msg.prefix or ""
                content = msg.content or ""

                # Prepare prefix styling per role
                if msg.role == "system":
                    prefix_text = Text(prefix, style="dim yellow")
                    # Escape brackets in system messages
                    content_text = Text(content.replace("[", "\\[").replace("]", "\\]"))
                    renderables.append(prefix_text)
                    renderables.append(content_text)
                elif msg.role == "error":
                    prefix_text = Text(prefix, style="bold red")
                    content_text = Text(content, style="bold red")
                    renderables.append(prefix_text)
                    renderables.append(content_text)
                elif msg.role == "user":
                    prefix_text = Text(prefix, style="cyan")
                    content_text = Text(content.replace("[", "\\[").replace("]", "\\]"))
                    renderables.append(prefix_text)
                    renderables.append(content_text)
                elif msg.role == "assistant":
                    # For assistant messages use Markdown renderable so Rich
                    # will render tables, code blocks, lists, etc. Keep prefix
                    # colored green.
                    prefix_text = Text(prefix, style="green")
                    md = Markdown(content)
                    renderables.append(prefix_text)
                    renderables.append(md)
                else:
                    renderables.append(Text(prefix + content))

                # Add a blank line for spacing
                renderables.append(Text(""))

            return Group(*renderables)
        except Exception:
            # Fallback: original string-based rendering using _render_markdown
            output_lines = []
            for msg in app_state.chat_history:
                prefix = msg.prefix
                content = msg.content
                try:
                    if msg.role == "system":
                        safe_content = content.replace("[", r"\[").replace("]", r"\]")
                        line = f"[dim yellow]{prefix}[/dim yellow]{safe_content}"
                    elif msg.role == "error":
                        safe_content = content.replace("[", r"\[").replace("]", r"\]")
                        line = f"[bold red]{prefix}[/bold red][bold red]{safe_content}[/bold red]"
                    elif msg.role == "user":
                        safe_content = content.replace("[", r"\[").replace("]", r"\]")
                        line = f"[cyan]{prefix}[/cyan]{safe_content}"
                    elif msg.role == "assistant":
                        rich_text = self._render_markdown(content)
                        line = f"[green]{prefix}[/green]{rich_text}"
                    else:
                        line = f"{prefix}{content}"
                    output_lines.append(line)
                except Exception:
                    safe_prefix = prefix.replace("[", "").replace("]", "")
                    safe_content = content.replace("[", "").replace("]", "")
                    output_lines.append(f"{safe_prefix}{safe_content}")
                output_lines.append("")

            return "\n".join(output_lines)


class ChatDisplay(ScrollableContainer):
    """Display chat messages with scrolling."""
    
    def compose(self):
        """Compose the chat display."""
        yield ChatContent(id="chat-content")


class FilePickerScreen(ModalScreen):
    """Modal screen for file selection with directory navigation."""
    
    CSS = """
    FilePickerScreen {
        align: center middle;
    }
    
    #file-picker-dialog {
        width: 80%;
        height: 80%;
        background: $surface;
        border: thick $primary;
    }
    
    #file-picker-path {
        height: 2;
        background: $boost;
        padding: 0 1;
        content-align: left middle;
    }
    
    #file-list {
        height: 1fr;
        border: solid $accent;
        scrollbar-size: 1 1;
    }
    
    #file-picker-buttons {
        height: 3;
        dock: bottom;
        background: $panel;
    }
    
    .file-button {
        margin: 1;
        min-width: 10;
    }
    
    #file-picker-help {
        height: 1;
        background: $panel;
        content-align: center middle;
        padding: 0 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_directory = Path.cwd()
        self.selected_files = []
        self.file_widgets = []
        self.focused_index = 0
    
    def compose(self) -> ComposeResult:
        """Compose the file picker dialog."""
        with Vertical(id="file-picker-dialog"):
            yield Label(str(self.current_directory), id="file-picker-path")
            yield ScrollableContainer(id="file-list")
            yield Label(
                "[cyan]↑↓[/] Navigate | [cyan]Enter[/] Select/Open | [cyan]Esc[/] Cancel",
                id="file-picker-help"
            )
            with Horizontal(id="file-picker-buttons"):
                yield Button("Add Selected", variant="primary", id="add-files", classes="file-button")
                yield Button("Cancel", variant="default", id="cancel-files", classes="file-button")
    
    def on_mount(self) -> None:
        """Initialize file list when screen mounts."""
        self.populate_file_list()
        # Focus on first item with cursor highlight
        if self.file_widgets:
            self._update_focus()
    
    def populate_file_list(self) -> None:
        """Populate the file list with files and directories."""
        try:
            file_container = self.query_one("#file-list", ScrollableContainer)
            
            # Clear existing widgets
            file_container.remove_children()
            self.file_widgets.clear()
            self.focused_index = 0
            
            # Update path display
            path_label = self.query_one("#file-picker-path", Label)
            path_label.update(str(self.current_directory))
            
            items = []
            
            # Add parent directory option (except at root)
            if self.current_directory.parent != self.current_directory:
                items.append(("../", self.current_directory.parent, True))
            
            # Get all items (files and directories)
            try:
                for item in sorted(self.current_directory.iterdir()):
                    if item.is_dir():
                        items.append((f"📁 {item.name}/", item, True))
                    elif item.is_file():
                        # Check if it's a supported file type
                        if self._is_supported_file(item):
                            items.append((item.name, item, False))
            except PermissionError:
                file_container.mount(Label("[red]Permission denied[/red]"))
                return
            
            if not items:
                file_container.mount(Label("No files or directories found"))
                return
            
            # Create file selection widgets
            for display_name, full_path, is_dir in items:
                file_widget = FileItem(full_path, display_name, is_dir)
                self.file_widgets.append(file_widget)
                file_container.mount(file_widget)
                
        except Exception as e:
            file_container = self.query_one("#file-list", ScrollableContainer)
            file_container.mount(Label(f"[red]Error: {str(e)}[/red]"))
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """Check if file is a supported type."""
        supported_extensions = {
            ".py", ".md", ".txt", ".json", ".yaml", ".yml",
            ".toml", ".cfg", ".ini", ".csv", ".xml", ".html",
            ".js", ".ts", ".css", ".sh", ".bash", ".zsh"
        }
        return file_path.suffix.lower() in supported_extensions
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel-files":
            # Clear selected files when canceling
            app_state.clear_selected_files()
            self.dismiss(False)
    
    def on_key(self, event) -> None:
        """Handle keyboard shortcuts."""
        if event.key == "escape":
            app_state.clear_selected_files()
            self.dismiss(False)
            event.prevent_default()
        elif event.key == "up":
            # Navigate up in list
            if self.file_widgets:
                self.focused_index = max(0, self.focused_index - 1)
                self._update_focus()
            event.prevent_default()
        elif event.key == "down":
            # Navigate down in list
            if self.file_widgets:
                self.focused_index = min(len(self.file_widgets) - 1, self.focused_index + 1)
                self._update_focus()
            event.prevent_default()
        elif event.key == "enter":
            # Add file or navigate directory
            if self.file_widgets and self.focused_index < len(self.file_widgets):
                widget = self.file_widgets[self.focused_index]
                if widget.is_directory:
                    # Navigate into directory
                    self.current_directory = widget.file_path
                    self.populate_file_list()
                else:
                    # Add this file and close picker
                    app_state.add_selected_files([widget.file_path])
                    self.dismiss(True)
            event.prevent_default()
    
    def _update_focus(self) -> None:
        """Update visual focus to current item."""
        for i, widget in enumerate(self.file_widgets):
            if i == self.focused_index:
                widget.add_class("cursor")
                widget.refresh()  # Refresh to re-render with bold
            else:
                widget.remove_class("cursor")
                widget.refresh()  # Refresh to re-render without bold


class FileItem(Static):
    """Widget representing a single file or directory in the picker."""

    CSS = """
    FileItem {
        height: 1;
        padding: 0 1;
        margin: 0;
    }
    
    FileItem:hover {
        background: $accent 50%;
    }
    
    FileItem:focus {
        background: $accent 30%;
        border: solid $accent;
    }
    
    FileItem.cursor {
        background: $primary 60%;
        color: $text;
        border: solid $primary;
    }
    
    FileItem.cursor:hover {
        background: $primary 80%;
    }
    
    FileItem.cursor:focus {
        background: $primary 70%;
        border: solid $text;
    }
    """
    
    def __init__(self, file_path: Path, display_name: str, is_directory: bool, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path
        self.display_name = display_name
        self.is_directory = is_directory
        self.can_focus = True
        
    def render(self) -> str:
        """Render the file item."""
        # Check if this item has focus (cursor class)
        is_focused = "cursor" in self.classes
        
        if self.is_directory:
            if is_focused:
                return f"[bold red]{self.display_name}[/bold red]"
            else:
                return f"[cyan]{self.display_name}[/cyan]"
        
        # Show file with size, no checkbox
        size = ""
        try:
            file_size = self.file_path.stat().st_size
            if file_size < 1024:
                size = f"{file_size}B"
            elif file_size < 1024 * 1024:
                size = f"{file_size // 1024}KB"
            else:
                size = f"{file_size // (1024 * 1024)}MB"
        except (OSError, IOError):
            size = "---"
        
        # Make focused file bold
        if is_focused:
            return f"[bold red]{self.display_name} ({size})[/bold red]"
        else:
            return f"{self.display_name} ({size})"


class StreamingIndicator(Static):
    """Widget that shows a pulsating indicator when streaming."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._pulse_timer = None
        self._pulse_state = 0
    
    def render(self) -> str:
        """Render the streaming indicator."""
        if app_state.is_streaming():
            return "⟳ Streaming..."
        else:
            return ""
    
    def on_mount(self) -> None:
        """Set up when mounted."""
        self.update_indicator()
    
    def update_indicator(self) -> None:
        """Update the indicator state and styling."""
        is_streaming = app_state.is_streaming()
        self.display = is_streaming
        if is_streaming:
            self.add_class("streaming")
            self._start_pulsing()
        else:
            self.remove_class("streaming")
            self._stop_pulsing()
        self.refresh()
    
    def _start_pulsing(self) -> None:
        """Start the pulsating animation."""
        if self._pulse_timer is None:
            self._pulse_timer = self.set_interval(0.5, self._pulse_step)
    
    def _stop_pulsing(self) -> None:
        """Stop the pulsating animation."""
        if self._pulse_timer is not None:
            self._pulse_timer.stop()
            self._pulse_timer = None
        # Reset to normal state
        self._pulse_state = 0
        self.remove_class("pulse-dim")
    
    def _pulse_step(self) -> None:
        """Step through the pulse animation."""
        self._pulse_state = (self._pulse_state + 1) % 2
        if self._pulse_state == 0:
            self.remove_class("pulse-dim")
        else:
            self.add_class("pulse-dim")
        self.refresh()


class MessageInput(Input):
    """Custom input widget with message history navigation."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history_index = -1  # -1 means current input, 0+ means history
        self.current_input = ""   # Store the current input when navigating history
    
    def get_user_messages(self) -> List[str]:
        """Get list of user messages from history."""
        return [msg.content for msg in app_state.chat_history if msg.role == "user"]
    
    def on_key(self, event) -> None:
        """Handle key events for history navigation."""
        if event.key == "up":
            # Navigate to previous message
            user_messages = self.get_user_messages()
            if user_messages:
                if self.history_index == -1:
                    # First time navigating, save current input
                    self.current_input = self.value
                self.history_index = min(self.history_index + 1, len(user_messages) - 1)
                if self.history_index < len(user_messages):
                    self.value = user_messages[-(self.history_index + 1)]  # Most recent first
                event.prevent_default()
        elif event.key == "down":
            # Navigate to next message or back to current input
            user_messages = self.get_user_messages()
            if self.history_index > 0:
                self.history_index -= 1
                self.value = user_messages[-(self.history_index + 1)]
            elif self.history_index == 0:
                # Back to current input
                self.history_index = -1
                self.value = self.current_input
            event.prevent_default()
        else:
            # Any other key resets history navigation
            if self.history_index != -1:
                self.history_index = -1
                self.current_input = ""
            # Let the input handle other keys normally (no prevent_default)


class TUI:
    """Main TUI application using Textual."""
    
    def __init__(self):
        """Initialize the CLI."""
        pass
    
    async def run(self) -> None:
        """Run the TUI application."""
        from textual.app import App
        
        class ChatApp(App):
            """Textual Chat Application."""
            
            CSS = """
            $accent: #00aa00;
            
            Screen {
                layout: vertical;
            }
            
            #banner {
                height: 4;
                dock: top;
                border: solid $accent;
                content-align: center middle;
            }
            
            #chat-display {
                height: 1fr;
                border: solid $accent;
                overflow: auto;
            }
            
            #input-info {
                dock: bottom;
                height: 1;
            }
            
            #streaming-indicator {
                dock: bottom;
                height: 3;
                content-align: center middle;
                color: $primary;
            }
            
            #streaming-indicator.streaming {
                background: $primary 20%;
            }
            
            #streaming-indicator.pulse-dim {
                opacity: 0.3;
            }
            
            #message-input {
                dock: bottom;
                height: 3;
                border: solid $accent;
            }
            
            #commands {
                dock: bottom;
                height: 1;
                background: $panel;
            }
            """
            
            def compose(self) -> ComposeResult:
                """Create child widgets."""
                yield Static(self.get_banner(), id="banner")
                yield ChatDisplay(id="chat-display")
                yield Static(self.get_input_instruction(), id="input-info")
                yield MessageInput(
                    placeholder="Type # to attach files (auto-opens picker) or /help for commands...",
                    id="message-input"
                )
                yield StreamingIndicator(id="streaming-indicator")
                # yield Static(self.get_commands_help(), id="commands")
            
            def get_banner(self) -> str:
                """Get simple banner text with CSS border."""
                return "[bold green]TUI CLI v1.0 - OpenAI-Compatible Chat Application[/bold green]"
            
            def get_input_instruction(self) -> str:
                """Get input instructions."""
                return "[dim cyan]Press Enter to send, Ctrl+C to stop or quit, Esc to stop streaming, /help for commands[/dim cyan]"
            
            def get_commands_help(self) -> str:
                """Get commands help text."""
                return (
                    "[cyan]/help[/] - Show commands | "
                    "[cyan]/clear[/] - Clear history | "
                    "[cyan]/save[/] - Save chat | "
                    "[cyan]/files[/] - Show attached files | "
                    "[cyan]/exit[/] - Quit"
                )
            
            def on_mount(self) -> None:
                """App mounted."""
                app_state.add_system_message("Connected! Type a message or use /help")
                self.refresh_chat_display()
                
                # Focus on input
                input_widget = self.query_one("#message-input", MessageInput)
                input_widget.focus()
            
            def on_resize(self, event) -> None:
                """Handle terminal resize."""
                # Refresh the banner when terminal is resized
                banner = self.query_one("#banner", Static)
                banner.update(self.get_banner())
            
            def on_key(self, event) -> None:
                """Handle global key events."""
                if event.key == "ctrl+c":
                    event.prevent_default()
                    # Check if currently streaming
                    if app_state.is_streaming():
                        # Cancel the streaming
                        if app_state.cancel_streaming():
                            app_state.add_system_message("Streaming cancelled.")
                            self.refresh_chat_display()
                    else:
                        # Exit application gracefully
                        self.exit()
                elif event.key == "escape":
                    event.prevent_default()
                    # Escape only stops streaming if currently streaming
                    if app_state.is_streaming():
                        if app_state.cancel_streaming():
                            app_state.add_system_message("Streaming cancelled.")
                            self.refresh_chat_display()
            
            def on_input_submitted(self, event: Input.Submitted) -> None:
                """Handle input submission from Input widget."""
                try:
                    user_input = event.value.strip()
                    if user_input:
                        event.control.value = ""
                        # Process input immediately (sync path first, then async if needed)
                        self._handle_input_sync(user_input)
                except Exception as e:
                    app_state.add_error_message(f"Input error: {str(e)}")
                    self.refresh_chat_display()
            
            def on_input_changed(self, event: Input.Changed) -> None:
                """Handle input changes to auto-open file picker on '#'."""
                if event.value == "#":
                    # Clear the input and open file picker automatically
                    event.control.value = ""
                    self.run_worker(self._worker_file_selector())
            
            def _handle_input_sync(self, user_input: str) -> None:
                """Handle input that can be processed synchronously."""
                user_input = user_input.strip()
                
                if not user_input:
                    return
                
                # Handle commands
                if user_input.startswith("/"):
                    self._handle_command_sync(user_input)
                    return
                
                # Regular message - schedule async AI response as a worker
                app_state.add_user_message(user_input)
                self.refresh_chat_display()
                self.run_worker(self._worker_get_response(user_input))
            
            def _handle_command_sync(self, cmd: str) -> None:
                """Handle special commands (synchronously where possible)."""
                if cmd == "/exit":
                    self.exit()
                elif cmd == "/help":
                    help_text = (
                        "Available commands:\n"
                        "  /help       - Show this help\n"
                        "  /clear      - Clear chat history\n"
                        "  /save       - Save chat to chat_log.txt\n"
                        "  /files      - Show attached files\n"
                        "  /clearfiles - Clear attached files\n"
                        "  /exit       - Quit application\n\n"
                        "File attachment (type '#' to auto-open file picker):\n"
                        "  ↑↓          - Navigate files/folders\n"
                        "  Enter       - Add file or open folder\n"
                        "  Escape      - Cancel file picker\n\n"
                        "File contents are automatically included as context"
                    )
                    app_state.add_system_message(help_text)
                elif cmd == "/clear":
                    app_state.clear_history()
                    app_state.add_system_message("Chat history cleared")
                elif cmd == "/clearfiles":
                    app_state.clear_selected_files()
                    app_state.add_system_message("Attached files cleared")
                elif cmd == "/files":
                    if app_state.selected_files:
                        files = ", ".join(f.name for f in app_state.selected_files)
                        app_state.add_system_message(f"Attached files: {files}")
                    else:
                        app_state.add_system_message("No files attached")
                elif cmd == "/save":
                    try:
                        with open("chat_log.txt", "w") as f:
                            for msg in app_state.chat_history:
                                f.write(f"{msg.prefix}{msg.content}\n\n")
                        app_state.add_system_message("Chat saved to chat_log.txt")
                    except Exception as e:
                        app_state.add_error_message(f"Failed to save chat: {str(e)}")
                else:
                    app_state.add_error_message(f"Unknown command: {cmd}")
                
                self.refresh_chat_display()
            
            async def _worker_file_selector(self) -> None:
                """Worker for file selector."""
                await self.open_file_selector()
            
            async def _worker_get_response(self, user_message: str) -> None:
                """Worker for AI response."""
                # Get the current task and track it
                task = asyncio.current_task()
                app_state.set_streaming_task(task)
                try:
                    await self.get_ai_response(user_message)
                except asyncio.CancelledError:
                    pass
                finally:
                    app_state.set_streaming_task(None)
            
            async def open_file_selector(self) -> None:
                """Open file selector dialog."""
                try:
                    # Clear files before opening picker
                    app_state.clear_selected_files()
                    
                    # Push the file picker screen as a modal
                    file_picker = FilePickerScreen()
                    
                    # Use a callback to handle result when screen closes
                    def handle_file_picker_result(result):
                        count = len(app_state.selected_files)
                        if count > 0:
                            file_names = [f.name for f in app_state.selected_files]
                            app_state.add_system_message(
                                f"Attached {count} file(s): {', '.join(file_names)}"
                            )
                        else:
                            if result is False:
                                app_state.add_system_message("File selection cancelled")
                            else:
                                app_state.add_system_message("No files selected")
                        
                        self.refresh_chat_display()
                    
                    self.push_screen(file_picker, handle_file_picker_result)
                    
                except Exception as e:
                    app_state.add_error_message(f"File picker error: {str(e)}")
                    self.refresh_chat_display()
            
            async def get_ai_response(self, user_message: str) -> None:
                """Get response from AI."""
                from api import APIClient
                
                try:
                    app_state.is_waiting_for_response = True
                    
                    # Prepare messages for API
                    messages = app_state.get_conversation_for_api()
                    
                    # Check token limits
                    tokens = app_state.estimate_tokens(user_message)
                    if tokens > config.max_tokens * 0.8:
                        app_state.add_system_message(
                            "Warning: Message may exceed token limit. Streaming response..."
                        )
                        self.refresh_chat_display()
                    
                    # Add empty assistant message for streaming
                    app_state.add_assistant_message("")
                    self.refresh_chat_display()
                    
                    # Stream response from API
                    response_text = ""
                    async with APIClient() as client:
                        try:
                            async for token in client.stream_chat(
                                messages,
                                max_tokens=config.max_tokens,
                            ):
                                # Check for cancellation
                                try:
                                    task = asyncio.current_task()
                                    if task and task.cancelled():
                                        raise asyncio.CancelledError()
                                except RuntimeError:
                                    pass
                                
                                response_text += token
                                
                                # Update the last message with accumulated response
                                if app_state.chat_history and app_state.chat_history[-1].role == "assistant":
                                    app_state.chat_history[-1].content = response_text
                                
                                # Refresh display for every token for better responsiveness
                                self.refresh_chat_display()
                                
                                # Yield control to event loop more frequently
                                await asyncio.sleep(0.001)
                        except asyncio.CancelledError:
                            # Streaming was cancelled - don't re-raise, just handle it
                            # app_state.add_system_message("[Streaming cancelled by user]")
                            self.refresh_chat_display()
                        except Exception as stream_error:
                            app_state.add_error_message(f"Stream error: {str(stream_error)}")
                            self.refresh_chat_display()
                    
                    app_state.is_waiting_for_response = False
                    app_state.set_streaming_task(None)
                    self.refresh_chat_display()
                
                except Exception as e:
                    app_state.add_error_message(f"API Error: {str(e)}")
                    app_state.is_waiting_for_response = False
                    app_state.set_streaming_task(None)
                    self.refresh_chat_display()
            
            def refresh_chat_display(self) -> None:
                """Refresh the chat display widget."""
                try:
                    chat_container = self.query_one("#chat-display", ScrollableContainer)
                    chat_content = chat_container.query_one("#chat-content", ChatContent)
                    content_to_render = chat_content.render()
                    chat_content.update(content_to_render)
                    chat_container.scroll_end(animate=False)
                    
                    # Update streaming indicator
                    indicator = self.query_one("#streaming-indicator", StreamingIndicator)
                    indicator.update_indicator()
                    
                    # Update input visibility based on streaming state
                    input_widget = self.query_one("#message-input", MessageInput)
                    input_widget.display = not app_state.is_streaming()
                    
                except Exception:
                    # If there's a rendering error, try to display a safe fallback
                    try:
                        chat_container = self.query_one("#chat-display", ScrollableContainer)
                        chat_content = chat_container.query_one("#chat-content", ChatContent)
                        # Display plain text fallback without markup
                        plain_text = "\n".join([
                            f"{msg.prefix}{msg.content}"
                            for msg in app_state.chat_history
                        ])
                        chat_content.update(plain_text)
                        chat_container.scroll_end(animate=False)
                        
                        # Update streaming indicator
                        indicator = self.query_one("#streaming-indicator", StreamingIndicator)
                        indicator.update_indicator()
                        
                        # Update input visibility based on streaming state
                        input_widget = self.query_one("#message-input", MessageInput)
                        input_widget.display = not app_state.is_streaming()
                        
                    except Exception:
                        # If even fallback fails, log silently
                        import sys
                        print("ERROR refreshing display", file=sys.stderr)
        
        app = ChatApp()
        await app.run_async()
