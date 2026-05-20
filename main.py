# ══════════════════════════════════════════════
#  JitakuSense_PC — main.py
#  Punto de entrada
#  Cómo correr: python main.py
# ══════════════════════════════════════════════

import tkinter as tk
import db
import api_client as api


def main():
    print("Iniciando JitakuSense PC...")

    # Verificar MySQL
    print("Verificando MySQL...", end=" ")
    if db.probar_conexion():
        print("OK")
    else:
        print("FALLO - continuando sin base de datos")

    # Verificar ESP32
    print("Verificando ESP32...", end=" ")
    status = api.get_status()
    if status:
        print(f"OK - IP: {status.get('ip','?')}")
    else:
        print("FALLO - continuando sin ESP32")

    # Abrir ventana
    from gui import JitakuSenseApp
    root = tk.Tk()
    app  = JitakuSenseApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()