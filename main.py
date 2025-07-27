"""Main entry point for WhatsApp automation tool."""

import asyncio
import os
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger

from config import settings
from whatsapp_automation import WhatsAppAutomation, send_message_to_contact, get_chat_messages
from llm_client import LLMManager

app = typer.Typer(help="WhatsApp Automation Tool with LLM Integration")
console = Console()


def setup_logging():
    """Set up logging configuration."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Configure loguru
    logger.remove()  # Remove default handler
    logger.add(
        settings.log_file,
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        rotation="1 MB",
        retention="7 days"
    )
    logger.add(
        lambda msg: console.print(msg, style="dim"),
        level=settings.log_level,
        format="{time:HH:mm:ss} | {level} | {message}"
    )


@app.command()
def start(
    auto_reply: bool = typer.Option(False, "--auto-reply", help="Enable automatic replies"),
    monitor_only: bool = typer.Option(False, "--monitor-only", help="Only monitor messages, don't reply")
):
    """Start the WhatsApp automation service."""
    setup_logging()
    
    console.print(Panel.fit("🚀 Starting WhatsApp Automation", style="bold green"))
    
    # Validate configuration
    if not settings.validate_api_keys():
        console.print("❌ Missing required API keys. Please check your .env file.", style="bold red")
        raise typer.Exit(1)
    
    async def run_automation():
        automation = WhatsAppAutomation()
        
        # Override settings based on command line args
        if monitor_only:
            settings.auto_reply_enabled = False
        elif auto_reply:
            settings.auto_reply_enabled = True
        
        try:
            await automation.start()
        except KeyboardInterrupt:
            console.print("\n🛑 Stopping automation...", style="yellow")
            await automation.stop()
        except Exception as e:
            console.print(f"❌ Error: {e}", style="bold red")
            await automation.stop()
    
    asyncio.run(run_automation())


@app.command()
def send(
    contact: str = typer.Argument(..., help="Contact name to send message to"),
    message: str = typer.Argument(..., help="Message to send")
):
    """Send a message to a specific contact."""
    setup_logging()
    
    console.print(f"📤 Sending message to {contact}...")
    
    async def send_msg():
        success = await send_message_to_contact(contact, message)
        if success:
            console.print("✅ Message sent successfully!", style="bold green")
        else:
            console.print("❌ Failed to send message", style="bold red")
    
    asyncio.run(send_msg())


@app.command()
def get_messages(
    contact: str = typer.Argument(..., help="Contact name to get messages from"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of messages to retrieve")
):
    """Get recent messages from a specific contact."""
    setup_logging()
    
    console.print(f"📥 Getting messages from {contact}...")
    
    async def get_msgs():
        messages = await get_chat_messages(contact, limit)
        
        if messages:
            table = Table(title=f"Recent Messages from {contact}")
            table.add_column("Sender", style="cyan")
            table.add_column("Message", style="white")
            table.add_column("Time", style="dim")
            
            for msg in messages:
                table.add_row(
                    msg.sender,
                    msg.content[:50] + "..." if len(msg.content) > 50 else msg.content,
                    msg.timestamp.strftime("%H:%M:%S")
                )
            
            console.print(table)
        else:
            console.print("❌ No messages found or failed to retrieve", style="bold red")
    
    asyncio.run(get_msgs())


@app.command()
def test_llm(
    message: str = typer.Argument(..., help="Test message for LLM"),
    provider: Optional[str] = typer.Option(None, help="LLM provider (openai/anthropic)")
):
    """Test LLM response generation."""
    setup_logging()
    
    if provider:
        settings.default_llm_provider = provider
    
    console.print(f"🤖 Testing LLM response with {settings.default_llm_provider}...")
    
    async def test_response():
        try:
            llm_manager = LLMManager()
            response = await llm_manager.generate_whatsapp_response(message, "Test User")
            
            console.print(Panel(
                f"[bold]Input:[/bold] {message}\n\n[bold]Response:[/bold] {response}",
                title="LLM Test Result",
                border_style="green"
            ))
            
        except Exception as e:
            console.print(f"❌ LLM test failed: {e}", style="bold red")
    
    asyncio.run(test_response())


@app.command()
def config():
    """Show current configuration."""
    console.print(Panel.fit("⚙️ Current Configuration", style="bold blue"))
    
    table = Table()
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    # Only show non-sensitive config
    config_items = [
        ("LLM Provider", settings.default_llm_provider),
        ("Model", settings.openai_model if settings.default_llm_provider == "openai" else settings.anthropic_model),
        ("Auto Reply", "Enabled" if settings.auto_reply_enabled else "Disabled"),
        ("Response Delay", f"{settings.response_delay_seconds}s"),
        ("Max Messages/Hour", str(settings.max_messages_per_hour)),
        ("Log Level", settings.log_level),
        ("OpenAI API Key", "Configured" if settings.openai_api_key else "Not Set"),
        ("Anthropic API Key", "Configured" if settings.anthropic_api_key else "Not Set"),
    ]
    
    for setting, value in config_items:
        table.add_row(setting, value)
    
    console.print(table)


@app.command()
def setup():
    """Interactive setup wizard."""
    console.print(Panel.fit("🔧 WhatsApp Automation Setup", style="bold blue"))
    
    # Check if .env exists
    if not os.path.exists(".env"):
        console.print("Creating .env file from template...")
        
        # Copy .env.example to .env
        with open(".env.example", "r") as example_file:
            content = example_file.read()
        
        with open(".env", "w") as env_file:
            env_file.write(content)
        
        console.print("✅ Created .env file", style="green")
    
    console.print("""
📋 Setup Checklist:

1. Edit the .env file with your API keys:
   - Add your OpenAI API key (if using OpenAI)
   - Add your Anthropic API key (if using Anthropic)

2. Install dependencies:
   pip install -r requirements.txt

3. Test your setup:
   python main.py test-llm "Hello, how are you?"

4. Start automation:
   python main.py start --auto-reply

📚 Documentation:
- Use 'python main.py --help' to see all commands
- Check the logs/ directory for detailed logs
- Ensure Chrome browser is installed for WhatsApp Web automation
    """)


if __name__ == "__main__":
    app() 