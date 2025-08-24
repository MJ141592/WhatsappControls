## WhatsApp Controls — Auto‑signup

Automate sign‑ups in Lypta WhatsApp groupchats by watching a numbered list and inserting your name automatically.

## Requirements
- Python 3.9+
- Google Chrome and a matching ChromeDriver

You will need to log onto WhatsappWeb on the first use, and potentially need to (rather quickly) click 'continue'.
Just retry if it closes before you've done that.

## Install
```bash
git clone https://github.com/MJ141592/WhatsappControls.git
cd WhatsappControls
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run auto‑signup
```bash
python auto_signup.py "Group Chat Name" --my-name "Your Name"
```
- The script polls the group. When it sees a numbered list like:
  1) Bob\n2) Alice\n3) \n...
  it inserts your name into the first empty slot, preserves any header/footer text, and sends the updated list.

## Notes
- The script uses a local `./whatsapp_profile` directory by default and will create it if missing. Log in to WhatsApp Web when Chrome opens the first time.
- ChromeDriver must be installed and compatible with your Chrome version (the code expects it at `/usr/bin/chromedriver`).

## Optional: .env configuration
You can store settings in a `.env` file at the repo root instead of passing flags:
```bash
# The display name to insert into signup lists, and as context for LLM generated messages
SIGNUP_MY_NAME=Your Name

# For LLM-powered replies in the scripts below
ANTHROPIC_API_KEY=...
```

## Other scripts for automatic LLM answers (optional, not required for Lypta signups)
This requires the Anthropic API key in the setup

- Live auto‑reply to new messages:
```bash
python live_reply.py "Chat Name"
```
- Reply to recent unanswered messages since your last message:
```bash
python reply_unanswered.py "Chat Name"
```