import subprocess
from sqlworker import init_database

scripts = [
    "scraper_otodom.py",
    "scraper_trojmiasto.py",
    "scraper_olx.py"
]

def run_script(script_name):
    init_database()
    print(f"Uruchamianie: {script_name}")
    try:
        result = subprocess.run(
            ["python3", script_name],  
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout = result.stdout.decode('utf-8') if result.stdout else ''
        stderr = result.stderr.decode('utf-8') if result.stderr else ''
        
        if result.returncode == 0:
            print(f"Skrypt {script_name} zakończony sukcesem.")
            print(f"Wynik:\n{stdout}")
        else:
            print(f"Błąd podczas uruchamiania skryptu {script_name}.\nKod wyjścia: {result.returncode}")
            print("Szczegóły błędu:")
            print(stderr)
    except Exception as e:
        print(f"Błąd: {e}")

def main():
    for script in scripts:
        run_script(script)

if __name__ == "__main__":
    main()
