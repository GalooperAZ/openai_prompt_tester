import argparse
from pathlib import Path

try:
    # Uruchamianie jako moduł pakietu: python -m src.main
    from src.utils import load_config, save_text_report
    from src.runner import run_prompt
except ImportError:  # fallback, np. przy bezpośrednim uruchomieniu pliku
    from utils import load_config, save_text_report
    from runner import run_prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Uruchamia pojedynczy plik .txt na wszystkich modelach z config/openai.yml "
            "i zapisuje raport w formacie .txt."
        )
    )
    parser.add_argument(
        "input",
        help="Ścieżka do pliku .txt z tekstem wejściowym dla wszystkich modeli.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)

    if not input_path.is_file():
        print(f"❌ Plik wejściowy nie istnieje: {input_path}")
        return

    cfg = load_config("config/openai.yml")

    model_list = cfg.get("model_list", [])
    model_temps = cfg.get("model_temps", {}) or {}

    # Walidacja: każdy model z listy musi mieć zdefiniowaną temperaturę
    for m in model_list:
        if m not in model_temps:
            raise ValueError(
                f"Brak wartości temperature dla modelu '{m}' w model_temps w config/openai.yml"
            )

    output_dir = Path(cfg.get("output_dir", "results"))
    output_dir.mkdir(exist_ok=True)

    input_text = input_path.read_text(encoding="utf-8").strip()

    print(f"Plik input: {input_path}")
    print(f"Liczba modeli: {len(model_list)}")
    print(f"Testowanie modeli: {', '.join(model_list)}")

    all_results = []

    for model in model_list:
        temperature = model_temps[model]
        print(f"\nModel: {model} (temperature={temperature})")

        # Dla każdego modelu wykonujemy to samo zapytanie w trzech planach rozliczeniowych:
        # STANDARD -> service_tier=\"standard\"
        # FLEX     -> service_tier=\"flex\"
        # BATCH    -> service_tier=\"batch\"
        plan_results = run_prompt(model, input_text, temperature)

        for r in plan_results:
            r["prompt_id"] = input_path.stem
            r["temperature"] = temperature
            all_results.append(r)

            plan = r.get("billing_plan", "UNKNOWN")
            time_s = r.get("time_s")
            status = "OK" if time_s is not None else "ERROR"
            time_str = f"{time_s}s" if time_s is not None else "NA"
            print(f"  - plan={plan}: {status} (czas={time_str})")

    report_path = save_text_report(all_results, str(input_path), output_dir)

    total_tests = len(all_results)
    print(
        f"\nZakonczono {total_tests} testow "
        f"(1 tekst × {len(model_list)} modeli × 3 plany rozliczeniowe)."
    )
    print(f"Raport: {report_path}")


if __name__ == "__main__":
    main()
