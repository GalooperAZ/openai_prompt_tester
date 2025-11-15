import time
from openai import OpenAI


def run_prompt(model: str, prompt: str, temperature: float = 0.7) -> dict:
    client = OpenAI()
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        elapsed = round(time.time() - start, 2)
        choice = response.choices[0].message.content.strip()
        usage = response.usage
        return {
            "model": model,
            "response": choice,
            "time_s": elapsed,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
        }
    except Exception as e:
        return {
            "model": model,
            "response": f"Error: {e}",
            "time_s": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
