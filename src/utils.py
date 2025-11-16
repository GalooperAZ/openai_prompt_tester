import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompts(prompts_dir: str) -> dict:
    """Pozostawione dla wstecznej kompatybilności (nieużywane w nowym trybie)."""
    prompts = {}
    for f in Path(prompts_dir).glob("*.txt"):
        prompts[f.stem] = f.read_text(encoding="utf-8").strip()
    return prompts


def save_results(results: List[Dict[str, Any]], output_file: str) -> None:
    """Oryginalny zapis do CSV – pozostawiony na wypadek, gdyby był jeszcze używany gdzie indziej."""
    import pandas as pd

    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(
        f"✅ Wyniki zapisano do: {output_file} (UTF-8-SIG, polskie znaki bezpieczne dla Excela)"
    )


def _compute_basic_stats(result: Dict[str, Any]) -> Dict[str, Any]:
    """Wylicza długość odpowiedzi i przepustowość dla pojedynczego wyniku."""
    response = result.get("response") or ""
    chars = len(response)
    lines = response.count("\n") + 1 if response else 0

    time_s = result.get("time_s")
    total_tokens = result.get("total_tokens")
    throughput = None
    if time_s and total_tokens:
        try:
            throughput = round(total_tokens / time_s, 2) if time_s > 0 else None
        except Exception:
            throughput = None

    return {
        "response_chars": chars,
        "response_lines": lines,
        "throughput_tokens_per_s": throughput,
    }


def save_text_report(
    results: List[Dict[str, Any]], input_path: str, output_dir: Path
) -> Path:
    """Zapisuje czytelny raport .txt: blok na model + sekcja podsumowania na końcu."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = Path(input_path).stem
    out_path = output_dir / f"{base_name}_{timestamp}.txt"

    lines: List[str] = []

    ok_results: List[Dict[str, Any]] = []
    error_results: List[Dict[str, Any]] = []

    for r in results:
        # Podstawowe dane
        model = r.get("model", "UNKNOWN")
        temp = r.get("temperature")
        time_s = r.get("time_s")
        total_tokens = r.get("total_tokens")
        prompt_tokens = r.get("prompt_tokens")
        completion_tokens = r.get("completion_tokens")

        # Wykrywanie błędu
        response = r.get("response") or ""
        is_error = (
            time_s is None
            or total_tokens is None
            or (isinstance(response, str) and response.startswith("Error:"))
        )

        # Statystyki odpowiedzi
        stats = _compute_basic_stats(r)
        chars = stats["response_chars"]
        resp_lines = stats["response_lines"]
        throughput = stats["throughput_tokens_per_s"]

        status = "STATUS: ERROR" if is_error else "STATUS: OK"

        # Nagłówek 1
        header_1 = (
            f"MODEL: {model} | params: temperature={temp if temp is not None else 'NA'} | "
            f"czas: {time_s if time_s is not None else 'NA'}s | {status}"
        )

        # Nagłówek 2 – statystyki
        tokens_part = (
            f"tokens: total={total_tokens} "
            f"(prompt={prompt_tokens}, completion={completion_tokens})"
        )
        throughput_part = (
            f"throughput: {throughput} tokens/s"
            if throughput is not None
            else "throughput: NA"
        )
        header_2 = (
            f"długość: chars={chars}, lines={resp_lines} | "
            f"{tokens_part} | {throughput_part}"
        )

        lines.append(header_1)
        lines.append(header_2)
        lines.append(response)
        lines.append("")  # pusty akapit między modelami

        if is_error:
            error_results.append(r)
        else:
            ok_results.append(r)

    # Sekcja podsumowania
    lines.append("=== SUMMARY ===")
    total_models = len(results)
    lines.append(f"models_total: {total_models}")
    lines.append(f"models_ok: {len(ok_results)}")
    lines.append(f"models_error: {len(error_results)}")

    # Statystyki czasu i tokenów dla udanych odpowiedzi
    if ok_results:
        times = [r["time_s"] for r in ok_results if r.get("time_s") is not None]
        tokens = [
            r["total_tokens"]
            for r in ok_results
            if r.get("total_tokens") is not None
        ]

        if times:
            min_time = min(times)
            max_time = max(times)
            avg_time = round(sum(times) / len(times), 2)
            fastest = min(ok_results, key=lambda x: x["time_s"])
            slowest = max(ok_results, key=lambda x: x["time_s"])
            lines.append(f"time_min: {min_time}s (model={fastest.get('model')})")
            lines.append(f"time_max: {max_time}s (model={slowest.get('model')})")
            lines.append(f"time_avg: {avg_time}s")

        if tokens:
            min_tokens = min(tokens)
            max_tokens = max(tokens)
            avg_tokens = round(sum(tokens) / len(tokens), 2)
            least_tokens = min(ok_results, key=lambda x: x["total_tokens"] or 0)
            most_tokens = max(ok_results, key=lambda x: x["total_tokens"] or 0)
            lines.append(
                f"tokens_min: {min_tokens} (model={least_tokens.get('model')})"
            )
            lines.append(
                f"tokens_max: {max_tokens} (model={most_tokens.get('model')})"
            )
            lines.append(f"tokens_avg: {avg_tokens}")

    if error_results:
        lines.append("error_models:")
        for r in error_results:
            lines.append(f"  - {r.get('model', 'UNKNOWN')}")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Raport zapisano do: {out_path}")

    return out_path
