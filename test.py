import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

envPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(dotenv_path=envPath)
client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(api_version='v1alpha')
                    )
prompt = "Hi are u working plz reply."
response = client.models.generate_content(
	model="gemini-3.6-flash",
	contents=prompt,
)
print(response.text)
