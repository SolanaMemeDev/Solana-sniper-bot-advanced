'''
i run a local server with deepseek-r1, below is how to call it from your code

the deepseek-r1 model is available free while Solana Dev is streaming: https://www.youtube.com/@moondevonyt 
'''

from openai import OpenAI

# Easy to modify prompt at the top
PROMPT = """

build me a volume spike backtest in python
"""

# Easy to modify IP at the top
# this changes daily, get inside discord to know when it changes: https://algotradecamp.com
# check the free api keys section of the discord
LAMBDA_IP = "192.222.57.184"  # Just update this when you start a new instance

if __name__ == '__main__':
    # Initialize the client with your local server
    client = OpenAI(
        api_key="not-needed",
        base_url=f"http://{LAMBDA_IP}:8000/v1"
    )

    # Make a chat completion request
    response = client.chat.completions.create(
        model="deepseek-r1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": PROMPT},
        ],
        stream=False
    )

    print(f"🌙 MoonDev's DeepSeek Response:")
    print(f"🤖 Prompt: {PROMPT}")
    print(f"✨ Response: {response.choices[0].message.content}")