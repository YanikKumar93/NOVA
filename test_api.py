print("TEST STARTED")

import os
from dotenv import load_dotenv

print("Imports successful")

load_dotenv()

print("API key loaded:", bool(os.getenv("OPENAI_API_KEY")))
print("Base URL:", os.getenv("OPENAI_BASE_URL"))
print("Model:", os.getenv("NOVA_MODEL"))

print("TEST FINISHED")