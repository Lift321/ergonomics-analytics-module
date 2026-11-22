# Moduł analityki i kalibracji ergonomii pracy

## Nazwa kursu
Testowanie i Jakość Oprogramowania

## Autor
Adam Szczerbiński 38122

## Temat projektu
Moduł analityki i kalibracji ergonomii pracy (Ergonomics Analytics)

## Opis projektu
Aplikacja webowa analizuje postawę użytkownika przy pracy przy komputerze na podstawie
współrzędnych punktów ciała (ucho, barki), np. z modelu detekcji pozy.

Najważniejsze funkcje:
- **Kalibracja**: zapis postawy wzorcowej użytkownika (bazowy kąt szyi, asymetria barków),
  tolerancji oraz czasu histerezy alertu.
- **Ocena postawy**: obliczanie kąta szyi i asymetrii barków, odchylenia od wzorca
  i zwracanie statusu `GOOD`, `WARNING` albo `ALERT`.
- **Tryby oceny**: `standard`, `strict` (tolerancja ×0.7), `relaxed` (tolerancja ×1.3).
- **Histereza alertu**: alert jest zgłaszany dopiero, gdy zła postawa trwa
  co najmniej zadaną liczbę sekund.
- **Statystyki sesji**: liczba próbek, procent poprawnej postawy, średni kąt szyi,
  liczba alertów i historia pomiarów.

## Uruchomienie projektu

### Wymagania
- Python 3.10 lub nowszy
- pip

### Instalacja i start (Windows, PowerShell)
```powershell
# 1. Przejdź do katalogu projektu
cd sciezka\do\projektu

# 2. Utwórz i aktywuj środowisko wirtualne
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Zainstaluj zależności
pip install -r requirements.txt

# 4. Uruchom aplikację
python app.py
```

Jeśli PowerShell blokuje aktywację środowiska (`running scripts is disabled`), wykonaj raz:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### Instalacja i start (Linux / macOS)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

### Korzystanie z aplikacji
1. Otwórz w przeglądarce: http://127.0.0.1:5000
2. Wpisz identyfikator użytkownika (domyślnie `user_1`).
3. W sekcji **1. Kalibracja** kliknij **Zapisz kalibrację**.
4. W sekcji **2. Symulacja** wybierz tryb i kliknij **Oceń postawę**.
5. Statystyki i historia pomiarów odświeżają się w sekcji **3**.

Dane zapisywane są w pliku `ergonomics.db` (SQLite), tworzonym automatycznie
w katalogu projektu. Aby zatrzymać serwer, naciśnij `Ctrl+C`.

## Technologie użyte w projekcie
- Python 3
- Flask 3.0.3
- SQLite (moduł `sqlite3` z biblioteki standardowej)
- HTML, CSS, JavaScript (Fetch API)
