from litellm import completion
import os

response = completion(
    model="openai/deepseek/deepseek-r1-0528-qwen3-8b",
    api_base="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
    messages=[
        {
            "role": "user",
            "content": "Say hello in one sentence."
        }
    ]
)

print(response.choices[0].message.content)