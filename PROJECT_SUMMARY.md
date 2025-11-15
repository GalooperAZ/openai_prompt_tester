## Cel projektu

Projekt `openai_prompt_tester` służy do **porównywania zachowania wielu modeli OpenAI na tym samym tekście wejściowym**.  
Narzędzie automatycznie:
- wczytuje tekst z pliku `.txt`,
- wysyła go kolejno do wszystkich modeli zdefiniowanych w konfiguracji,
- zbiera odpowiedzi wraz ze statystykami,
- zapisuje wyniki w czytelnym raporcie tekstowym `.txt`.

## Architektura i logika działania

### Konfiguracja (`config/openai.yml`)

Plik YAML zawiera:
- `model_list` – listę modeli, które mają zostać przetestowane (np. `gpt-4.1`, `gpt-5.1`, `o3`, itp.),
- `temperature` – parametr temperatury wspólny dla wszystkich wywołań,
- `output_dir` – katalog, w którym zapisywane są raporty (np. `results`).

Konfiguracja jest wczytywana funkcją `load_config` z modułu `src.utils`.

### Wejście użytkownika (plik input)

Użytkownik tworzy plik `.txt` z **pełnym promptem**, tzn.:
- może to być polecenie + tekst do przetworzenia,
- lub dowolny inny opis zadania dla modelu.

Przykład:

```text
Przetłumacz na angielski:

Polska gospodarka rozwija się w szybkim tempie.
```

Ścieżka do tego pliku jest przekazywana jako argument w linii komend.

### Główna logika (`src/main.py`)

1. **Parsowanie argumentów**  
   Program przyjmuje jeden argument pozycyjny – ścieżkę do pliku `.txt` z tekstem wejściowym.

2. **Walidacja pliku**  
   Sprawdzane jest, czy plik istnieje. Jeśli nie – wypisywany jest komunikat o błędzie, a program kończy działanie.

3. **Wczytanie konfiguracji i tekstu**  
   - Wczytywana jest konfiguracja z `config/openai.yml`.
   - Pobierana jest lista modeli `model_list`, temperatura `temperature` i katalog wyjściowy `output_dir`.
   - Tworzony jest katalog wyników (jeśli nie istnieje).
   - Z pliku wejściowego wczytywany jest tekst (`input_text`), który będzie wysyłany do wszystkich modeli.

4. **Pętla po modelach**  
   Dla każdego modelu z `model_list`:
   - wywoływana jest funkcja `run_prompt(model, input_text, temperature)` z modułu `src.runner`,
   - mierzony jest czas odpowiedzi i zbierane są statystyki zużycia tokenów,
   - wynik (odpowiedź modelu + statystyki) jest dodawany do listy `all_results`,
   - w konsoli wypisywany jest status (`OK` z czasem lub `X` w przypadku błędu).

5. **Generowanie raportu**  
   Po przetworzeniu wszystkich modeli:
   - wywoływana jest funkcja `save_text_report(all_results, input_path, output_dir, temperature)` z `src.utils`,
   - tworzony jest raport `.txt` w katalogu `results`,
   - ścieżka do raportu jest wypisywana w konsoli.

### Wywołanie modeli OpenAI (`src/runner.py`)

Moduł `runner` zawiera funkcję:

- `run_prompt(model: str, prompt: str, temperature: float) -> dict`  
  - tworzy klienta `OpenAI()`,
  - wysyła żądanie `chat.completions.create` z:
    - `model` – nazwą modelu,
    - `messages=[{"role": "user", "content": prompt}]` – pełny prompt z pliku input,
    - `temperature` – zgodnie z konfiguracją,
  - mierzy czas od wysłania do otrzymania odpowiedzi,
  - wyciąga:
    - treść odpowiedzi (`response`),
    - statystyki tokenów (`prompt_tokens`, `completion_tokens`, `total_tokens`),
  - zwraca słownik z powyższymi informacjami.
  - W przypadku błędu:
    - zwraca `response` w postaci komunikatu błędu (`"Error: ..."`) oraz `None` dla czasu i tokenów.

### Narzędzia pomocnicze i raport (`src/utils.py`)

Moduł `utils` odpowiada za:

- `load_config(path)` – wczytanie pliku YAML z konfiguracją.
- `save_results(...)` – oryginalny zapis do CSV (pozostawiony dla ewentualnej wstecznej kompatybilności).
- `save_text_report(results, input_path, output_dir, temperature)` – **kluczowa funkcja formatująca raport `.txt`**:
  - tworzy nazwę pliku raportu na podstawie:
    - nazwy pliku wejściowego,
    - znacznika czasu (`YYYYMMDD_HHMMSS`),
  - dla każdego modelu buduje blok z:
    - nagłówkiem 1:  
      `MODEL: <model> | params: temperature=<temp> | czas: <time_s>s | STATUS: OK/ERROR`
    - nagłówkiem 2 (statystyki):  
      `długość: chars=<liczba_znaków>, lines=<liczba_linii> | tokens: total=<total> (prompt=<prompt>, completion=<completion>) | throughput: <tokens/s>`
    - treścią odpowiedzi modelu (pełny tekst),
    - pustą linią jako separatorem przed kolejnym modelem,
  - na końcu dodaje sekcję podsumowania `=== SUMMARY ===`, gdzie znajdują się m.in.:
    - liczba modeli ogółem, liczba modeli OK i z błędami,
    - min/avg/max czasu odpowiedzi,
    - min/avg/max `total_tokens`,
    - lista modeli, dla których wystąpiły błędy.

## Zakres wykonanych prac

W ramach prac nad projektem wykonano m.in.:

1. **Przebudowę trybu pracy**  
   - Zrezygnowano z iterowania po wielu promptach z katalogu `prompts/`.  
   - Wprowadzono tryb: **jeden plik `.txt` z pełnym promptem → wszystkie modele z `model_list`**.

2. **Aktualizację listy modeli**  
   - `model_list` w `config/openai.yml` została zaktualizowana do nowego zestawu modeli OpenAI (m.in. `gpt‑4.1`, `gpt‑5.1`, seria `o*`, itp.).

3. **Dodanie raportu `.txt` zamiast (lub obok) CSV**  
   - Zaimplementowano funkcję `save_text_report`, która:
     - tworzy czytelny raport tekstowy z blokiem dla każdego modelu,
     - dodaje bogate statystyki (czas, tokeny, długość odpowiedzi, throughput),
     - generuje sekcję `SUMMARY` z podsumowaniem całego runu.

4. **Obsługa błędów**  
   - W raportach widoczny jest status `STATUS: OK` / `STATUS: ERROR`.  
   - Błędy są zliczane i wypisywane w sekcji `SUMMARY` wraz z listą modeli, które zwróciły błąd.

5. **Porządkowanie importów i struktury pakietu**  
   - `src` zostało przekształcone w pakiet Pythona (`__init__.py`),  
   - w `main.py` poprawiono importy tak, aby poprawnie działało uruchamianie:
     - jako moduł pakietu (`python -m src.main input.txt`),
     - oraz ewentualnie bezpośrednio (`python src/main.py input.txt`) – dzięki fallbackowi importów.

## Sposób użycia z perspektywy użytkownika

1. Przygotuj plik `.txt` z pełnym promptem (polecenie + tekst do obróbki).  
2. Upewnij się, że:
   - w `config/openai.yml` jest poprawna lista modeli i temperatura,
   - zmienna środowiskowa `OPENAI_API_KEY` jest ustawiona.
3. W katalogu projektu uruchom:

```bash
python -m src.main path\do\input.txt
```

4. Po zakończeniu działania:
   - w katalogu `results` pojawi się raport `.txt` z nazwą zawierającą nazwę pliku input oraz znacznik czasu,
   - raport zawiera odpowiedzi wszystkich modeli oraz statystyki ich działania.

Dokument ten stanowi podsumowanie aktualnego stanu projektu oraz opis logiki działania narzędzia, ułatwiając dalszy rozwój, refaktoryzację i użytkowanie.


