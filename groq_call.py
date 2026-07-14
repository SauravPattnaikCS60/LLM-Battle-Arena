import os
from dotenv import load_dotenv
from groq import Groq
from groq import APIConnectionError, APITimeoutError, RateLimitError,APIStatusError
import time

load_dotenv()

RETRY_EXCEPTIONS = (APITimeoutError, APIConnectionError, RateLimitError)
def call_groq_with_retry(max_retries = 5):
    def call_groq(function):
        def groq_api(*args, **kwargs):
            last_exc = None
            for retry in range(max_retries):
                try:
                    response = function(*args, **kwargs)
                    return response
                except RETRY_EXCEPTIONS as e:
                    last_exc = e
                    wait_time = min(2**retry, 30)
                    # logger.warning(f"Groq call failed due to {last_exc}. Retrying in {wait_time} seconds. Attempts : {retry+1}/{max_retries}")
                    time.sleep(wait_time)
            # logger.error(f"Groq call failed after {max_retries}. Error : {last_exc}")
            return ""
        return groq_api
    return call_groq

@call_groq_with_retry(max_retries=3)
def run_groq_api(prompt, model="openai/gpt-oss-120b"):

    client = Groq(
        api_key=os.environ.get("GROQ_API"),
    )

    if model.startswith('qwen'):
        chat_completion = client.chat.completions.create(
        messages=[
            {
                "role":"system",
                "content":"You are a helpful AI assistant who is tasked with answering user queries accurately. You must follow the instructions faithfully and do not hallucinate or perform tasks which are not asked."
            }
            ,
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
        reasoning_effort="none"
    )
    else:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role":"system",
                    "content":"You are a helpful AI assistant who is tasked with answering user queries accurately. You must follow the instructions faithfully and do not hallucinate or perform tasks which are not asked."
                }
                ,
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model,
        )

    response = chat_completion.choices[0].message.content
    return response