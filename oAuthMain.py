import streamlit as st
from auth import get_login_str, display_user, fetch_spam_emails, fetch_latest_emails, get_email_summary
import asyncio  
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def generate_word_cloud(emails):
    text = ' '.join(email['snippet'] for email in emails)
    wordcloud = WordCloud(width=800, height=400, max_words=50).generate(text)
    return wordcloud

async def get_emails_and_generate_wordcloud(token):
    emails = await fetch_emails(token, 'Spam', 30)  
    if emails:
        wordcloud = generate_word_cloud(emails[:30])  
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        return fig
    else:
        return None


def main():
    st.title("CPSC Final GmailAPI Streamlit ")
    st.write(get_login_str(), unsafe_allow_html=True)
    
    if st.button("Display User"):
        display_user()
    
    st.sidebar.title("Options")
    if st.sidebar.button("Generate Spam Emails Word Cloud"):
        token = st.session_state.get('token', None)
        if token:
            with st.spinner('Fetching spam emails...'):
                fig = asyncio.run(get_emails_and_generate_wordcloud(token))  
                if fig:
                    st.write(fig)
                else:
                    st.error("No emails found in spam.")
        else:
            st.error("You need to log in first.")

    if st.sidebar.button("Show Latest 10 Emails Summaries"):
        token = st.session_state.get('token', None)
        if token:
            with st.spinner('Fetching your latest emails...'):
                latest_emails = asyncio.run(fetch_emails(token, 'Inbox', 10))
                if latest_emails and not isinstance(latest_emails, str):
                    summaries = get_email_summary(latest_emails[:5])  
                    st.write("Email Summaries:", summaries)
                else:
                    st.error("Failed to fetch emails or no emails found.")
        else:
            st.error("You need to log in first.")
    return
    
if __name__ == '__main__':
    main()
        
  
