import os
import base64 #Encodes email into safe format for sending via Gmail API
import textwrap #Helps format long text (like transcripts)
from datetime import datetime
from email.mime.text import MIMEText #Creates email body (plain text) this is from gmail api
from email.mime.multipart import MIMEMultipart #Builds full email (subject + body + attachments)
from google.auth.transport.requests import Request #Refresh expired login tokens
from google.oauth2.credentials import Credentials #Stores your login credentials
from google_auth_oauthlib.flow import InstalledAppFlow #Handles OAuth login (Google sign-in popup)
from googleapiclient.discovery import build #Creates a connection to Gmail API

#Login → store token → refresh when needed

# Set API keys via environment variable placeholders for GitHub safety
os.environ["GOOGLE_API_KEY"] = "YOUR_GOOGLE_API_KEY"

# Email settings
EMAIL_SENDER = "your_email@gmail.com"
EMAIL_RECIPIENT = "recipient_email@gmail.com"
SCOPES = ['https://www.googleapis.com/auth/gmail.send'] #what permission your app has

def send_email_notification(subject, summary, key_points, assignments):
    print("Function loaded")  # test

#UNCOMMENT THIS SECTION TO ENABLE GMAIL FUNCTIONALITY

# # Gmail API authentication
# #Google login + authentication for Gmail API.
# #It logs you into Gmail (via OAuth) and returns a Gmail API service object that can send emails.
# def authenticate_gmail_api():
#     creds = None #stores login info
#     #Check if user already logged in
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES) #if exits, load login info from file
#     if not creds or not creds.valid: #if no login info or expired, need to log in again
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request()) #Automatically refresh login
#         else:
#             #If no valid login → ask user to login (opens Google sign-in popup)
#             flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#             creds = flow.run_local_server(port=0) #safe way to handle OAuth callback
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json()) #save creds to file for next time
#     return build('gmail', 'v1', credentials=creds) #Creates connection to Gmail

# # Trim to first n words
# def get_first_n_words(text, n=100):
#     words = text.split()
#     return ' '.join(words[:n])

# # Send summary via Gmail API
# #It takes AI output (summary + key points) and sends it as an email using Gmail API
# def send_email_notification(subject, summary, key_points, assignments):
#     service = authenticate_gmail_api() #Logs into Gmail and returns a service object

#     message = MIMEMultipart() #create email container
#     message['To'] = EMAIL_RECIPIENT
#     message['From'] = EMAIL_SENDER
#     message['Subject'] = subject

#     #Create email body
#     email_body = f"""
#     Upcoming Assignment Notification

#     Summary:{summary}

#     Key Concepts:{key_points}

#     Assignments:{assignments}
#     """

#     #Attach body to email
#     message.attach(MIMEText(email_body, 'plain'))

#     # Converts email into safe format for sending via Gmail API (base64 encoding)
#     raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

#     #Prepare API payload
#     payload = {'raw': raw}

#     try:
#         #Sends email through Gmail
#         service.users().messages().send(userId='me', body=payload).execute()
#         return "Email sent successfully via Gmail API"
#     except Exception as e:
#         return f"Failed to send email: {e}"
