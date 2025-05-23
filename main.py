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
import pandas as pd


# Defining the form states 
NAME, EMAIL, REASON, AMOUNT, ACCOUNT_NUM, ACCOUNT_NAME, BANK_NAME, CONFIRM = range(8)

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
    await update.message.reply_text("Please enter your reason for payment")
    return REASON

async def get_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["reason"] = update.message.text
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
        f"Reason: {context.user_data['reason']}\n"
        f"Amount: ₦{context.user_data['amount']}\n"
        f"Account Number: {context.user_data['accountnumber']}\n"
        f"Account Name: {context.user_data['accountname']}\n"
        f"Bank Name: {context.user_data['bank_name']}\n\n"
        f"Review the details and reply with 'Yes' to confirm or 'No' to cancel."

    )
    return CONFIRM

import pandas as pd

def csv_to_excel(csv_file, excel_file):
    try:
        df = pd.read_csv(csv_file)
        df.to_excel(excel_file, index=False)
        print(f"Converted {csv_file} to {excel_file}")
        return True
    except FileNotFoundError:
        print(f"Error: {csv_file} not found")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_reply = update.message.text.lower()

    if user_reply == "yes":
        # File paths
        csv_file_path = "payment_data.csv"
        excel_file_path = "payment_data.xlsx"

        # Prepare the user data  
        user_data = {
            "Name": context.user_data["name"],
            "Email": context.user_data["email"],
            "Reason": context.user_data["reason"],
            "Amount": context.user_data["amount"],
            "Account Number": context.user_data["accountnumber"],
            "Account Name": context.user_data["accountname"],
            "Bank Name": context.user_data["bank_name"],
        }

        # Write the data to the CSV file
        try:
            file_exists = os.path.isfile(csv_file_path)

            with open(csv_file_path, "a", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(file, fieldnames=user_data.keys())

                # Write header if the file is new
                if not file_exists:
                    writer.writeheader()

                writer.writerow(user_data)

            # Convert CSV to Excel
            if csv_to_excel(csv_file_path, excel_file_path):
                # Send the Excel file to the accountant
                if send_email.send_email_via_gmail(excel_file_path):
                    await update.message.reply_text(
                        "Your application has been submitted successfully, and the accountant has been notified."
                    )
                else:
                    await update.message.reply_text(
                        "Your application was saved, but there was an error notifying the accountant. Please contact support."
                    )
            else:
                await update.message.reply_text(
                    "Your application was saved, but there was an error generating the Excel file. Please contact support."
                )

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

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the Payment Bot!\n\n"
        "Here are the available commands:\n"
        "/start - Start the bot and get a greeting message.\n"
        "/form - Begin the payment application process.\n"
        "/cancel - Cancel the current operation.\n"
        "Feel free to use any of these commands to interact with the bot!"
    )

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
    application.add_handler(CommandHandler('welcome', welcome))  # Add the welcome command

    # conversation handler for the form 
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('form', start_form)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reason)],
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
