# ══════════════════════════════════════════════
#  JitakuSense_PC — gui.py
#  Ventana principal del subsistema PC
#  Usa CustomTkinter para la UI y Matplotlib para gráficas
# ══════════════════════════════════════════════

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import threading

import api_client as api
import db
from config import (
    TITULO_APP, ANCHO_APP, ALTO_APP,
    TEMA_COLOR, COLOR_ACCENT,
    INTERVALO_RECOLECCION_SEG
)

# Tema global de CustomTkinter
ctk.set_appearance_mode(TEMA_COLOR)
ctk.set_default_color_theme("dark-blue")

# Paleta de colores consistente con la web
COLORES = {
    "bg":       "#0d0f14",
    "bg2":      "#13161e",
    "bg3":      "#1a1e28",
    "accent":   COLOR_ACCENT,
    "accent2":  "#f59e6b",
    "accent3":  "#7eb8f5",
    "danger":   "#f87171",
    "text":     "#e8eaf0",
    "muted":    "#6b7280",
}


class JitakuSenseApp(ctk.CTk):
    """Ventana principal de la aplicación."""

    def __init__(self):
        super().__init__()

        self.title(TITULO_APP)
        self.geometry(f"{ANCHO_APP}x{ALTO_APP}")
        self.configure(fg_color=COLORES["bg"])
        self.resizable(True, True)

        # Estado interno
        self._corriendo      = True
        self._periodo_graf   = "1h"
        self._ultimo_mov     = None

        self._construir_ui()
        self._iniciar_recoleccion()

    #  CONSTRUCCIÓN DE LA UI


    def _construir_ui(self):
        """Construye todos los widgets de la ventana."""

        #Header 
        header = ctk.CTkFrame(self, fg_color=COLORES["bg2"], height=56, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="家  JitakuSense",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORES["accent"]
        ).pack(side="left", padx=20, pady=12)

        self.lbl_status = ctk.CTkLabel(
            header, text="● Conectando...",
            font=ctk.CTkFont(size=12),
            text_color=COLORES["muted"]
        )
        self.lbl_status.pack(side="left", padx=16)

        self.lbl_ip = ctk.CTkLabel(
            header, text="IP: —",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["muted"]
        )
        self.lbl_ip.pack(side="right", padx=20)

        self.lbl_uptime = ctk.CTkLabel(
            header, text="Uptime: —",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["muted"]
        )
        self.lbl_uptime.pack(side="right", padx=8)

        # Cuerpo principal
        cuerpo = ctk.CTkFrame(self, fg_color=COLORES["bg"], corner_radius=0)
        cuerpo.pack(fill="both", expand=True, padx=16, pady=12)
        cuerpo.columnconfigure(0, weight=0, minsize=220)
        cuerpo.columnconfigure(1, weight=1)
        cuerpo.columnconfigure(2, weight=0, minsize=240)
        cuerpo.rowconfigure(0, weight=1)

        self._col_izq    = ctk.CTkFrame(cuerpo, fg_color=COLORES["bg"], corner_radius=0)
        self._col_centro = ctk.CTkFrame(cuerpo, fg_color=COLORES["bg"], corner_radius=0)
        self._col_der    = ctk.CTkFrame(cuerpo, fg_color=COLORES["bg"], corner_radius=0)

        self._col_izq.grid   (row=0, column=0, sticky="nsew", padx=(0, 8))
        self._col_centro.grid(row=0, column=1, sticky="nsew", padx=8)
        self._col_der.grid   (row=0, column=2, sticky="nsew", padx=(8, 0))

        self._construir_col_izq()
        self._construir_col_centro()
        self._construir_col_der()

    # Columna izquierda: sensores
    def _construir_col_izq(self):
        col = self._col_izq

        # Temperatura
        self._card_temp = self._card(col, "Temperatura")
        self.lbl_temp   = self._valor_grande(self._card_temp, "—", "°C")
        self._barra_temp = self._barra(self._card_temp, COLORES["accent"])
        self._sub(self._card_temp, "DHT11 · GPIO 4")

        # Humedad
        card_hum = self._card(col, "Humedad")
        self.lbl_hum = self._valor_grande(card_hum, "—", "%")
        self._barra_hum = self._barra(card_hum, COLORES["accent3"])
        self._sub(card_hum, "DHT11 · GPIO 4")

        # Luz
        card_luz = self._card(col, "Luz ambiental")
        self.lbl_luz = self._valor_grande(card_luz, "—", "%")
        self._barra_luz = self._barra(card_luz, COLORES["accent2"])
        self._sub(card_luz, "LDR · GPIO 34")

        # Movimiento
        card_mov = self._card(col, "Movimiento")
        self.lbl_mov = ctk.CTkLabel(
            card_mov, text="Sin actividad",
            font=ctk.CTkFont(size=13),
            text_color=COLORES["muted"]
        )
        self.lbl_mov.pack(pady=8)
        self._sub(card_mov, "PIR HC-SR501 · GPIO 13")

    # Columna centro: gráficas
    def _construir_col_centro(self):
        col = self._col_centro

        # Controles de período
        frame_ctrl = ctk.CTkFrame(col, fg_color=COLORES["bg2"], corner_radius=10)
        frame_ctrl.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            frame_ctrl, text="Período:",
            font=ctk.CTkFont(size=11),
            text_color=COLORES["muted"]
        ).pack(side="left", padx=12, pady=8)

        for periodo in ["1h", "6h", "24h"]:
            ctk.CTkButton(
                frame_ctrl,
                text=periodo,
                width=60, height=28,
                font=ctk.CTkFont(size=11),
                fg_color=COLORES["bg3"],
                hover_color=COLORES["bg2"],
                border_color=COLORES["accent"],
                border_width=1,
                command=lambda p=periodo: self._cambiar_periodo(p)
            ).pack(side="left", padx=4, pady=6)

        # Gráfica de temperatura
        fig_temp, self.ax_temp = self._crear_figura()
        self.canvas_temp = FigureCanvasTkAgg(fig_temp, master=col)
        self.canvas_temp.get_tk_widget().pack(fill="both", expand=True, pady=(0, 8))

        # Gráfica de humedad
        fig_hum, self.ax_hum = self._crear_figura()
        self.canvas_hum = FigureCanvasTkAgg(fig_hum, master=col)
        self.canvas_hum.get_tk_widget().pack(fill="both", expand=True, pady=(0, 8))

        # Estadísticas
        frame_stats = ctk.CTkFrame(col, fg_color=COLORES["bg2"], corner_radius=10)
        frame_stats.pack(fill="x")
        ctk.CTkLabel(
            frame_stats, text="ESTADÍSTICAS",
            font=ctk.CTkFont(size=10),
            text_color=COLORES["muted"]
        ).pack(anchor="w", padx=12, pady=(8, 4))

        stats_grid = ctk.CTkFrame(frame_stats, fg_color="transparent")
        stats_grid.pack(fill="x", padx=12, pady=(0, 8))

        self.stats = {}
        for i, (clave, label) in enumerate([
            ("temp_prom", "Temp. prom."), ("temp_max", "Temp. máx."),
            ("temp_min", "Temp. mín."),  ("hum_prom", "Hum. prom."),
        ]):
            f = ctk.CTkFrame(stats_grid, fg_color=COLORES["bg3"], corner_radius=8)
            f.grid(row=0, column=i, padx=4, pady=0, sticky="ew")
            stats_grid.columnconfigure(i, weight=1)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=10), text_color=COLORES["muted"]).pack(pady=(6, 0))
            lbl = ctk.CTkLabel(f, text="—", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORES["text"])
            lbl.pack(pady=(0, 6))
            self.stats[clave] = lbl

    # Columna derecha: actuadores y parámetros
    def _construir_col_der(self):
        col = self._col_der

        # Actuadores
        card_act = self._card(col, "Actuadores")

        self._toggle_led = self._toggle(card_act, "LED RGB", "GPIO 5", 1)
        self._toggle_buz = self._toggle(card_act, "Buzzer",  "GPIO 18", 2)

        # Parámetros
        card_par = self._card(col, "Parámetros")
        self._input_periodo = self._parametro(
            card_par, "Período de sensado (seg)", 1, 60, 5,
            lambda v: self._aplicar_param("periodo_sensado", v, "feedb_periodo"),
            "feedb_periodo"
        )
        self._input_umbral = self._parametro(
            card_par, "Umbral temperatura (°C)", 15, 50, 30,
            lambda v: self._aplicar_param("umbral_temperatura", v, "feedb_umbral"),
            "feedb_umbral"
        )

        # Estado del sistema
        card_sys = self._card(col, "Sistema")
        self.sys_labels = {}
        for campo in ["Estado", "RAM libre", "RSSI", "Lecturas guardadas"]:
            fila = ctk.CTkFrame(card_sys, fg_color=COLORES["bg3"], corner_radius=6)
            fila.pack(fill="x", pady=3)
            ctk.CTkLabel(fila, text=campo, font=ctk.CTkFont(size=11), text_color=COLORES["muted"]).pack(side="left", padx=8, pady=4)
            lbl = ctk.CTkLabel(fila, text="—", font=ctk.CTkFont(size=11), text_color=COLORES["text"])
            lbl.pack(side="right", padx=8, pady=4)
            self.sys_labels[campo] = lbl

        # Eventos de movimiento
        card_ev = self._card(col, "Últimos eventos")
        self.lista_eventos = ctk.CTkTextbox(
            card_ev, height=100,
            font=ctk.CTkFont(size=11, family="Courier"),
            fg_color=COLORES["bg3"],
            text_color=COLORES["muted"],
            state="disabled"
        )
        self.lista_eventos.pack(fill="x")


    #  WIDGETS REUTILIZABLES
    

    def _card(self, parent, titulo: str) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=COLORES["bg2"], corner_radius=12)
        frame.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(
            frame, text=titulo.upper(),
            font=ctk.CTkFont(size=10),
            text_color=COLORES["muted"]
        ).pack(anchor="w", padx=12, pady=(10, 4))
        return frame

    def _valor_grande(self, parent, valor: str, unidad: str) -> ctk.CTkLabel:
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(anchor="w", padx=12)
        lbl = ctk.CTkLabel(f, text=valor, font=ctk.CTkFont(size=32, weight="bold"), text_color=COLORES["text"])
        lbl.pack(side="left")
        ctk.CTkLabel(f, text=unidad, font=ctk.CTkFont(size=13), text_color=COLORES["muted"]).pack(side="left", padx=4, pady=8)
        return lbl

    def _barra(self, parent, color: str) -> ctk.CTkProgressBar:
        bar = ctk.CTkProgressBar(parent, height=4, progress_color=color, fg_color=COLORES["bg3"])
        bar.pack(fill="x", padx=12, pady=(4, 0))
        bar.set(0)
        return bar

    def _sub(self, parent, texto: str):
        ctk.CTkLabel(parent, text=texto, font=ctk.CTkFont(size=10), text_color=COLORES["muted"]).pack(anchor="w", padx=12, pady=(2, 8))

    def _toggle(self, parent, nombre: str, pin: str, id_actuador: int) -> ctk.CTkSwitch:
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(fila, text=f"{nombre}\n{pin}", font=ctk.CTkFont(size=12), text_color=COLORES["text"], justify="left").pack(side="left")
        sw = ctk.CTkSwitch(
            fila, text="",
            progress_color=COLORES["accent"],
            command=lambda: self._toggle_actuador(id_actuador, sw)
        )
        sw.pack(side="right")
        return sw

    def _parametro(self, parent, label: str, minv, maxv, defv, callback, feedback_key: str):
        ctk.CTkLabel(parent, text=label, font=ctk.CTkFont(size=11), text_color=COLORES["muted"]).pack(anchor="w", padx=12, pady=(8, 2))
        fila = ctk.CTkFrame(parent, fg_color="transparent")
        fila.pack(fill="x", padx=12, pady=(0, 4))
        entry = ctk.CTkEntry(fila, width=70, font=ctk.CTkFont(size=13))
        entry.insert(0, str(defv))
        entry.pack(side="left")
        ctk.CTkButton(
            fila, text="Aplicar", width=70, height=28,
            font=ctk.CTkFont(size=11),
            fg_color="transparent",
            border_color=COLORES["accent"],
            border_width=1,
            text_color=COLORES["accent"],
            hover_color=COLORES["bg3"],
            command=lambda: callback(entry.get())
        ).pack(side="left", padx=8)
        lbl_fb = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=10), text_color=COLORES["accent"])
        lbl_fb.pack(anchor="w", padx=12)
        setattr(self, feedback_key, lbl_fb)
        return entry

    def _crear_figura(self):
        fig, ax = plt.subplots(figsize=(5, 2.2))
        fig.patch.set_facecolor(COLORES["bg2"])
        ax.set_facecolor(COLORES["bg3"])
        ax.tick_params(colors=COLORES["muted"], labelsize=8)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORES["bg3"])
        fig.tight_layout(pad=1.2)
        return fig, ax


    #  LÓGICA DE ACTUALIZACIÓN


    def _iniciar_recoleccion(self):
        """Lanza el hilo de recolección independiente."""
        self._hilo = threading.Thread(target=self._loop_recoleccion, daemon=True)
        self._hilo.start()

    def _loop_recoleccion(self):
        """Loop en hilo separado — pide datos al ESP32 y guarda en MySQL."""
        import time
        while self._corriendo:
            self._recolectar()
            time.sleep(INTERVALO_RECOLECCION_SEG)

    def _recolectar(self):
        """Pide datos al ESP32, los guarda en DB y actualiza la UI."""
        # Sensores
        lecturas = api.get_lecturas()
        if lecturas:
            t = lecturas.get("temperatura", 0)
            h = lecturas.get("humedad", 0)
            l = lecturas.get("luz", 0)
            m = lecturas.get("movimiento", False)

            # Guardar en MySQL
            db.insertar_lectura(1, t)
            db.insertar_lectura(2, h)
            db.insertar_lectura(4, l)
            if m and self._ultimo_mov != datetime.now().strftime("%H:%M"):
                db.insertar_evento_movimiento()
                self._ultimo_mov = datetime.now().strftime("%H:%M")

            # Actualizar UI (desde el hilo principal)
            self.after(0, lambda: self._actualizar_sensores_ui(t, h, l, m))

        # Status
        status = api.get_status()
        if status:
            self.after(0, lambda: self._actualizar_status_ui(status))

        # Gráficas y estadísticas
        self.after(0, self._actualizar_graficas)
        self.after(0, self._actualizar_estadisticas)
        self.after(0, self._actualizar_eventos)

    def _actualizar_sensores_ui(self, temp, hum, luz, mov):
        self.lbl_temp.configure(text=f"{temp:.1f}")
        self.lbl_hum.configure(text=f"{hum:.1f}")
        self.lbl_luz.configure(text=f"{luz:.0f}")
        self._barra_temp.set(min(temp / 50, 1.0))
        self._barra_hum.set(min(hum / 100, 1.0))
        self._barra_luz.set(min(luz / 100, 1.0))

        if mov:
            self.lbl_mov.configure(text="Movimiento detectado", text_color=COLORES["accent"])
            self.lbl_status.configure(text="● ALERTA", text_color=COLORES["danger"])
        else:
            self.lbl_mov.configure(text="Sin actividad", text_color=COLORES["muted"])
            self.lbl_status.configure(text="● En línea", text_color=COLORES["accent"])

    def _actualizar_status_ui(self, status):
        nombres = {0: "INIT", 1: "SENSANDO", 2: "ALERTA", 3: "CONFIGURANDO", 4: "ERROR"}
        self.lbl_ip.configure(text=f"IP: {status.get('ip','—')}")
        ms = status.get("uptime_ms", 0)
        s = ms // 1000; m = s // 60; h = m // 60
        uptime = f"{h}h {m%60}m" if h > 0 else f"{m}m {s%60}s"
        self.lbl_uptime.configure(text=f"Uptime: {uptime}")
        self.sys_labels["Estado"].configure(text=nombres.get(status.get("estado", 0), "—"))
        self.sys_labels["RAM libre"].configure(text=f"{status.get('heap_libre',0)//1024} KB")
        self.sys_labels["RSSI"].configure(text=f"{status.get('rssi','—')} dBm")

    def _actualizar_graficas(self):
        # Temperatura (id_sensor=1)
        datos_t = db.get_historial_por_periodo(1, self._periodo_graf)
        if datos_t:
            xs = [r[0] for r in datos_t]
            ys = [float(r[1]) for r in datos_t]
            self.ax_temp.clear()
            self.ax_temp.plot(xs, ys, color=COLORES["accent"], linewidth=1.5)
            self.ax_temp.fill_between(xs, ys, alpha=0.08, color=COLORES["accent"])
            self.ax_temp.set_facecolor(COLORES["bg3"])
            self.ax_temp.tick_params(colors=COLORES["muted"], labelsize=8)
            self.ax_temp.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            self.ax_temp.set_ylabel("°C", color=COLORES["muted"], fontsize=9)
            for spine in self.ax_temp.spines.values():
                spine.set_edgecolor(COLORES["bg3"])
            self.canvas_temp.draw()

        # Humedad (id_sensor=2)
        datos_h = db.get_historial_por_periodo(2, self._periodo_graf)
        if datos_h:
            xs = [r[0] for r in datos_h]
            ys = [float(r[1]) for r in datos_h]
            self.ax_hum.clear()
            self.ax_hum.plot(xs, ys, color=COLORES["accent3"], linewidth=1.5)
            self.ax_hum.fill_between(xs, ys, alpha=0.08, color=COLORES["accent3"])
            self.ax_hum.set_facecolor(COLORES["bg3"])
            self.ax_hum.tick_params(colors=COLORES["muted"], labelsize=8)
            self.ax_hum.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
            self.ax_hum.set_ylabel("%", color=COLORES["muted"], fontsize=9)
            for spine in self.ax_hum.spines.values():
                spine.set_edgecolor(COLORES["bg3"])
            self.canvas_hum.draw()

    def _actualizar_estadisticas(self):
        est_t = db.get_estadisticas(1, self._periodo_graf)
        est_h = db.get_estadisticas(2, self._periodo_graf)
        if est_t:
            self.stats["temp_prom"].configure(text=f"{est_t['promedio']}°C")
            self.stats["temp_max"].configure(text=f"{est_t['maximo']}°C")
            self.stats["temp_min"].configure(text=f"{est_t['minimo']}°C")
            total = est_t.get("total", 0)
            self.sys_labels["Lecturas guardadas"].configure(text=str(total))
        if est_h:
            self.stats["hum_prom"].configure(text=f"{est_h['promedio']}%")

    def _actualizar_eventos(self):
        eventos = db.get_eventos_movimiento(10)
        self.lista_eventos.configure(state="normal")
        self.lista_eventos.delete("0.0", "end")
        if eventos:
            for (ts,) in eventos:
                self.lista_eventos.insert("end", f"  {ts.strftime('%d/%m %H:%M:%S')}  Movimiento\n")
        else:
            self.lista_eventos.insert("end", "  Sin eventos registrados")
        self.lista_eventos.configure(state="disabled")

    def _cambiar_periodo(self, periodo: str):
        self._periodo_graf = periodo
        self._actualizar_graficas()
        self._actualizar_estadisticas()

    def _toggle_actuador(self, id_actuador: int, switch: ctk.CTkSwitch):
        estado = switch.get() == 1
        resultado = api.set_actuador(id_actuador, estado)
        if resultado:
            db.insertar_estado_actuador(id_actuador, estado, "manual")

    def _aplicar_param(self, clave: str, valor_str: str, feedback_key: str):
        lbl = getattr(self, feedback_key)
        try:
            valor = float(valor_str)
            resultado = api.set_parametro(clave, valor)
            if resultado:
                lbl.configure(text="Aplicado correctamente", text_color=COLORES["accent"])
            else:
                lbl.configure(text="Error al aplicar", text_color=COLORES["danger"])
        except ValueError:
            lbl.configure(text="Valor inválido", text_color=COLORES["danger"])
        self.after(2500, lambda: lbl.configure(text=""))

    def on_close(self):
        self._corriendo = False
        self.destroy()
