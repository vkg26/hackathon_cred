import os
import openai

# Get credentials from environment variables
api_key = os.getenv("LITELLM_API_KEY")
api_base = os.getenv("OPENAI_API_BASE") 

client = openai.OpenAI(
    api_key=api_key,
    base_url=api_base
)