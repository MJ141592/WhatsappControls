# WhatsApp Automation Tool 🚀

A powerful Python tool for automating WhatsApp Web interactions with LLM-powered intelligent responses using OpenAI or Anthropic APIs.

## Features

- 🤖 **LLM Integration**: Support for both OpenAI GPT and Anthropic Claude models
- 📱 **WhatsApp Web Automation**: Automated message sending and receiving via Selenium
- 🔄 **Auto-Reply**: Intelligent automatic responses to incoming messages
- 📊 **Message Analysis**: Intent detection and sentiment analysis
- 🎯 **Targeted Messaging**: Send messages to specific contacts
- 📈 **Rate Limiting**: Built-in protection against spam
- 🔍 **Message Monitoring**: Real-time chat monitoring and logging
- ⚙️ **Configurable**: Extensive configuration options via environment variables

## Installation

1. **Clone the repository** (see instructions below for creating private repo)

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

4. **Install Chrome browser** (required for WhatsApp Web automation)

## Configuration

Edit the `.env` file with your settings:

```bash
# Required: At least one LLM API key
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# WhatsApp settings
WHATSAPP_PHONE_NUMBER=your_phone_number_here
CHROME_PROFILE_PATH=path_to_your_chrome_profile  # Optional

# LLM Configuration
DEFAULT_LLM_PROVIDER=openai  # or anthropic
OPENAI_MODEL=gpt-4-turbo-preview
TEMPERATURE=0.7

# Automation settings
AUTO_REPLY_ENABLED=false
RESPONSE_DELAY_SECONDS=2
MAX_MESSAGES_PER_HOUR=50
```

## Usage

### Quick Setup
```bash
python main.py setup
```

### Start Automation Service
```bash
# Start with monitoring only
python main.py start

# Start with auto-reply enabled
python main.py start --auto-reply

# Monitor only mode
python main.py start --monitor-only
```

### Send Messages
```bash
# Send a message to a contact
python main.py send "John Doe" "Hello, how are you?"
```

### Get Messages
```bash
# Get recent messages from a contact
python main.py get-messages "John Doe" --limit 5
```

### Test LLM Integration
```bash
# Test with default provider
python main.py test-llm "How's the weather today?"

# Test with specific provider
python main.py test-llm "Hello there" --provider anthropic
```

### View Configuration
```bash
python main.py config
```

## Project Structure

```
WhatsappControls/
├── main.py                 # CLI entry point
├── whatsapp_automation.py  # WhatsApp Web automation
├── llm_client.py          # LLM API integration
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── logs/                 # Log files (created automatically)
```

## API Keys Setup

### OpenAI
1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add to `.env` as `OPENAI_API_KEY`

### Anthropic
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Add to `.env` as `ANTHROPIC_API_KEY`

## WhatsApp Web Setup

1. The tool will open Chrome and navigate to WhatsApp Web
2. Scan the QR code with your phone (first time only)
3. The session will be saved for future use

## Safety Features

- Rate limiting to prevent spam
- Message intent analysis before auto-reply
- Configurable response delays
- Comprehensive logging
- Safe message parsing

## Troubleshooting

### Common Issues

1. **Chrome driver issues**:
   - Ensure Chrome browser is installed
   - The tool auto-downloads the correct ChromeDriver

2. **WhatsApp Web login**:
   - Make sure WhatsApp is active on your phone
   - Check your internet connection
   - Try clearing browser cache

3. **API errors**:
   - Verify your API keys are correct
   - Check your API usage limits
   - Ensure you have sufficient credits

### Logs

Check the `logs/` directory for detailed error information:
```bash
tail -f logs/whatsapp_automation.log
```

## Development

### Running Tests
```bash
# Test LLM integration
python main.py test-llm "Test message"

# Test configuration
python main.py config
```

### Adding Features

The codebase is modular and extensible:
- Add new LLM providers in `llm_client.py`
- Extend WhatsApp functionality in `whatsapp_automation.py`
- Add new CLI commands in `main.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational and personal use. Please respect WhatsApp's Terms of Service and use responsibly.

## Disclaimer

This tool automates WhatsApp Web through browser automation. Use it responsibly and in compliance with WhatsApp's Terms of Service. The authors are not responsible for any misuse or violations.

---

## Creating a Private GitHub Repository

To turn this into a private GitHub repository on your account:

### Option 1: Using GitHub Web Interface

1. **Go to GitHub**: Visit [github.com](https://github.com) and sign in
2. **Create New Repository**: Click the "+" icon in the top right, then "New repository"
3. **Repository Settings**:
   - Repository name: `WhatsappControls` (or your preferred name)
   - Description: "WhatsApp automation tool with LLM integration"
   - Set to **Private**
   - Don't initialize with README, .gitignore, or license (we already have these)
4. **Click "Create repository"**

### Option 2: Using GitHub CLI (if installed)

```bash
# Install GitHub CLI if you haven't already
# https://cli.github.com/

# Create private repository
gh repo create WhatsappControls --private --description "WhatsApp automation tool with LLM integration"
```

### Initialize Git and Push

After creating the repository on GitHub:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Make initial commit
git commit -m "Initial commit: WhatsApp automation tool with LLM integration"

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/WhatsappControls.git

# Push to GitHub
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Setting up SSH (Recommended)

For easier future pushes without entering passwords:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add SSH key to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub
```

Then add this SSH key to your GitHub account in Settings > SSH and GPG keys.

After setting up SSH, change your remote URL:
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/WhatsappControls.git
```

Your private repository is now ready! 🎉 