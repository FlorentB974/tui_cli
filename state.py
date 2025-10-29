"""Application state management."""
import asyncio
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class Message:
    """Represents a single message."""
    
    role: str  # "user", "assistant", "system"
    content: str
    prefix: str = ""  # For display (e.g., "You > ", "AI > ")
    color: str = ""   # For display (e.g., "cyan", "green")


@dataclass
class AppState:
    """Manages application state."""
    
    chat_history: List[Message] = field(default_factory=list)
    selected_files: List[Path] = field(default_factory=list)
    file_contents: dict = field(default_factory=dict)  # filename -> content mapping
    current_input: str = ""
    is_waiting_for_response: bool = False
    streaming_task: Optional[asyncio.Task] = None  # Track the current streaming task
    
    def add_message(self, role: str, content: str, prefix: str = "", color: str = "") -> None:
        """Add a message to chat history."""
        msg = Message(role=role, content=content, prefix=prefix, color=color)
        self.chat_history.append(msg)
    
    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.add_message("system", content, prefix="Sys > ", color="yellow")
    
    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message("user", content, prefix="You > ", color="cyan")
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message("assistant", content, prefix="AI > ", color="green")
    
    def add_error_message(self, error: str) -> None:
        """Add an error message."""
        self.add_message("error", error, prefix="Sys > ", color="red")
    
    def add_selected_files(self, files: List[Path]) -> None:
        """Add selected files and load their contents."""
        self.selected_files = files
        self.file_contents.clear()
        
        for file_path in files:
            try:
                if file_path.is_file():
                    with open(file_path, "r", encoding="utf-8") as f:
                        self.file_contents[file_path.name] = f.read()
            except Exception as e:
                self.add_error_message(f"Failed to read {file_path.name}: {str(e)}")
    
    def clear_selected_files(self) -> None:
        """Clear selected files."""
        self.selected_files.clear()
        self.file_contents.clear()
    
    def get_context_prompt(self) -> str:
        """Get context prompt with file contents."""
        if not self.file_contents:
            return ""
        
        context_parts = ["Additional context from attached files:"]
        for filename, content in self.file_contents.items():
            context_parts.append(f"\n--- File: {filename} ---\n{content}")
        
        return "\n".join(context_parts)
    
    def clear_history(self) -> None:
        """Clear chat history."""
        self.chat_history.clear()
    
    def get_conversation_for_api(self) -> List[dict]:
        """Get conversation history formatted for API with file context."""
        messages = []
        
        # Add file context as a system message at the beginning if files are attached
        context_prompt = self.get_context_prompt()
        if context_prompt:
            messages.append({
                "role": "system",
                "content": context_prompt
            })
        
        # Add chat history
        for msg in self.chat_history:
            if msg.role != "error" and msg.role != "system":
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return messages
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: 1 token ≈ 4 characters)."""
        return len(text) // 4
    
    def get_estimated_message_tokens(self) -> int:
        """Estimate total tokens in conversation."""
        total = 0
        for msg in self.chat_history:
            if msg.role in ("user", "assistant"):
                total += self.estimate_tokens(msg.content)
        return total
    
    def set_streaming_task(self, task: Optional[asyncio.Task]) -> None:
        """Set the current streaming task."""
        self.streaming_task = task
    
    def cancel_streaming(self) -> bool:
        """Cancel the current streaming task if any. Returns True if cancelled."""
        if self.streaming_task and not self.streaming_task.done():
            self.streaming_task.cancel()
            return True
        return False
    
    def is_streaming(self) -> bool:
        """Check if currently streaming."""
        return self.streaming_task is not None and not self.streaming_task.done()


# Global state instance
app_state = AppState()
