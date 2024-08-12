# IMPORTING LIBRARIES
from numpy import void
import streamlit as st
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from openai import OpenAI

CLIENT_ID = st.secrets["CLIENT_ID"]
CLIENT_SECRET = st.secrets["CLIENT_SECRET"]
REDIRECT_URI = st.secrets["REDIRECT_URI"]
api_key = st.secrets["OPENAI_API_KEY"]

def create_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key is None:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    client = OpenAI(api_key=api_key)
    return client


async def get_authorization_url(client: GoogleOAuth2, redirect_uri: str):
    authorization_url = await client.get_authorization_url(redirect_uri, scope=["profile", "email", "https://www.googleapis.com/auth/gmail.readonly"])
    return authorization_url

async def get_access_token(client: GoogleOAuth2, redirect_uri: str, code: str):
    token = await client.get_access_token(code, redirect_uri)
    return token

async def get_email(client: GoogleOAuth2, token: str):
    user_id, user_email = await client.get_id_email(token)
    return user_id, user_email

async def fetch_spam_emails(token: str):
    credentials = Credentials(token)
    service = build('gmail', 'v1', credentials=credentials)
    results = service.users().messages().list(userId='me', labelIds=['SPAM'], maxResults=30).execute()
    messages = results.get('messages', [])
    if not messages:
        return "No messages in the spam folder."
    else:
        emails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = {
                'id': msg['id'],
                'snippet': msg['snippet']
            }
            emails.append(email_data)
        return emails

async def fetch_latest_emails(token: str):
    credentials = Credentials(token)
    service = build('gmail', 'v1', credentials=credentials)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=10).execute()
    messages = results.get('messages', [])
    if not messages:
        return "No new messages."
    else:
        emails = []
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = {
                'id': msg['id'],
                'snippet': msg['snippet']
            }
            emails.append(email_data)
        return emails

def get_login_str():
    client: GoogleOAuth2 = GoogleOAuth2(CLIENT_ID, CLIENT_SECRET)  # 创建GoogleOAuth2实例
    authorization_url = asyncio.run(
        get_authorization_url(client, REDIRECT_URI))  # 异步获取授权URL
    return f'''<a target = "_self" href = "{authorization_url}">Google login</a>'''  # 返回一个HTML链接

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def get_email_summary(emails):
    client = create_openai_client()
    summaries = []
    for email in emails:
        email_content = email['snippet']
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": f"Summarize this email: {email_content}"}],
                max_tokens=50
            )
            
            summary = response.choices[0].message.content  
            summaries.append(summary)
        except Exception as e:
            summaries.append(f"An error occurred: {e}")
    return summaries



def display_user() -> void:
    client: GoogleOAuth2 = GoogleOAuth2(CLIENT_ID, CLIENT_SECRET)
    code = st.experimental_get_query_params()['code']
    token = asyncio.run(get_access_token(
        client, REDIRECT_URI, code))
    user_id, user_email = asyncio.run(
        get_email(client, token['access_token']))
    st.write(
        f"You're logged in as {user_email} and id is {user_id}")
    st.session_state['token'] = token['access_token']  # Storing the token in session_state
    spam_emails = asyncio.run(fetch_spam_emails(token['access_token']))
    st.write("Spam Emails: ", spam_emails)

