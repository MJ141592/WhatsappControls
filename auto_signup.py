#!/usr/bin/env python3
"""Automatic sign-up responder for group lists."""
import asyncio
import typer
from utils import setup_logging, console
from whatsapp_automation import auto_signup_live


def main(
    chat: str = typer.Argument(..., help="Group chat name"),
    interval: int = typer.Option(1, "--interval", "-i", help="Poll interval seconds"),
):
    setup_logging()
    async def run():
        await auto_signup_live(chat_name=chat, poll_interval=interval)
    console.print(f"✍️  Auto-signup running in {chat}. Ctrl-C to stop.")
    asyncio.run(run())


if __name__ == "__main__":
    typer.run(main) 