# WhatsApp Controls (slim)

Automates WhatsApp Web with Selenium and plugs into Anthropic to help reply to chats and maintain simple signup lists.

Important notes
- This codebase was largely vibe‑coded with supervision and subsequent edits. It currently has bugs and very messy code, but works for me using Anthropic's API for answering messages automatically, and automatically signing up for an event in a certain groupchat.

What’s included
- WhatsApp Web automation: open chat, read recent messages, send replies
- Auto‑reply loops: reply live to incoming messages with LLM context (last 30 msgs)
- Auto‑signup helper: watches a numbered list and adds your name when conditions are met
- Config via .env (Pydantic): Anthropic key, Chrome profile path, your signup display name

Quick start
1) Requirements
- Python 3.9+
- Google Chrome + matching ChromeDriver

2) Install
```bash
git clone https://github.com/MJ141592/WhatsappControls.git
cd WhatsappControls
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3) Configure
Create .env in the repo root:
```bash
ANTHROPIC_API_KEY=...

# WhatsApp session (Chrome user data dir) — reuse a logged‑in profile
CHROME_PROFILE_PATH=/home/you/chrome_profile

# Name to add to signup lists
SIGNUP_MY_NAME=Your Name

# LLM config
ANTHROPIC_MODEL=claude-3-sonnet-20240229
MAX_TOKENS=1000
TEMPERATURE=0.7
```

4) Run
- Auto‑signup in a group (watches for lists and inserts your name):
```bash
python auto_signup.py "Group Chat Name"
```
- Live auto‑reply for a chat (uses last 30 messages as context):
```bash
python live_reply.py "Chat Name"
```
- Reply to unanswered messages since your last message:
```bash
python reply_unanswered.py "Chat Name"
```

How it works (high level)
- Selenium drives Chrome to WhatsApp Web with your existing logged‑in profile.
- Message reads try to preserve emojis by parsing innerHTML and replacing <img alt> emoji.
- Sending avoids slow key‑by‑key typing: it inserts the whole message quickly and clicks send.
- LLM calls are wrapped via `LLMManager`; we pass a short conversation history for context.

Tips
- Use a persistent Chrome profile dir so you don’t have to re‑scan the QR each run.
- For always‑on usage, run on a small Linux VM with a systemd service.
- If you need to handle multiple chats sequentially:
```bash
python auto_signup.py "A" && python auto_signup.py "B"
```

Project layout
- `whatsapp_automation.py`  Core automation and helpers
- `llm_client.py`           Anthropic client and manager
- `auto_signup.py`          CLI wrapper for the auto‑signup loop
- `live_reply.py`           CLI for continuous auto‑reply
- `reply_unanswered.py`     CLI to reply to recent unanswered messages
- `config.py`               Pydantic settings (.env → Settings)

License / Disclaimer
- Educational use only. You are responsible for complying with WhatsApp’s ToS.
- No warranties. This is pragmatic automation code; expect occasional rough edges. 