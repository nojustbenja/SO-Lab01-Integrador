from pathlib import Path

entrada = Path("data/entrada")
entrada.mkdir(parents=True, exist_ok=True)

for i in range(1, 101):
    archivo = entrada / f"archivo_{i}.txt"
    archivo.write_text(
        "uno dos tres cuatro cinco procesos hilos memoria\n",
        encoding="utf-8",
    )

print("Se crearon 100 archivos en data/entrada/")
