import requests

API_KEY = ""  # Replace with your actual API key
API_URL = "https://api.perplexity.ai/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "sonar-pro",   # Use a valid model name as per Perplexity documentation
    "messages": [
        {"role": "user", "content": "Hello, are you working?"}
    ]
}

response = requests.post(API_URL, headers=headers, json=data)

print("Status Code:", response.status_code)
print("Response JSON:", response.json())
