import requests
from dotenv import load_dotenv
import os

load_dotenv()

url = "https://www.googleapis.com/customsearch/v1"
params = {
    "key": os.getenv("GOOGLE_API_KEY",) ,
    "cx": os.getenv("GOOGLE_CX"),
    "q": "Model Context Protocol MCP"
}

response = requests.get(url, params=params)
print(response.json())
