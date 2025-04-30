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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from decouple import config
import os 
import send_email


# Defining the form states 
NAME, EMAIL, AMOUNT, ACCOUNT_NUM, ACCOUNT_NAME, BANK_NAME, CONFIRM = range(7)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello, Welcome to the payment bot!\n Please enter /form to begin the application process.')

async def start_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Please enter your name:')
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Please enter your email")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Please enter the payment amount")
    return AMOUNT

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    await update.message.reply_text("Please enter account number")
    return ACCOUNT_NUM

async def get_account_num(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accountnumber"] = update.message.text
    await update.message.reply_text("Please enter your account name")
    return ACCOUNT_NAME
async def get_account_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accountname"] = update.message.text
    await update.message.reply_text("Please enter your bank name")
    return BANK_NAME
 
async def get_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["bank_name"] = update.message.text
    
    await update.message.reply_text(
        f"Please confirm your application details:\n\n"
        f"Name: {context.user_data['name']}\n"
        f"Email: {context.user_data['email']}\n"        
        f"Amount: {context.user_data['amount']}\n"
        f"Account Number: {context.user_data['accountnumber']}\n"
        f"Account Name: {context.user_data['accountname']}\n"
        f"Bank Name: {context.user_data['bank_name']}\n\n"
        f"Review the details and reply with 'Yes' to confirm or 'No' to cancel."

    )
    return CONFIRM

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save the last response
    user_reply = update.message.text.lower()

    if user_reply == "yes":
        # Save the data to a CSV file
        file_path = "payment_data.csv"

        # Prepare the user data  
        user_data = {
            "Name": context.user_data["name"],
            "Email": context.user_data["email"],
            "Amount": context.user_data["amount"],
            "Account Number": context.user_data["accountnumber"],
            "Account Name": context.user_data["accountname"],
            "Bank Name": context.user_data["bank_name"],
        }

        # Write the data to the CSV file
        try:
            file_exists = os.path.isfile(file_path)

            with open(file_path, "a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=user_data.keys())

                # Write header if the file is new
                if not file_exists:
                    writer.writeheader()

                writer.writerow(user_data)

            # Summarize data to show the user and ask for confirmation
            await update.message.reply_text(
                f"Thank you for your application. Here is the summary of your application:\n\n"
                f"**Name:** {context.user_data['name']}\n"
                f"**Email**: {context.user_data['email']}\n"
                f"**Amount**: ₦{context.user_data['amount']}\n"
                f"**Account Number**: {context.user_data['accountnumber']}\n"
                f"**Account Name**: {context.user_data['accountname']}\n"
                f"**Bank Name**: {context.user_data['bank_name']}\n"
            )

        # Send the CSV file to the accountant
            if send_email.send_email_via_gmail(file_path):
                await update.message.reply_text("Your application has been submitted successfully, and the accountant has been notified.")
            else:
                await update.message.reply_text("Your application was saved, but there was an error notifying the accountant. Please contact support.")

        except Exception as e:
            await update.message.reply_text("An error occurred while saving your data. Please try again.")
            print(f"Error: {e}")

    elif user_reply == "no":
        await update.message.reply_text("Application canceled. Use /form to fill the form again.")
    else:
        await update.message.reply_text("Invalid response. Please reply with 'Yes' or 'No'.")
        return CONFIRM

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
            ACCOUNT_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_account_num)],
            ACCOUNT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_account_name)],
            BANK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bank_name)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_form)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
)

    application.add_handler(conv_handler)

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
