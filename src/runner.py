import time
from typing import Any, Dict, List, Tuple

from openai import OpenAI


# Konfiguracja trzech wariantów rozliczeniowych używanych sekwencyjnie
_BILLING_PLANS: List[Tuple[str, str]] = [
    # Uwaga: API nie akceptuje wartości "standard" ani "batch" dla `service_tier`.
    # Dozwolone wartości to: auto, default, flex, priority.
    # Dlatego mapujemy nazwy planów raportowych na faktyczne wartości API:
    # - STANDARD -> default
    # - FLEX     -> flex
    # - BATCH    -> priority (trzeci wariant rozliczeniowy w ramach service_tier; Batch API to osobny, asynchroniczny mechanizm)
    ("STANDARD", "default"),
    ("FLEX", "flex"),
    ("BATCH", "priority"),
]


def _run_single_plan(
    client: OpenAI,
    model: str,
    prompt: str,
    temperature: float,
    plan_name: str,
    service_tier: str,
) -> Dict[str, Any]:
    """
    Wykonuje pojedyncze wywołanie API dla danego planu rozliczeniowego.

    - Zachowuje identyczny prompt / model / temperature między planami.
    - Jawnie ustawia parametr `service_tier`.
    - Błąd w tym planie nie przerywa wykonania kolejnych.
    """
    start = time.time()
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            service_tier=service_tier,
        )
        elapsed = round(time.time() - start, 2)
        choice = response.choices[0].message.content.strip()
        usage = response.usage

        return {
            "model": model,
            "response": choice,
            "time_s": elapsed,
            "prompt_tokens": getattr(usage, "prompt_tokens", None),
            "completion_tokens": getattr(usage, "completion_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
            "billing_plan": plan_name,
            "service_tier": service_tier,
            "status": "ok",
            "error_message": None,
        }
    except Exception as e:
        # Zwracamy błąd w strukturze wyniku, ale NIE przerywamy całej sekwencji planów.
        return {
            "model": model,
            "response": f"Error: {e}",
            "time_s": None,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "billing_plan": plan_name,
            "service_tier": service_tier,
            "status": "error",
            "error_message": str(e),
        }


def run_prompt(model: str, prompt: str, temperature: float = 0.7) -> List[Dict[str, Any]]:
    """
    Wykonuje to samo zapytanie (prompt, model, temperature) sekwencyjnie
    w trzech wariantach rozliczeniowych:
    - STANDARD  -> service_tier="default"
    - FLEX      -> service_tier="flex"
    - BATCH     -> service_tier="priority"

    Zwraca listę trzech wyników – po jednym dla każdego planu.
    """
    client = OpenAI()

    results: List[Dict[str, Any]] = []
    for plan_name, service_tier in _BILLING_PLANS:
        result = _run_single_plan(
            client=client,
            model=model,
            prompt=prompt,
            temperature=temperature,
            plan_name=plan_name,
            service_tier=service_tier,
        )
        results.append(result)

    return results

