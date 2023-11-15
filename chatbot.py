import openai
import time
import requests
from bs4 import BeautifulSoup
import pdfkit

class Chatbot:
    def __init__(self):
        self.openai_api_key = "YOUR_OPENAI_API_KEY"  # replace with your OpenAI API key
        openai.api_key = self.openai_api_key

    def get_response(self, user_input):
        try:
            response = openai.Completion.create(
              engine="text-davinci-002",
              prompt=user_input,
              temperature=0.5,
              max_tokens=100
            )
            return response.choices[0].text.strip()
        except Exception as e:
            return str(e)

    def get_pdf(self, url):
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            pdfkit.from_file(soup, 'out.pdf')
            return "PDF created successfully"
        except Exception as e:
            return str(e)
