# ══════════════════════════════════════════════
#  JitakuSense_PC — config.py
#  Configuración centralizada del sistema
#  Cambia aquí la IP del ESP32 y los datos de MySQL
# ══════════════════════════════════════════════

# ── ESP32 
ESP32_IP      = "192.168.1.51"   # 
ESP32_PORT    = 80
ESP32_BASE    = f"http://{ESP32_IP}:{ESP32_PORT}"
TIMEOUT_SEG   = 5                 # segundos de espera por respuesta

# ── MySQL
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_USER     = "root"             
DB_PASSWORD = "oto19816"                 
DB_NAME     = "jitakusense"

# ── Recolección de datos 
INTERVALO_RECOLECCION_SEG = 5     # cada cuántos segundos pide datos al ESP32

# ── UI 
TITULO_APP   = "JitakuSense — Panel de Control"
ANCHO_APP    = 1100
ALTO_APP     = 700
TEMA_COLOR   = "dark"             # "dark" o "light"
COLOR_ACCENT = "#7dd3b0"
