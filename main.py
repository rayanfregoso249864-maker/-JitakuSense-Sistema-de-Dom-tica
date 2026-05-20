# ══════════════════════════════════════════════
#  JitakuSense_PC — main.py
#  Punto de entrada de la aplicación
#
#  Cómo correr:
#    1. pip install -r requirements.txt
#    2. python main.py
# ══════════════════════════════════════════════

import sys
from gui import JitakuSenseApp
import db
import api_client as api


def verificar_dependencias():
    """Verifica que MySQL y el ESP32 estén accesibles antes de abrir la ventana."""

    print("=" * 48)
    print("  JitakuSense — Iniciando subsistema PC")
    print("=" * 48)

    # Verificar MySQL
    print("\n[1/2] Verificando conexión a MySQL...", end=" ")
    if db.probar_conexion():
        print("OK")
    else:
        print("FALLO")
        print("\n  ✗ No se pudo conectar a MySQL.")
        print("  → Verifica que MySQL esté corriendo.")
        print("  → Revisa usuario/contraseña en config.py")
        respuesta = input("\n  ¿Continuar de todas formas? (s/n): ")
        if respuesta.lower() != "s":
            sys.exit(1)

    # Verificar ESP32
    print("[2/2] Verificando conexión al ESP32...", end=" ")
    status = api.get_status()
    if status:
        print(f"OK — IP: {status.get('ip','?')} | Estado: {status.get('estado','?')}")
    else:
        print("FALLO")
        print("\n  ✗ No se pudo conectar al ESP32.")
        print("  → Verifica que el ESP32 esté encendido y en la misma red.")
        print("  → Revisa la IP en config.py")
        respuesta = input("\n  ¿Continuar de todas formas? (s/n): ")
        if respuesta.lower() != "s":
            sys.exit(1)

    print("\n  Abriendo interfaz...\n")


def main():
    verificar_dependencias()

    app = JitakuSenseApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
