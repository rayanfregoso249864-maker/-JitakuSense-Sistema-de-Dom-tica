# ══════════════════════════════════════════════
#  JitakuSense_PC — api_client.py
#  Comunicación TCP con el ESP32 via HTTP
#  Consume todos los endpoints de la API REST
# ══════════════════════════════════════════════

import requests
from config import ESP32_BASE, TIMEOUT_SEG


def _get(endpoint: str) -> dict | None:
    """Petición GET al ESP32. Retorna dict o None si falla."""
    try:
        r = requests.get(f"{ESP32_BASE}{endpoint}", timeout=TIMEOUT_SEG)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        print(f"[API] Sin conexión al ESP32 — {endpoint}")
        return None
    except requests.exceptions.Timeout:
        print(f"[API] Timeout — {endpoint}")
        return None
    except Exception as e:
        print(f"[API] Error GET {endpoint}: {e}")
        return None


def _put(endpoint: str, body: dict) -> dict | None:
    """Petición PUT al ESP32. Retorna dict o None si falla."""
    try:
        r = requests.put(
            f"{ESP32_BASE}{endpoint}",
            json=body,
            timeout=TIMEOUT_SEG
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[API] Error PUT {endpoint}: {e}")
        return None


# ── Sensores ─────────────────────────────────────
def get_lecturas() -> dict | None:
    """Última lectura de todos los sensores."""
    return _get("/api/sensores/lecturas")


def get_historial_sensor(id_sensor: int, limite: int = 50) -> list | None:
    """Historial de lecturas de un sensor específico."""
    return _get(f"/api/sensores/{id_sensor}/historial?limite={limite}")


# ── Actuadores ───────────────────────────────────
def get_actuadores() -> dict | None:
    """Estado actual de todos los actuadores."""
    return _get("/api/actuadores")


def set_actuador(id_actuador: int, estado: bool) -> dict | None:
    """Cambia el estado de un actuador (True=ON, False=OFF)."""
    return _put(f"/api/actuadores/{id_actuador}", {
        "estado": estado,
        "origen": "manual"
    })


# ── Movimiento ───────────────────────────────────
def get_movimiento() -> dict | None:
    """Último estado del sensor PIR."""
    return _get("/api/movimiento")


# ── Parámetros ───────────────────────────────────
def get_parametros() -> list | None:
    """Lista de parámetros configurables actuales."""
    return _get("/api/parametros")


def set_parametro(clave: str, valor: float) -> dict | None:
    """Modifica un parámetro en el ESP32."""
    return _put(f"/api/parametros/{clave}", {"valor": valor})


# ── Sistema ──────────────────────────────────────
def get_status() -> dict | None:
    """Estado general del ESP32: uptime, IP, RAM, estado."""
    return _get("/api/status")


def get_estadisticas() -> dict | None:
    """Estadísticas de sensores (promedios, máximos, mínimos)."""
    return _get("/api/estadisticas")
