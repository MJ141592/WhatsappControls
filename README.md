## WhatsApp Controls — Auto‑signup

Automate sign‑ups in a WhatsApp group by watching a numbered list and inserting your name automatically.

## Requirements
- Python 3.9+
- Google Chrome and a matching ChromeDriver (ensure Chrome is logged in with WhatsApp Web)

## Install
```bash
git clone https://github.com/MJ141592/WhatsappControls.git
cd WhatsappControls
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure (.env)
```bash
# Reuse an existing Chrome user data dir that is already logged into WhatsApp Web
CHROME_PROFILE_PATH=/home/you/chrome_profile

# The display name to insert into signup lists
SIGNUP_MY_NAME=Your Name
```

## Run auto‑signup
```bash
python auto_signup.py "Group Chat Name"
```
- The script polls the group. When it sees a numbered list like:
  1) Bob\n2) Alice\n3) \n...
  it inserts `SIGNUP_MY_NAME` into the first empty slot, preserves any header/footer text, and sends the updated list.

### Options
- Poll interval seconds (default 1):
```bash
python auto_signup.py "Group Chat Name" --interval 1
```
- Override the name without editing .env:
```bash
python auto_signup.py "Group Chat Name" --my-name "Different Name"
```

## Notes
- Ensure your Chrome profile path is correct and already logged into WhatsApp Web.
- ChromeDriver must be installed and compatible with your Chrome version (the code expects it at `/usr/bin/chromedriver`).

## Other scripts for automatic LLM answers (optional, not required for Lypta signups)
If you want automatic, brief LLM replies (for the scripts below), add this to `.env`:
```bash
# Anthropic API key
ANTHROPIC_API_KEY=...
```

- Live auto‑reply to new messages:
```bash
python live_reply.py "Chat Name"
```
- Reply to recent unanswered messages since your last message:
```bash
python reply_unanswered.py "Chat Name"
```