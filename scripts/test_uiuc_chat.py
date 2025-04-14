import requests

API_URL = "https://uiuc.chat/api/chat-api/chat"
API_KEY = "uc_0a6c6e31ac654737a3cd4d5c1ad4e4cd"  # Replace with your actual key

title = "Bias-Aware Agent: Enhancing Fairness in AI-Driven Knowledge Retrieval"
abstract = "Advancements in retrieving accessible information have evolved more rapidly over the last few years... (omitting for brevity) ... by empowering users with transparency and awareness, this approach aims to foster more equitable information systems."
'''
headers = {
    'Content-Type': 'application/json'
}
messages = [
    {
        "role": "system",
        # 可以空着，或写很简短
        "content": "You are a helpful assistant."
    },
    {
        "role": "user",
        "content": (
            "Here is a paper's title and abstract:\n\n"
            f"Title: {title}\n\n"
            f"Abstract: {abstract}\n\n"
            "Respond with '1' (just the digit) if this paper is clearly about both "
            "large language models (or generative text models) AND about bias/fairness. "
            "Otherwise respond '0'. No explanation, no punctuation, only the digit."
        )
    }
]

data = {
    "model": "llama3.1:8b-instruct-fp16",
    "messages": messages,
    "api_key": API_KEY,
    "course_name": "llm-bias-papers",
    "stream": False,
    "temperature": 0.1
}
'''
url = "https://uiuc.chat/api/chat-api/chat"
headers = {
  'Content-Type': 'application/json'
}
data = {
  "model": "llama3.1:8b-instruct-fp16",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful AI assistant. Follow instructions carefully."
    },
    {
      "role": "user",
      "content": "Here is a paper's title and abstract:\n\nTitle:" + title + "\n\nAbstract: " + abstract + "\n\nRespond with 'Yes' (just the word) if this paper is clearly about both large language models (or generative text models) AND about bias/fairness. Otherwise respond 'No'. No explanation, no punctuation, only the digit."
    }
  ],
  "api_key": "uc_0a6c6e31ac654737a3cd4d5c1ad4e4cd",
  "course_name": "llm-bias-papers",
  "stream": False,
  "temperature": 0.0,
  "retrieval_only": False
}

response = requests.post(url, headers=headers, json=data)
for chunk in response.iter_lines():
    if chunk:
        print(chunk.decode())
resp = requests.post(API_URL, headers=headers, json=data)
print("Status:", resp.status_code)
print("Response:", resp.text)
print("[DEBUG] resp.text =", resp.text)
print("[DEBUG] resp.json() =", resp.json())  # if not raising error
