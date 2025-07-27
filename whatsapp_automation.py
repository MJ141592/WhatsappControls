"""WhatsApp Web automation using Selenium."""

import time
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from loguru import logger

from config import settings
from llm_client import LLMManager


@dataclass
class WhatsAppMessage:
    """Represents a WhatsApp message."""
    sender: str
    content: str
    timestamp: datetime
    is_outgoing: bool
    chat_name: str


class WhatsAppAutomation:
    """Main class for WhatsApp Web automation."""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.llm_manager = LLMManager()
        self.message_history: Dict[str, List[WhatsAppMessage]] = {}
        self.processed_messages: set = set()
        
    def setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        # Use existing Chrome profile if specified
        if settings.chrome_profile_path:
            chrome_options.add_argument(f"--user-data-dir={settings.chrome_profile_path}")
        
        # Additional Chrome options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Install and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        return driver
    
    async def start(self):
        """Start the WhatsApp automation."""
        logger.info("Starting WhatsApp automation...")
        
        try:
            self.driver = self.setup_driver()
            await self.connect_to_whatsapp()
            
            if settings.auto_reply_enabled:
                await self.start_message_monitoring()
            else:
                logger.info("Auto-reply is disabled. Use manual methods to send messages.")
                
        except Exception as e:
            logger.error(f"Failed to start WhatsApp automation: {e}")
            if self.driver:
                self.driver.quit()
            raise
    
    async def connect_to_whatsapp(self):
        """Connect to WhatsApp Web and wait for QR code scan if needed."""
        logger.info("Connecting to WhatsApp Web...")
        
        self.driver.get("https://web.whatsapp.com")
        
        # Wait for either QR code or main interface
        try:
            # Check if already logged in
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
            )
            logger.info("Already logged in to WhatsApp Web")
            
        except TimeoutException:
            # Need to scan QR code
            logger.info("Please scan the QR code to log in to WhatsApp Web...")
            
            # Wait for login completion
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='chat-list']"))
            )
            logger.info("Successfully logged in to WhatsApp Web")
    
    def get_chat_list(self) -> List[str]:
        """Get list of available chats."""
        try:
            chat_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "[data-testid='chat-list'] [data-testid='cell-frame-container']"
            )
            
            chats = []
            for element in chat_elements[:10]:  # Limit to first 10 chats
                try:
                    name_element = element.find_element(
                        By.CSS_SELECTOR, 
                        "[data-testid='cell-frame-title'] span[title]"
                    )
                    chats.append(name_element.get_attribute("title"))
                except NoSuchElementException:
                    continue
            
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chat list: {e}")
            return []
    
    def select_chat(self, chat_name: str) -> bool:
        """Select a specific chat by name."""
        try:
            # Search for the chat
            search_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-list-search']"))
            )
            search_box.clear()
            search_box.send_keys(chat_name)
            
            time.sleep(2)  # Wait for search results
            
            # Click on the first result
            first_result = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='chat-list'] [data-testid='cell-frame-container']"))
            )
            first_result.click()
            
            # Clear search
            search_box.clear()
            
            logger.info(f"Selected chat: {chat_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to select chat '{chat_name}': {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send a message to the currently selected chat."""
        try:
            message_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='conversation-compose-box-input']"))
            )
            
            message_box.clear()
            message_box.send_keys(message)
            
            # Send the message
            send_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='send']")
            send_button.click()
            
            logger.info(f"Sent message: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_recent_messages(self, limit: int = 10) -> List[WhatsAppMessage]:
        """Get recent messages from the current chat."""
        try:
            message_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "[data-testid='conversation-panel-messages'] [data-testid='msg-container']"
            )
            
            messages = []
            for element in message_elements[-limit:]:
                try:
                    # Determine if message is outgoing
                    is_outgoing = "message-out" in element.get_attribute("class")
                    
                    # Get message content
                    content_element = element.find_element(
                        By.CSS_SELECTOR, 
                        ".copyable-text span"
                    )
                    content = content_element.text
                    
                    # Create message object
                    message = WhatsAppMessage(
                        sender="You" if is_outgoing else "Contact",
                        content=content,
                        timestamp=datetime.now(),
                        is_outgoing=is_outgoing,
                        chat_name="Current Chat"
                    )
                    
                    messages.append(message)
                    
                except Exception:
                    continue
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    async def start_message_monitoring(self):
        """Start monitoring for new messages and auto-reply if enabled."""
        logger.info("Starting message monitoring...")
        
        while True:
            try:
                chats = self.get_chat_list()
                
                for chat_name in chats:
                    if self.select_chat(chat_name):
                        await self.process_chat_messages(chat_name)
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in message monitoring: {e}")
                await asyncio.sleep(10)
    
    async def process_chat_messages(self, chat_name: str):
        """Process messages in a specific chat."""
        messages = self.get_recent_messages(5)
        
        for message in messages:
            message_id = f"{chat_name}_{message.content}_{message.timestamp.isoformat()}"
            
            if message_id not in self.processed_messages and not message.is_outgoing:
                self.processed_messages.add(message_id)
                
                # Analyze message intent
                intent_analysis = await self.llm_manager.analyze_message_intent(message.content)
                
                if intent_analysis.get("requires_response", True):
                    # Generate response
                    response = await self.llm_manager.generate_whatsapp_response(
                        message.content,
                        message.sender,
                        self._get_conversation_history(chat_name)
                    )
                    
                    # Wait before responding
                    await asyncio.sleep(settings.response_delay_seconds)
                    
                    # Send response
                    if self.send_message(response):
                        logger.info(f"Auto-replied to {chat_name}: {response[:50]}...")
    
    def _get_conversation_history(self, chat_name: str) -> List[Dict[str, str]]:
        """Get conversation history for a chat in LLM format."""
        if chat_name not in self.message_history:
            return []
        
        history = []
        for message in self.message_history[chat_name][-10:]:  # Last 10 messages
            role = "assistant" if message.is_outgoing else "user"
            history.append({
                "role": role,
                "content": message.content
            })
        
        return history
    
    async def stop(self):
        """Stop the automation and clean up."""
        logger.info("Stopping WhatsApp automation...")
        
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        logger.info("WhatsApp automation stopped")


# Convenience functions
async def send_message_to_contact(contact_name: str, message: str) -> bool:
    """Send a message to a specific contact."""
    automation = WhatsAppAutomation()
    
    try:
        await automation.start()
        
        if automation.select_chat(contact_name):
            result = automation.send_message(message)
            await automation.stop()
            return result
        else:
            await automation.stop()
            return False
            
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        await automation.stop()
        return False


async def get_chat_messages(contact_name: str, limit: int = 10) -> List[WhatsAppMessage]:
    """Get recent messages from a specific chat."""
    automation = WhatsAppAutomation()
    
    try:
        await automation.start()
        
        if automation.select_chat(contact_name):
            messages = automation.get_recent_messages(limit)
            await automation.stop()
            return messages
        else:
            await automation.stop()
            return []
            
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        await automation.stop()
        return [] 