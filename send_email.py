from decouple import config 
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from decouple import config
import os 



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
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
