from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from decouple import config
import csv

# Defining the form states 
NAME, EMAIL, AMOUNT, METHOD = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, Welcome to the payment bot!\n Please enter /form to begin the application process.')

async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please enter your name:')
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("PLease enter your email")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Please enter the payment amount")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    await update.message.reply_text("Please enter the payment method")
    return METHOD

async def get_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["method"] = update.message.text

    # Summarization of data to show the user
    await update.message.reply_text(
        f"Thank you for your application. Here is the summary of your application:\n"
        f"Name: {context.user_data['name']}\n"
        f"Email: {context.user_data['email']}\n"
        f"Amount: ₦{context.user_data['amount']}\n"
        f"Method: {context.user_data['method']}\n"
        "Use /form to fill the form again"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Application canceled. Use /form to fill the form again.")
    return ConversationHandler.END

def main():
    # Get the token from your environment or .env file
    TOKEN = config("TOKEN", default=None)
    if not TOKEN:
        print("Error: Bot token not found. Make sure you set TOKEN in your environment.")
        return

    # Create an application instance
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler('start', start))

    # conversation handler for the form 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('form', start_form)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            METHOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_method)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
)

    application.add_handler(conv_handler)

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
