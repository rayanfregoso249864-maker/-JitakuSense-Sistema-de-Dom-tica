# ══════════════════════════════════════════════
#  JitakuSense_PC — db.py
#  Conexión y operaciones con MySQL
#  Almacena lecturas, eventos y estadísticas
# ══════════════════════════════════════════════

import mysql.connector
from mysql.connector import Error
from datetime import datetime
from config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def conectar():
    """Crea y retorna una conexión a MySQL."""
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        return conn
    except Error as e:
        print(f"[DB] Error de conexión: {e}")
        return None


def probar_conexion() -> bool:
    """Verifica si MySQL está disponible. Retorna True/False."""
    conn = conectar()
    if conn and conn.is_connected():
        conn.close()
        return True
    return False


#  Insertar lecturas
def insertar_lectura(id_sensor: int, valor: float) -> bool:
    """Guarda una lectura de sensor en la tabla lecturas."""
    conn = conectar()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lecturas (id_sensor, valor, timestamp) VALUES (%s, %s, %s)",
            (id_sensor, valor, datetime.now())
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB] Error insertando lectura: {e}")
        return False
    finally:
        conn.close()


def insertar_evento_movimiento(id_sensor: int = 3) -> bool:
    """Guarda un evento de movimiento detectado."""
    conn = conectar()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO eventos_movimiento (id_sensor, detectado, timestamp) VALUES (%s, %s, %s)",
            (id_sensor, True, datetime.now())
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB] Error insertando movimiento: {e}")
        return False
    finally:
        conn.close()


def insertar_estado_actuador(id_actuador: int, estado: bool, origen: str = "manual") -> bool:
    """Guarda un cambio de estado de actuador."""
    conn = conectar()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO estados_actuador (id_actuador, estado, origen, timestamp) VALUES (%s, %s, %s, %s)",
            (id_actuador, estado, origen, datetime.now())
        )
        conn.commit()
        return True
    except Error as e:
        print(f"[DB] Error insertando estado actuador: {e}")
        return False
    finally:
        conn.close()


#  Consultas de historial 
def get_historial(id_sensor: int, limite: int = 50) -> list:
    """
    Retorna los últimos N registros de un sensor.
    Formato: [(timestamp, valor), ...]
    """
    conn = conectar()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT timestamp, valor FROM lecturas
               WHERE id_sensor = %s
               ORDER BY timestamp DESC LIMIT %s""",
            (id_sensor, limite)
        )
        rows = cursor.fetchall()
        return list(reversed(rows))
    except Error as e:
        print(f"[DB] Error historial: {e}")
        return []
    finally:
        conn.close()


def get_eventos_movimiento(limite: int = 20) -> list:
    """Retorna los últimos N eventos de movimiento."""
    conn = conectar()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT timestamp FROM eventos_movimiento
               ORDER BY timestamp DESC LIMIT %s""",
            (limite,)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB] Error eventos: {e}")
        return []
    finally:
        conn.close()


#  Estadísticas
def get_estadisticas(id_sensor: int, periodo: str = "1h") -> dict:
    """
    Retorna promedio, máximo y mínimo de un sensor en el período dado.
    periodo: '1h', '6h', '24h'
    """
    horas = {"1h": 1, "6h": 6, "24h": 24}.get(periodo, 1)
    conn = conectar()
    if not conn:
        return {}
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT
                 ROUND(AVG(valor), 2) AS promedio,
                 ROUND(MAX(valor), 2) AS maximo,
                 ROUND(MIN(valor), 2) AS minimo,
                 COUNT(*)            AS total
               FROM lecturas
               WHERE id_sensor = %s
                 AND timestamp >= NOW() - INTERVAL %s HOUR""",
            (id_sensor, horas)
        )
        row = cursor.fetchone()
        if row:
            return {
                "promedio": row[0] or 0,
                "maximo":   row[1] or 0,
                "minimo":   row[2] or 0,
                "total":    row[3] or 0,
                "periodo":  periodo,
            }
        return {}
    except Error as e:
        print(f"[DB] Error estadísticas: {e}")
        return {}
    finally:
        conn.close()


def get_historial_por_periodo(id_sensor: int, periodo: str = "1h") -> list:
    """Historial de lecturas filtrado por período para graficar."""
    horas = {"5m": 0.083, "30m": 0.5, "1h": 1, "6h": 6, "24h": 24}.get(periodo, 1)
    conn = conectar()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT timestamp, valor FROM lecturas
               WHERE id_sensor = %s
                 AND timestamp >= NOW() - INTERVAL %s HOUR
               ORDER BY timestamp ASC""",
            (id_sensor, horas)
        )
        return cursor.fetchall()
    except Error as e:
        print(f"[DB] Error historial período: {e}")
        return []
    finally:
        conn.close()
