import os
import logging
import asyncio
from typing import Dict, List
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate environment variables
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Store conversation history per user (optional - for memory)
user_conversations: Dict[int, List[Dict[str, str]]] = {}

# System prompt to define bot's personality
SYSTEM_PROMPT = """You are JOMApellBot, a helpful AI assistant created by JOMA Project. 
You are friendly, knowledgeable, and always ready to help users with their questions.
You provide clear, concise, and accurate information. 
If you don't know something, be honest about it.
Current date: {current_date}"""

# Conversation states for /feedback command
FEEDBACK_TEXT = 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when /start is issued."""
    user = update.effective_user
    welcome_message = f"""
👋 Hello {user.first_name}! Welcome to JOMApellBot!

I'm your AI assistant powered by advanced language models. You can chat with me about anything - I'm here to help!

💡 **What I can do:**
- Answer questions on any topic
- Help with research and learning
- Provide creative ideas
- Assist with writing and editing
- And much more!

🚀 **Commands:**
/start - Show this welcome message
/help - Get help and tips
/clear - Clear conversation history
/feedback - Send feedback about the bot
/about - Learn more about JOMApellBot

Just send me a message and let's chat! 😊
"""
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send helpful information when /help is issued."""
    help_text = """
🤖 **How to use JOMApellBot**

Simply send me any message and I'll respond like a friendly AI assistant!

**Tips for better conversations:**
1. **Be specific** - Clear questions get better answers
2. **Provide context** - If you're asking about something complex, give background info
3. **Ask follow-ups** - Feel free to ask clarifying questions
4. **Use /clear** - Reset the conversation if you want to start fresh

**Available Commands:**
/start - Welcome message and introduction
/help - Show this help message
/clear - Clear your conversation history
/feedback - Send feedback about the bot
/about - Learn more about the project

**Privacy Note:** Your conversations are processed by AI models. Don't share sensitive personal information.

Type anything to start chatting! 💬
"""
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send information about the bot project."""
    about_text = """
📚 **About JOMApellBot**

**Project:** JOMApellBot
**Developer:** JOMA Project Team
**Purpose:** To provide accessible AI assistance to everyone

**Features:**
- Powered by advanced AI (OpenAI GPT)
- 24/7 availability
- Natural conversation capabilities
- Secure and private
- Continuously improving

**Technology Stack:**
- Python 3.11+
- python-telegram-bot v20+
- OpenAI API
- Railway for hosting
- GitHub for version control

**Feedback:** Use /feedback to share your thoughts and help us improve!

Thank you for using JOMApellBot! 🌟
"""
    await update.message.reply_text(about_text, parse_mode="Markdown")


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the conversation history for the user."""
    user_id = update.effective_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
        await update.message.reply_text("🧹 Conversation history cleared! Starting fresh.")
    else:
        await update.message.reply_text("No conversation history to clear.")


async def feedback_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the feedback conversation."""
    await update.message.reply_text(
        "📝 Please send your feedback about JOMApellBot.\n\n"
        "What do you like? What could be improved? "
        "Send /cancel to cancel."
    )
    return FEEDBACK_TEXT


async def feedback_receive(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive and process the feedback."""
    feedback_text = update.message.text
    user = update.effective_user
    
    # Here you could save feedback to a database or send it to a channel
    # For now, we'll just acknowledge it
    logger.info(f"Feedback from {user.id} ({user.username}): {feedback_text}")
    
    await update.message.reply_text(
        "✅ Thank you for your feedback! It helps us make JOMApellBot better."
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the feedback conversation."""
    await update.message.reply_text("Feedback cancelled.")
    return ConversationHandler.END


async def get_ai_response(user_message: str, user_id: int = None) -> str:
    """Get a response from the AI model."""
    try:
        # Prepare messages for the AI
        messages = []
        
        # Add system prompt with current date
        system_msg = SYSTEM_PROMPT.format(
            current_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        messages.append({"role": "system", "content": system_msg})
        
        # Add conversation history if available
        if user_id and user_id in user_conversations:
            # Get last 10 messages for context (to stay within token limits)
            history = user_conversations[user_id][-10:]
            messages.extend(history)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI API
        response = await openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            presence_penalty=0.6,
            frequency_penalty=0.3,
        )
        
        ai_response = response.choices[0].message.content
        
        # Save to conversation history
        if user_id:
            if user_id not in user_conversations:
                user_conversations[user_id] = []
            user_conversations[user_id].append({"role": "user", "content": user_message})
            user_conversations[user_id].append({"role": "assistant", "content": ai_response})
            
            # Limit history to last 20 messages to prevent excessive token usage
            if len(user_conversations[user_id]) > 20:
                user_conversations[user_id] = user_conversations[user_id][-20:]
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error getting AI response: {e}")
        return "I'm having trouble processing your request right now. Please try again in a moment."


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle any text message (not commands) and respond with AI."""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Show typing indicator
    await update.message.chat.send_action(action="typing")
    
    # Get AI response
    ai_response = await get_ai_response(user_message, user_id)
    
    # Send response (split if too long)
    if len(ai_response) > 4096:
        for i in range(0, len(ai_response), 4096):
            await update.message.reply_text(ai_response[i:i+4096])
    else:
        await update.message.reply_text(ai_response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    
    # Send error message to user if possible
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ An error occurred while processing your request. "
            "Please try again later or use /feedback to report the issue."
        )


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # Feedback conversation handler
    feedback_conv = ConversationHandler(
        entry_points=[CommandHandler("feedback", feedback_start)],
        states={
            FEEDBACK_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_receive)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(feedback_conv)
    
    # Handle all text messages (but not commands)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    
    # Register error handler
    application.add_error_handler(error_handler)

    # Start the bot
    print("🤖 JOMApellBot is starting...")
    application.run_polling(
        poll_interval=0.5,
        timeout=30,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
