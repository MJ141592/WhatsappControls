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
        
        # Use system ChromeDriver
        service = Service("/usr/bin/chromedriver")
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
            # Check if already logged in - look for chat list
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label*="Chat list"]'))
            )
            logger.info("Already logged in to WhatsApp Web")
            
        except TimeoutException:
            # Need to scan QR code
            logger.info("Please scan the QR code to log in to WhatsApp Web...")
            
            # Wait for login completion - look for chat list
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label*="Chat list"]'))
            )
            logger.info("Successfully logged in to WhatsApp Web")
    
    def get_chat_list(self) -> List[str]:
        """Get list of available chats."""
        try:
            # Wait a bit for chats to load
            time.sleep(3)
            
            # Find individual chat items using modern selector
            chat_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                'div[role="gridcell"]'
            )
            
            chats = []
            for element in chat_elements[:10]:  # Limit to first 10 chats
                try:
                    # Try to get chat name from the element text
                    text = element.text.strip()
                    if text and len(text) > 0:
                        # Get first line which is usually the chat name
                        chat_name = text.split('\n')[0]
                        if chat_name and chat_name not in chats:
                            chats.append(chat_name)
                except Exception:
                    continue
            
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chat list: {e}")
            return []
    
    def select_chat(self, chat_name: str) -> bool:
        """Select a specific chat by name."""
        try:
            # First try to find the search box
            search_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="textbox"]')
            
            if search_elements:
                search_box = search_elements[0]
                search_box.clear()
                search_box.send_keys(chat_name)
                
                time.sleep(2)  # Wait for search results
                
                # Click on the first result
                chat_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="gridcell"]')
                if chat_elements:
                    chat_elements[0].click()
                    
                    # Clear search
                    search_box.clear()
                    
                    logger.info(f"Selected chat: {chat_name}")
                    return True
            
            # Alternative method: find chat directly by text content
            chat_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="gridcell"]')
            
            for element in chat_elements:
                try:
                    if chat_name.lower() in element.text.lower():
                        element.click()
                        logger.info(f"Selected chat: {chat_name}")
                        return True
                except Exception:
                    continue
            
            logger.warning(f"Chat '{chat_name}' not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to select chat '{chat_name}': {e}")
            return False
    
    def send_message(self, message: str) -> bool:
        """Send a message to the currently selected chat."""
        try:
            # Find the specific message input box (not the search box)
            message_selectors = [
                'div[contenteditable="true"][aria-label="Type a message"]',  # Specific message input
                'div[contenteditable="true"][data-tab="10"]',  # Alternative: by data-tab
                'div[contenteditable="true"][role="textbox"]:not([aria-label*="Search"])',  # Not search
            ]
            
            message_box = None
            for selector in message_selectors:
                try:
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    
                    # Find the one that's actually visible and in the right position
                    for elem in elements:
                        if elem.is_displayed():
                            location = elem.location
                            # Message input should be lower on the page (y > 400)
                            if location['y'] > 400:
                                message_box = elem
                                logger.info(f"Found message input using: {selector}")
                                break
                    
                    if message_box:
                        break
                        
                except TimeoutException:
                    continue
            
            if not message_box:
                # Fallback: find any contenteditable that's not the search box
                all_editable = self.driver.find_elements(By.CSS_SELECTOR, 'div[contenteditable="true"]')
                for elem in all_editable:
                    if elem.is_displayed():
                        location = elem.location
                        aria_label = elem.get_attribute('aria-label') or ''
                        
                        # Skip search boxes
                        if 'search' in aria_label.lower():
                            continue
                            
                        # Use the one that's lower on the page
                        if location['y'] > 400:
                            message_box = elem
                            logger.info("Found message input using fallback method")
                            break
            
            if not message_box:
                logger.error("Could not find message input box")
                return False
            
            # Focus the input properly
            message_box.click()
            time.sleep(0.5)
            
            # Clear any existing content multiple ways
            message_box.clear()
            
            # Use JavaScript to clear if needed
            self.driver.execute_script("arguments[0].innerHTML = '';", message_box)
            time.sleep(0.5)
            
            # Type the message character by character for reliability
            for char in message:
                message_box.send_keys(char)
                time.sleep(0.02)  # Small delay between characters
            
            time.sleep(1)  # Wait for message to be fully typed
            
            # Verify the message was typed
            current_text = message_box.text or message_box.get_attribute('textContent') or ''
            if message not in current_text:
                logger.warning("Message not properly entered, retrying...")
                message_box.clear()
                self.driver.execute_script("arguments[0].innerHTML = '';", message_box)
                message_box.send_keys(message)
                time.sleep(1)
            
            # Try multiple send methods
            sent = False
            
            # Method 1: Enter key (most reliable)
            try:
                from selenium.webdriver.common.keys import Keys
                message_box.send_keys(Keys.RETURN)
                time.sleep(1)
                
                # Check if message was sent (input should be empty)
                new_text = message_box.text or message_box.get_attribute('textContent') or ''
                if not new_text.strip():
                    logger.info(f"Sent message via Enter key: {message[:50]}...")
                    return True
                    
            except Exception as e:
                logger.warning(f"Enter key method failed: {e}")
            
            # Method 2: Look for send button with more patterns
            send_selectors = [
                'button[aria-label*="Send"]',
                'span[data-icon="send"]',
                'button[data-icon="send"]',
                '[data-testid="send"]',
                'button[title*="Send"]',
                'span[title*="Send"]',
                'button[aria-label*="send"]',  # case insensitive
                'div[role="button"][aria-label*="Send"]',
                'svg[data-icon="send"]',
                'button:has(span[data-icon="send"])',
            ]
            
            for selector in send_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            time.sleep(1)
                            
                            # Check if message was sent
                            new_text = message_box.text or message_box.get_attribute('textContent') or ''
                            if not new_text.strip():
                                logger.info(f"Sent message via button ({selector}): {message[:50]}...")
                                return True
                except Exception:
                    continue
            
            # Method 3: Try Ctrl+Enter
            try:
                message_box.send_keys(Keys.CONTROL + Keys.RETURN)
                time.sleep(1)
                
                new_text = message_box.text or message_box.get_attribute('textContent') or ''
                if not new_text.strip():
                    logger.info(f"Sent message via Ctrl+Enter: {message[:50]}...")
                    return True
                    
            except Exception as e:
                logger.warning(f"Ctrl+Enter method failed: {e}")
            
            # Method 4: JavaScript click on any element that might be the send button
            try:
                # Find any clickable element near the input that might be send button
                possible_send_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    'button, span[data-icon], div[role="button"]'
                )
                
                for element in possible_send_elements:
                    try:
                        # Check if element is in the right area (near message input)
                        if element.is_displayed():
                            # Try clicking with JavaScript
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(1)
                            
                            # Check if message was sent
                            new_text = message_box.text or message_box.get_attribute('textContent') or ''
                            if not new_text.strip():
                                logger.info(f"Sent message via JS click: {message[:50]}...")
                                return True
                    except:
                        continue
                        
            except Exception as e:
                logger.warning(f"JavaScript click method failed: {e}")
            
            # If we get here, none of the methods worked
            logger.error("All send methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_recent_messages(self, limit: int = 10) -> List[WhatsAppMessage]:
        """Get recent messages from the current chat."""
        try:
            # Wait a bit for messages to load
            time.sleep(2)
            
            # Modern WhatsApp Web message selectors
            message_selectors = [
                'div[data-id*="BAE5"]',  # WhatsApp message containers often have this pattern
                'div[role="row"]',  # Message rows in chat
                'div[class*="_akbu"]',  # Common WhatsApp message class pattern
                'div[class*="message"]',  # Any element with "message" in class
                '.copyable-text',  # Traditional selector that might still work
                'div[data-id]',  # Fallback to any data-id elements
            ]
            
            message_elements = []
            working_selector = None
            
            for selector in message_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) > 0:
                        message_elements = elements
                        working_selector = selector
                        logger.info(f"Found {len(elements)} messages using selector: {selector}")
                        break
                except Exception:
                    continue
            
            if not message_elements:
                logger.warning("No message elements found with any selector")
                return []
            
            messages = []
            chat_title = self._get_current_chat_name()
            
            # Process the most recent messages
            recent_elements = message_elements[-limit:] if len(message_elements) > limit else message_elements
            
            for i, element in enumerate(recent_elements):
                try:
                    # Get message content - try multiple methods
                    content = ""
                    
                    # Method 1: Direct text
                    content = element.text.strip()
                    
                    # Method 2: Look for specific message text containers
                    if not content:
                        text_containers = element.find_elements(
                            By.CSS_SELECTOR, 
                            '.copyable-text, [data-pre-plain-text], span[dir="ltr"], span[dir="auto"]'
                        )
                        for container in text_containers:
                            text = container.text.strip()
                            if text and len(text) > len(content):
                                content = text
                    
                    # Skip if no content found
                    if not content or len(content.strip()) == 0:
                        continue
                    
                    # Clean up content (remove timestamps, extra whitespace)
                    content_lines = content.split('\n')
                    # The actual message is usually the longest line or the last substantial line
                    actual_message = ""
                    for line in content_lines:
                        line = line.strip()
                        if line and not self._is_timestamp_or_status(line):
                            if len(line) > len(actual_message):
                                actual_message = line
                    
                    if not actual_message:
                        actual_message = content.split('\n')[0].strip()  # Fallback to first line
                    
                    # Determine if message is outgoing
                    is_outgoing = self._is_outgoing_message(element)
                    
                    # Get timestamp (approximate)
                    timestamp = self._extract_timestamp(element) or datetime.now()
                    
                    # Create message object
                    message = WhatsAppMessage(
                        sender="You" if is_outgoing else chat_title or "Contact",
                        content=actual_message,
                        timestamp=timestamp,
                        is_outgoing=is_outgoing,
                        chat_name=chat_title or "Current Chat"
                    )
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.debug(f"Error processing message element {i}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(messages)} messages from {len(recent_elements)} elements")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get recent messages: {e}")
            return []
    
    def _get_current_chat_name(self) -> str:
        """Get the name of the currently open chat."""
        try:
            # Try multiple selectors for chat title
            title_selectors = [
                'header span[title]',  # Chat title in header
                'header [data-testid="conversation-info-header-chat-title"]',
                'header h1',
                '[data-testid="conversation-header"] span',
            ]
            
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        title = element.get_attribute('title') or element.text.strip()
                        if title and len(title) > 0:
                            return title
                except:
                    continue
                    
            return "Unknown Chat"
            
        except Exception:
            return "Unknown Chat"
    
    def _is_outgoing_message(self, element) -> bool:
        """Determine if a message element is an outgoing message."""
        try:
            # Check various indicators for outgoing messages
            class_attr = element.get_attribute("class") or ""
            
            # Common patterns for outgoing messages
            outgoing_indicators = [
                "message-out", "msg-out", "_amk4", "_akbu", 
                "outgoing", "sent", "_ahjy"  # Various WhatsApp class patterns
            ]
            
            for indicator in outgoing_indicators:
                if indicator in class_attr:
                    return True
            
            # Check parent elements
            parent = element
            for _ in range(3):  # Check up to 3 levels up
                try:
                    parent = parent.find_element(By.XPATH, './..')
                    parent_class = parent.get_attribute("class") or ""
                    for indicator in outgoing_indicators:
                        if indicator in parent_class:
                            return True
                except:
                    break
            
            # Check if message is positioned on the right (outgoing messages are typically on the right)
            try:
                location = element.location
                size = element.size
                window_width = self.driver.get_window_size()['width']
                
                # If message is in the right half of the screen, likely outgoing
                if location['x'] + size['width'] > window_width * 0.6:
                    return True
            except:
                pass
                
            return False
            
        except Exception:
            return False
    
    def _is_timestamp_or_status(self, text: str) -> bool:
        """Check if text looks like a timestamp or status message."""
        if not text:
            return True
            
        # Common patterns for timestamps and status
        timestamp_patterns = [
            r'^\d{1,2}:\d{2}',  # Time format
            r'^Yesterday',
            r'^Today',
            r'^\w+day',  # Monday, Tuesday, etc.
            r'^\d{1,2}/\d{1,2}',  # Date format
            r'^Read$',
            r'^Delivered$',
            r'^Sent$',
            r'checkmark',
            r'✓',
        ]
        
        import re
        for pattern in timestamp_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        # Very short text is likely status
        if len(text.strip()) < 3:
            return True
            
        return False
    
    def _extract_timestamp(self, element) -> Optional[datetime]:
        """Try to extract timestamp from message element."""
        try:
            # Look for timestamp indicators
            timestamp_selectors = [
                '[data-pre-plain-text]',  # WhatsApp sometimes stores timestamp here
                '.copyable-text time',
                'time',
                'span[title*=":"]',  # Elements with time in title
            ]
            
            for selector in timestamp_selectors:
                try:
                    time_elements = element.find_elements(By.CSS_SELECTOR, selector)
                    for time_elem in time_elements:
                        time_text = time_elem.get_attribute('title') or time_elem.text
                        if time_text and ':' in time_text:
                            # Try to parse common time formats
                            import re
                            time_match = re.search(r'(\d{1,2}:\d{2})', time_text)
                            if time_match:
                                # For now, just use current date with extracted time
                                # In a full implementation, you'd parse the full timestamp
                                return datetime.now()  # Simplified
                except:
                    continue
                    
            return None
            
        except Exception:
            return None
    
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
        automation.driver = automation.setup_driver()
        await automation.connect_to_whatsapp()
        
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
        automation.driver = automation.setup_driver()
        await automation.connect_to_whatsapp()
        
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