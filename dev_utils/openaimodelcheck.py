from dotenv import load_dotenv
import os

load_dotenv()

from openai import OpenAI

apiKey = os.getenv("OPENAI_API_KEY")
baseUrl = os.getenv("OPENAI_BASE_URL") or None
clientOptions = {"api_key": apiKey}
if baseUrl:
    clientOptions["base_url"] = baseUrl
else:
    os.environ.pop("OPENAI_BASE_URL", None)

clientOptions["max_retries"] = 0
client = OpenAI(**clientOptions)
for m in client.models.list():
    print(m.id)