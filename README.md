# JOMApellBot

An AI-powered Telegram bot that provides ChatGPT-like conversational capabilities.

## Features

- 💬 Natural conversation with AI
- 🧠 Conversation memory (per user)
- 📝 Feedback system
- 🎯 Multiple commands for better UX
- 🔒 Secure environment variable management
- 🚀 Deployed on Railway

## Commands

- `/start` - Welcome message
- `/help` - Help and tips
- `/about` - About the project
- `/clear` - Clear conversation history
- `/feedback` - Send feedback
- `/cancel` - Cancel feedback

## Setup

1. Create a Telegram bot via @BotFather
2. Get your OpenAI API key
3. Clone this repository
4. Install dependencies: `pip install -r requirements.txt`
5. Create `.env` file with your tokens
6. Run: `python main.py`

## Deployment

Deploy to Railway by connecting your GitHub repository:
1. Push code to GitHub
2. Create new project on Railway
3. Connect to your repository
4. Add environment variables
5. Railway will auto-deploy

## Tech Stack

- Python 3.11+
- python-telegram-bot v20+
- OpenAI API
- Railway
- GitHub

## License

MIT
