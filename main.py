#!/usr/bin/env python3
"""Main entry point for Codex CLI TUI chat application."""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from ui import CodexCLI


async def main():
    """Main entry point."""
    # Validate configuration
    if not config.validate():
        print("Error: Invalid configuration. Please check your .env file.")
        print(f"  OPENAI_BASE_URL: {config.base_url}")
        print(f"  OPENAI_API_KEY: {'*' * len(config.api_key) if config.api_key else 'NOT SET'}")
        print(f"  OPENAI_MODEL: {config.model}")
        sys.exit(1)
    
    # Run the CLI
    cli = CodexCLI()
    await cli.run()


if __name__ == "__main__":
    asyncio.run(main())
