import argparse
from pathlib import Path

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
    temperature = cfg.get("temperature", 0.7)
    output_dir = Path(cfg.get("output_dir", "results"))
    output_dir.mkdir(exist_ok=True)

    input_text = input_path.read_text(encoding="utf-8").strip()

    print(f"Plik input: {input_path}")
    print(f"Liczba modeli: {len(model_list)}")
    print(f"Testowanie modeli: {', '.join(model_list)}")

    all_results = []

    for model in model_list:
        print(f"\nModel: {model} ...", end="", flush=True)
        result = run_prompt(model, input_text, temperature)
        result["prompt_id"] = input_path.stem
        all_results.append(result)
        print(f" OK ({result['time_s']}s)" if result.get("time_s") else " X")

    report_path = save_text_report(
        all_results, str(input_path), output_dir, temperature
    )

    total_tests = len(all_results)
    print(f"\nZakonczono {total_tests} testow (1 tekst × {len(model_list)} modeli).")
    print(f"Raport: {report_path}")


if __name__ == "__main__":
    main()
