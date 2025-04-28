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


# Defining the form states 
NAME, EMAIL, AMOUNT, ACCOUNT_NUM, ACCOUNT_NAME, BANK_NAME = range(6)

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
    return await finish_form(update, context)

def send_email_via_gmail(file_path):
    # Load environment variables
    sender_email = config("EMAIL_SENDER", default=None)
    sender_password = config("EMAIL_PASSWORD", default=None)
    receiver_email = config("EMAIL_RECEIVER", default=None)

    if not sender_email or not sender_password or not receiver_email:
        print("Error: Missing email environment variables. Check your .env file.")
        return False

    # Email content
    subject = "New Payment Application"
    body = "A new payment application has been received. Please find the attached file for more details."

    # Create the email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach the file
    try:
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(file_path)}",
            )
            msg.attach(part)
    except Exception as e:
        print(f"Error attaching file: {e}")
        return False

    # Send the email using Gmail SMTP
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:  # Use SMTP_SSL for port 465
            server.login(sender_email, sender_password)  # Log in using App Password
            server.send_message(msg)  # Send the email
            print("Email sent successfully!")
            return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

async def finish_form(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Save the last response
    context.user_data["method"] = update.message.text

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

        # Summarize data to show the user
        await update.message.reply_text(
            f"Thank you for your application. Here is the summary of your application:\n"
            f"Name: {context.user_data['name']}\n"
            f"Email: {context.user_data['email']}\n"
            f"Amount: ₦{context.user_data['amount']}\n"
            f"Account Number: {context.user_data['accountnumber']}\n"
            f"Account Name: {context.user_data['accountname']}\n"
            f"Bank Name: {context.user_data['bank_name']}\n"
            "Use /cancel to cancel the process. Use /form to fill the form again."
        )

        # Send the CSV file to the accountant
        if send_email_via_gmail(file_path):
            await update.message.reply_text("Your application has been submitted successfully, and the accountant has been notified.")
        else:
            await update.message.reply_text("Your application was saved, but there was an error notifying the accountant. Please contact support.")

    except Exception as e:
        await update.message.reply_text("An error occurred while saving your data. Please try again.")
        print(f"Error: {e}")

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
        },
        fallbacks=[CommandHandler('cancel', cancel)],
)

    application.add_handler(conv_handler)

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
