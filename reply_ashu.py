import asyncio, time
from whatsapp_automation import get_chat_messages, send_message_to_contact
from llm_client import LLMManager
from loguru import logger

async def main():
    messages = await get_chat_messages("Something", limit=20, chat_type="group")
    llm = LLMManager()
    for msg in messages:
        if msg.is_outgoing:
            continue
        if msg.sender.lower().startswith('+1') or 'ashu' in msg.sender.lower():
            logger.info(f"Replying to Ashu message: {msg.content}")
            response = await llm.generate_whatsapp_response(msg.content, msg.sender, [])
            await asyncio.sleep(2)  # brief pause
            success = await send_message_to_contact("Something", response, chat_type="group")
            if success:
                logger.info("Sent response.")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
