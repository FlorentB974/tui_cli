"""OpenAI-compatible API client with streaming."""
import asyncio
import aiohttp
import json
from typing import AsyncGenerator, List, Optional, Dict
from config import config


class APIClient:
    """Async OpenAI-compatible API client with streaming support."""
    
    def __init__(self):
        """Initialize API client."""
        self.base_url = config.base_url.rstrip("/")
        self.api_key = config.api_key
        self.model = config.model
        self.proxy = config.proxy
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Create session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=None)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def disconnect(self) -> None:
        """Close session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.1,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion tokens.
        
        Args:
            messages: List of message dicts with "role" and "content"
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            
        Yields:
            Tokens as they arrive from the API
        """
        if self.session is None:
            await self.connect()
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        try:
            async with self.session.post(
                url,
                json=payload,
                headers=headers,
                proxy=self.proxy,
                ssl=False,
            ) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    raise Exception(f"API error {resp.status}: {error_text}")
                
                async for line in resp.content:
                    # Check for cancellation frequently
                    try:
                        asyncio.current_task()
                    except RuntimeError:
                        raise asyncio.CancelledError()
                    
                    line = line.decode("utf-8").strip()
                    
                    if not line:
                        continue
                    
                    if line.startswith("data: "):
                        line = line[6:]
                    
                    if line == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(line)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        token = delta.get("content", "")
                        if token:
                            yield token
                    except json.JSONDecodeError:
                        continue
        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            raise Exception(f"Streaming error: {str(e)}")
    
    async def estimate_request_tokens(self, messages: List[Dict[str, str]]) -> int:
        """Estimate token count for messages (rough approximation)."""
        total = 0
        for msg in messages:
            total += len(msg.get("content", "")) // 4
        return total
