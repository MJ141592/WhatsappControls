"""Simplified WhatsApp Web automation using Selenium."""

import time
import asyncio
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
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
    """Simplified WhatsApp Web automation."""
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.llm_manager = LLMManager()
        self.processed_messages: set = set()
        
    def setup_driver(self) -> webdriver.Chrome:
        """Set up Chrome WebDriver."""
        chrome_options = Options()
        
        if settings.chrome_profile_path:
            chrome_options.add_argument(f"--user-data-dir={settings.chrome_profile_path}")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service("/usr/bin/chromedriver")
        return webdriver.Chrome(service=service, options=chrome_options)
    
    async def start(self):
        """Start the WhatsApp automation."""
        logger.info("Starting WhatsApp automation...")
        
        try:
            self.driver = self.setup_driver()
            await self.connect_to_whatsapp()
            
            if settings.auto_reply_enabled:
                await self.start_monitoring()
            else:
                logger.info("Auto-reply disabled. Use manual methods to send messages.")
                
        except Exception as e:
            logger.error(f"Failed to start: {e}")
            await self.stop()
            raise
    
    async def connect_to_whatsapp(self):
        """Connect to WhatsApp Web."""
        logger.info("Connecting to WhatsApp Web...")
        self.driver.get("https://web.whatsapp.com")
        
        try:
            # Check if already logged in
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label*="Chat list"]'))
            )
            logger.info("Already logged in")
            
        except TimeoutException:
            logger.info("Please scan QR code...")
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[aria-label*="Chat list"]'))
            )
            logger.info("Successfully logged in")
    
    def select_chat(self, contact_name: str, chat_type: str = "individual") -> bool:
        """Select a chat by contact name."""
        try:
            # 1. Search for the contact/group
            search_box = self.driver.find_element(By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="3"]')
            search_box.click()
            search_box.clear()
            search_box.send_keys(Keys.CONTROL + "a", Keys.DELETE)
            search_box.send_keys(contact_name)
            time.sleep(1)
            
            # Quick keyboard selection – press ENTER to open the first/highlighted result
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)

            # If chat still not open, try Arrow-Down + ENTER
            if not self._verify_chat_opened():
                search_box.send_keys(Keys.ARROW_DOWN, Keys.RETURN)
                time.sleep(2)

            # Verify again
            if self._verify_chat_opened():
                logger.info(f"Successfully opened {chat_type} chat via keyboard: {contact_name}")
                return True

            # 2. Find the correct search result
            results = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
            target_element = None
            for result in results:
                result_text = result.text.lower()
                if contact_name.lower() in result_text:
                    group_indicators = ['group', 'participants', 'members', 'in common']
                    is_group = any(indicator in result_text for indicator in group_indicators)
                    
                    if chat_type == "individual" and not is_group:
                        target_element = result
                        break
                    elif chat_type == "group" and is_group:
                        target_element = result
                        break
            
            if not target_element:
                logger.error(f"Could not find a matching {chat_type} in search results.")
                return False

            # 3. Click the result reliably and verify
            logger.info(f"Found '{target_element.text.splitlines()[0]}'. Attempting to open chat...")
            self.driver.execute_script("arguments[0].click();", target_element)
            
            if self._verify_chat_opened():
                logger.info(f"Successfully opened {chat_type} chat.")
                return True
            else:
                logger.error("Clicked on search result, but chat did not open.")
                return False

        except Exception as e:
            logger.error(f"Failed to select {chat_type} chat for '{contact_name}': {e}")
            return False
    
    def _verify_chat_opened(self) -> bool:
        """Verify a chat is open by reliably finding the message compose box."""
        try:
            # Wait up to 5 seconds for the compose box to appear
            wait = WebDriverWait(self.driver, 5)
            compose_box = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"][data-tab="10"]'))
            )
            # Ensure it's visible and at the bottom of the screen
            if compose_box and compose_box.is_displayed() and compose_box.location['y'] > 400:
                return True
        except TimeoutException:
            logger.debug("Verification failed: Could not find message compose box.")
            return False
        return False
    
    def _check_message_compose(self) -> bool:
        """Check for message compose elements."""
        compose_selectors = [
            'div[contenteditable="true"][data-tab="10"]',
            'div[contenteditable="true"][aria-label*="Type a message"]',
            'div[contenteditable="true"][aria-label*="type a message"]',
            'div[data-testid="conversation-compose-box-input"]',
            'div[contenteditable="true"]'
        ]
        
        for selector in compose_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.location['y'] > 300:
                        return True
            except:
                continue
        return False
    
    def _check_chat_header(self) -> bool:
        """Check for chat header elements."""
        header_selectors = [
            'header[data-testid="conversation-header"]',
            'header span[title]',
            'div[data-testid="conversation-info-header"]',
            'header'
        ]
        
        for selector in header_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.location['y'] < 200:
                        return True
            except:
                continue
        return False
    
    def _check_message_area(self) -> bool:
        """Check for message display area."""
        message_selectors = [
            '[data-testid="conversation-panel-body"]',
            'div[class*="message"]',
            '[data-testid="msg-container"]'
        ]
        
        for selector in message_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    return True
            except:
                continue
        return False
    
    def send_message(self, message: str) -> bool:
        """Send a message to current chat."""
        try:
            # Wait a moment for chat to fully load
            time.sleep(2)
            
            # Try multiple selectors for message input
            input_selectors = [
                'div[contenteditable="true"][data-tab="10"]',  # Original
                'div[contenteditable="true"][aria-label*="Type a message"]',  # By aria-label
                'div[contenteditable="true"][aria-label*="type a message"]',  # Case variation
                'div[contenteditable="true"][role="textbox"]',  # By role
                'div[data-testid="conversation-compose-box-input"]',  # Possible new selector
                'div[contenteditable="true"][data-tab]',  # Any data-tab
                'div[contenteditable="true"]',  # Generic fallback
                '[data-testid="compose-btn"]',  # Compose button area
                'div[aria-label*="Message"]',  # Any element with Message in aria-label
                'div[placeholder*="Type"]',  # Placeholder text
                'div[class*="compose"]',  # Class-based
                'div[class*="input"]',  # Input class
                'textarea',  # Textarea elements
                'input[type="text"]'  # Text inputs
            ]
            
            message_box = None
            
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        # Make sure it's the message input (bottom half of page, visible)
                        if elem.location['y'] > 200 and elem.is_displayed() and elem.is_enabled():
                            message_box = elem
                            logger.info(f"Found message input using {selector}")
                            break
                    if message_box:
                        break
                except Exception:
                    continue
            
            if not message_box:
                logger.error("Could not find message input box")
                # Debug: print page source if input not found
                try:
                    page_source = self.driver.page_source
                    with open("logs/page_source.html", "w") as f:
                        f.write(page_source)
                    logger.debug("Saved page source to logs/page_source.html for debugging")
                except Exception as e:
                    logger.error(f"Failed to save page source: {e}")
                return False
            
            message_box.click()
            time.sleep(0.3)
            message_box.clear()
            message_box.send_keys(message)
            time.sleep(0.5)
            message_box.send_keys(Keys.RETURN)
            time.sleep(1)
            
            # Keep connection open for 2 extra seconds to ensure message sends
            time.sleep(2)
            
            logger.info(f"Message sent: {message[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def get_recent_messages(self, limit: int = 10) -> List[WhatsAppMessage]:
        """Get recent messages from current chat."""
        try:
            # Try multiple selectors for message containers
            message_selectors = [
                '[data-testid="msg-container"]',  # Original
                'div[class*="message"]',  # Class-based
                'div[data-id]',  # Data-id based
                'div[class*="copyable-text"]',  # Copyable text
                'div[role="row"]',  # Role-based
                'span.selectable-text'  # Direct text spans
            ]
            
            message_elements = []
            working_selector = None
            
            for selector in message_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        message_elements = elements
                        working_selector = selector
                        logger.info(f"Found {len(elements)} message elements using {selector}")
                        break
                except Exception:
                    continue
            
            if not message_elements:
                logger.error("No message elements found with any selector")
                return []
            
            messages = []
            chat_name = self._get_current_chat_name()
            
            for elem in message_elements[-limit:]:
                try:
                    # Try to get text content
                    content = ""
                    text_selectors = ['span.selectable-text', 'span', 'div']
                    
                    for text_sel in text_selectors:
                        try:
                            content_elem = elem.find_element(By.CSS_SELECTOR, text_sel)
                            content = content_elem.text.strip()
                            if content:
                                break
                        except:
                            continue
                    
                    # If no content found, try getting text directly
                    if not content:
                        content = elem.text.strip()
                    
                    if not content or len(content) < 2:
                        continue
                    
                    # Determine if outgoing - try multiple ways
                    is_outgoing = False
                    try:
                        elem_class = elem.get_attribute("class") or ""
                        parent_class = elem.find_element(By.XPATH, './..').get_attribute("class") or ""
                        
                        if "message-out" in elem_class or "message-out" in parent_class:
                            is_outgoing = True
                        elif "message-in" in elem_class or "message-in" in parent_class:
                            is_outgoing = False
                        else:
                            # Position-based detection as fallback
                            location = elem.location
                            window_width = self.driver.get_window_size()['width']
                            is_outgoing = (location['x'] + elem.size['width']) > (window_width * 0.6)
                    except:
                        pass
                    
                    # Determine sender properly in group chats
                    sender = "You" if is_outgoing else chat_name
                    if not is_outgoing:
                        # Look for a span/div with data-pre-plain-text just before or inside elem
                        meta_elem = None
                        try:
                            meta_elem = elem.find_element(By.XPATH, './preceding-sibling::*[@data-pre-plain-text][1]')
                        except Exception:
                            try:
                                meta_elem = elem.find_element(By.XPATH, './/*[@data-pre-plain-text]')
                            except Exception:
                                meta_elem = None
                        if meta_elem:
                            pre_plain = meta_elem.get_attribute('data-pre-plain-text') or ''
                            if ']' in pre_plain and ':' in pre_plain:
                                try:
                                    sender_candidate = pre_plain.split(']')[1].split(':')[0].strip()
                                    if sender_candidate:
                                        sender = sender_candidate
                                except Exception:
                                    pass
                    
                    message = WhatsAppMessage(
                        sender=sender,
                        content=content,
                        timestamp=datetime.now(),
                        is_outgoing=is_outgoing,
                        chat_name=chat_name
                    )
                    
                    messages.append(message)
                    
                except Exception:
                    continue
            
            logger.info(f"Successfully retrieved {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return []
    
    def _get_current_chat_name(self) -> str:
        """Get current chat name."""
        try:
            title_elem = self.driver.find_element(By.CSS_SELECTOR, 'header span[title]')
            return title_elem.get_attribute('title') or title_elem.text
        except:
            return "Unknown Chat"
    
    async def start_monitoring(self):
        """Start monitoring for auto-reply."""
        logger.info("Starting message monitoring...")
        
        while True:
            try:
                messages = self.get_recent_messages(5)
                
                for message in messages:
                    await self._process_message(message)
                
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _process_message(self, message: WhatsAppMessage):
        """Process message for auto-reply."""
        message_id = f"{message.chat_name}_{message.content}_{message.timestamp.isoformat()}"
        
        if message_id not in self.processed_messages and not message.is_outgoing:
            self.processed_messages.add(message_id)
            
            # Generate response
            response = await self.llm_manager.generate_whatsapp_response(
                message.content,
                message.sender,
                []  # Simplified - no conversation history
            )
            
            await asyncio.sleep(settings.response_delay_seconds)
            
            if self.send_message(response):
                logger.info(f"Auto-replied: {response[:50]}...")
    
    async def stop(self):
        """Stop automation and cleanup."""
        logger.info("Stopping automation...")
        if self.driver:
            self.driver.quit()
            self.driver = None


# Simple convenience functions
async def send_message_to_contact(contact_name: str, message: str, chat_type: str = "individual") -> bool:
    """Send message to a contact or group.
    
    Args:
        contact_name: Name/number of contact or group name
        message: Message to send
        chat_type: "individual" for direct messages, "group" for group chats
    """
    automation = WhatsAppAutomation()
    
    try:
        await automation.start()
        
        if automation.select_chat(contact_name, chat_type):
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


async def get_chat_messages(contact_name: str, limit: int = 10, chat_type: str = "individual") -> List[WhatsAppMessage]:
    """Get messages from a contact or group.
    
    Args:
        contact_name: Name/number of contact or group name
        limit: Number of messages to retrieve
        chat_type: "individual" for direct messages, "group" for group chats
    """
    automation = WhatsAppAutomation()
    
    try:
        await automation.start()
        
        if automation.select_chat(contact_name, chat_type):
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