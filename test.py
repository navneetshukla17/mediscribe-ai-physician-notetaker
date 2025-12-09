import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

model = genai.GenerativeModel('gemini-2.0-flash')
chat = model.start_chat()

response = chat.send_message("Hello")
print(f"Gemini: {response.text}")
