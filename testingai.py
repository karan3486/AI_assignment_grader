import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Set your API key
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test the chat completion
def test_openai():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello world!"}
            ]
        )
        print("✅ OpenAI Response:", response.choices[0].message.content)
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    test_openai()
