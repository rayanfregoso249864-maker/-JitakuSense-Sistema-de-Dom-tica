
CREATE DATABASE IF NOT EXISTS jitakusense
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE jitakusense;


-- TABLA: sensores
-- Catálogo de sensores físicos registrados en el sistema.

CREATE TABLE sensores (
    id_sensor       INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)     NOT NULL,           -- Nombre descriptivo (ej. "DHT11")
    tipo            VARCHAR(50)     NOT NULL,           -- Tipo de magnitud: temperatura, humedad, movimiento, luz
    unidad          VARCHAR(20)     NOT NULL,           -- Unidad de medida (°C, %, lux, booleano)
    pin_gpio        TINYINT UNSIGNED NOT NULL,          -- Pin GPIO del ESP32
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    fecha_registro  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- TABLA: lecturas
-- Historial de todas las mediciones de los sensores.

CREATE TABLE lecturas (
    id_lectura      BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_sensor       INT             NOT NULL,
    valor           FLOAT           NOT NULL,           -- Valor numérico de la medición
    timestamp       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_lecturas_sensor
        FOREIGN KEY (id_sensor) REFERENCES sensores(id_sensor)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Índice para acelerar consultas por sensor y tiempo
CREATE INDEX idx_lecturas_sensor_ts ON lecturas(id_sensor, timestamp);


-- TABLA: actuadores
-- Catálogo de actuadores físicos del sistema.

CREATE TABLE actuadores (
    id_actuador     INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50)     NOT NULL,           -- Nombre descriptivo (ej. "LED RGB")
    tipo            VARCHAR(50)     NOT NULL,           -- Tipo: led, buzzer, relay
    pin_gpio        TINYINT UNSIGNED NOT NULL,          -- Pin GPIO del ESP32
    activo          BOOLEAN         NOT NULL DEFAULT TRUE,
    fecha_registro  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- TABLA: estados_actuador
-- Historial de cambios de estado de cada actuador.

CREATE TABLE estados_actuador (
    id_estado       BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_actuador     INT             NOT NULL,
    estado          BOOLEAN         NOT NULL,           -- TRUE = encendido, FALSE = apagado
    origen          ENUM('automatico', 'manual') NOT NULL DEFAULT 'manual',
    timestamp       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_estados_actuador
        FOREIGN KEY (id_actuador) REFERENCES actuadores(id_actuador)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_estados_actuador_ts ON estados_actuador(id_actuador, timestamp);


-- TABLA: eventos_movimiento
-- Registro específico de detecciones del sensor PIR.

CREATE TABLE eventos_movimiento (
    id_evento       BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_sensor       INT             NOT NULL,
    detectado       BOOLEAN         NOT NULL DEFAULT TRUE,
    timestamp       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_eventos_sensor
        FOREIGN KEY (id_sensor) REFERENCES sensores(id_sensor)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE INDEX idx_eventos_ts ON eventos_movimiento(timestamp);


-- TABLA: parametros
-- Configuración global del sistema (modificable desde la GUI).

CREATE TABLE parametros (
    id_parametro    INT AUTO_INCREMENT PRIMARY KEY,
    clave           VARCHAR(50)     NOT NULL UNIQUE,    -- Identificador del parámetro
    valor           VARCHAR(100)    NOT NULL,           -- Valor actual
    descripcion     VARCHAR(200)    NOT NULL,           -- Descripción legible
    unidad          VARCHAR(20)     DEFAULT NULL,       -- Unidad (segundos, °C, etc.)
    ultima_modificacion DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                    ON UPDATE CURRENT_TIMESTAMP
);


--  DATOS INICIALES

-- Sensores
INSERT INTO sensores (nombre, tipo, unidad, pin_gpio) VALUES
    ('DHT11 Temperatura',   'temperatura',  '°C',       4),
    ('DHT11 Humedad',       'humedad',      '%',        4),
    ('PIR HC-SR501',        'movimiento',   'booleano', 13),
    ('LDR',                 'luz',          '%',        34);

-- Actuadores
INSERT INTO actuadores (nombre, tipo, pin_gpio) VALUES
    ('LED RGB',  'led',    5),
    ('Buzzer',   'buzzer', 18);

-- Parámetros configurables
INSERT INTO parametros (clave, valor, descripcion, unidad) VALUES
    ('periodo_sensado',     '5',    'Intervalo entre lecturas de sensores',         'segundos'),
    ('umbral_temperatura',  '30',   'Temperatura máxima antes de activar alerta',   '°C');

-- Lecturas de ejemplo
INSERT INTO lecturas (id_sensor, valor, timestamp) VALUES
    (1, 24.5, NOW() - INTERVAL 10 MINUTE),
    (1, 25.1, NOW() - INTERVAL 5  MINUTE),
    (1, 25.8, NOW()),
    (2, 55.0, NOW() - INTERVAL 10 MINUTE),
    (2, 56.2, NOW() - INTERVAL 5  MINUTE),
    (2, 57.0, NOW()),
    (4, 70.0, NOW() - INTERVAL 10 MINUTE),
    (4, 65.0, NOW() - INTERVAL 5  MINUTE),
    (4, 60.0, NOW());

-- Eventos de movimiento de ejemplo
INSERT INTO eventos_movimiento (id_sensor, detectado, timestamp) VALUES
    (3, TRUE, NOW() - INTERVAL 15 MINUTE),
    (3, TRUE, NOW() - INTERVAL 3  MINUTE);

-- Estados de actuadores de ejemplo
INSERT INTO estados_actuador (id_actuador, estado, origen, timestamp) VALUES
    (1, TRUE,  'automatico', NOW() - INTERVAL 3 MINUTE),
    (2, TRUE,  'automatico', NOW() - INTERVAL 3 MINUTE),
    (1, FALSE, 'manual',     NOW() - INTERVAL 1 MINUTE),
    (2, FALSE, 'manual',     NOW() - INTERVAL 1 MINUTE);