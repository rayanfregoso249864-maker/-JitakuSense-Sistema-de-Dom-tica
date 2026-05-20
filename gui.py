# ══════════════════════════════════════════════
#  JitakuSense_PC — gui.py
#  Ventana principal del subsistema PC
#  Tkinter simple + Matplotlib para gráficas
# ══════════════════════════════════════════════

import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime
import threading

import api_client as api
import db
from config import TITULO_APP, INTERVALO_RECOLECCION_SEG

class JitakuSenseApp:

    def __init__(self, root):
        self.root = root
        self.root.title(TITULO_APP)
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")

        self._corriendo    = True
        self._estado_led   = False
        self._estado_buz   = False
        self._periodo_graf = "1h"

        self._construir_ui()
        self._iniciar_recoleccion()

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════

    def _construir_ui(self):

        # ── Header ──────────────────────────────
        header = tk.Frame(self.root, bg="#2c3e50", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="JitakuSense — Panel de Control",
                 bg="#2c3e50", fg="white",
                 font=("Arial", 14, "bold")).pack(side="left", padx=16, pady=12)

        self.lbl_status = tk.Label(header, text="Conectando...",
                                   bg="#2c3e50", fg="#f39c12",
                                   font=("Arial", 11))
        self.lbl_status.pack(side="right", padx=16)

        # ── Cuerpo ───────────────────────────────
        cuerpo = tk.Frame(self.root, bg="#f0f0f0")
        cuerpo.pack(fill="both", expand=True, padx=10, pady=10)

        # Columna izquierda
        izq = tk.Frame(cuerpo, bg="#f0f0f0", width=200)
        izq.pack(side="left", fill="y", padx=(0, 8))
        izq.pack_propagate(False)

        # Columna central
        centro = tk.Frame(cuerpo, bg="#f0f0f0")
        centro.pack(side="left", fill="both", expand=True, padx=8)

        # Columna derecha
        der = tk.Frame(cuerpo, bg="#f0f0f0", width=200)
        der.pack(side="right", fill="y", padx=(8, 0))
        der.pack_propagate(False)

        self._col_izq(izq)
        self._col_centro(centro)
        self._col_der(der)

    def _col_izq(self, parent):
        tk.Label(parent, text="SENSORES", bg="#f0f0f0",
                 font=("Arial", 10, "bold"), fg="#555").pack(anchor="w", pady=(0,4))

        # Temperatura
        f = self._frame(parent)
        tk.Label(f, text="Temperatura", bg="white", fg="#888", font=("Arial", 9)).pack(anchor="w")
        self.lbl_temp = tk.Label(f, text="-- °C", bg="white", font=("Arial", 18, "bold"))
        self.lbl_temp.pack(anchor="w")
        tk.Label(f, text="DHT11 · GPIO 4", bg="white", fg="#aaa", font=("Arial", 8)).pack(anchor="w")

        # Humedad
        f = self._frame(parent)
        tk.Label(f, text="Humedad", bg="white", fg="#888", font=("Arial", 9)).pack(anchor="w")
        self.lbl_hum = tk.Label(f, text="-- %", bg="white", font=("Arial", 18, "bold"))
        self.lbl_hum.pack(anchor="w")
        tk.Label(f, text="DHT11 · GPIO 4", bg="white", fg="#aaa", font=("Arial", 8)).pack(anchor="w")

        # Luz
        f = self._frame(parent)
        tk.Label(f, text="Luz ambiental", bg="white", fg="#888", font=("Arial", 9)).pack(anchor="w")
        self.lbl_luz = tk.Label(f, text="-- %", bg="white", font=("Arial", 18, "bold"))
        self.lbl_luz.pack(anchor="w")
        tk.Label(f, text="LDR · GPIO 34", bg="white", fg="#aaa", font=("Arial", 8)).pack(anchor="w")

        # Movimiento
        f = self._frame(parent)
        tk.Label(f, text="Movimiento", bg="white", fg="#888", font=("Arial", 9)).pack(anchor="w")
        self.lbl_mov = tk.Label(f, text="Sin actividad", bg="white", font=("Arial", 12))
        self.lbl_mov.pack(anchor="w", pady=4)
        tk.Label(f, text="PIR · GPIO 13", bg="white", fg="#aaa", font=("Arial", 8)).pack(anchor="w")

    def _col_centro(self, parent):
        # Controles de período
        ctrl = tk.Frame(parent, bg="#f0f0f0")
        ctrl.pack(fill="x", pady=(0, 6))
        tk.Label(ctrl, text="Período:", bg="#f0f0f0", font=("Arial", 10)).pack(side="left")
        for p in ["1h", "6h", "24h"]:
            tk.Button(ctrl, text=p, width=4,
                      command=lambda x=p: self._cambiar_periodo(x),
                      font=("Arial", 9)).pack(side="left", padx=2)

        # Gráfica temperatura
        tk.Label(parent, text="Temperatura (°C)", bg="#f0f0f0",
                 font=("Arial", 9, "bold"), fg="#555").pack(anchor="w")
        fig1, self.ax_temp = plt.subplots(figsize=(5, 1.8))
        fig1.patch.set_facecolor("#ffffff")
        self.ax_temp.set_facecolor("#f8f8f8")
        fig1.tight_layout(pad=1)
        self.canvas_temp = FigureCanvasTkAgg(fig1, master=parent)
        self.canvas_temp.get_tk_widget().pack(fill="x", pady=(0, 8))

        # Gráfica humedad
        tk.Label(parent, text="Humedad (%)", bg="#f0f0f0",
                 font=("Arial", 9, "bold"), fg="#555").pack(anchor="w")
        fig2, self.ax_hum = plt.subplots(figsize=(5, 1.8))
        fig2.patch.set_facecolor("#ffffff")
        self.ax_hum.set_facecolor("#f8f8f8")
        fig2.tight_layout(pad=1)
        self.canvas_hum = FigureCanvasTkAgg(fig2, master=parent)
        self.canvas_hum.get_tk_widget().pack(fill="x", pady=(0, 8))

        # Estadísticas
        tk.Label(parent, text="Estadísticas", bg="#f0f0f0",
                 font=("Arial", 9, "bold"), fg="#555").pack(anchor="w")
        sf = tk.Frame(parent, bg="#f0f0f0")
        sf.pack(fill="x")
        self.stats = {}
        for i, (k, txt) in enumerate([
            ("t_prom","Temp prom"), ("t_max","Temp máx"),
            ("t_min","Temp mín"),  ("h_prom","Hum prom")
        ]):
            c = tk.Frame(sf, bg="white", relief="solid", bd=1)
            c.grid(row=0, column=i, padx=3, sticky="ew")
            sf.columnconfigure(i, weight=1)
            tk.Label(c, text=txt, bg="white", fg="#888", font=("Arial", 8)).pack(pady=(4,0))
            lbl = tk.Label(c, text="--", bg="white", font=("Arial", 11, "bold"))
            lbl.pack(pady=(0,4))
            self.stats[k] = lbl

    def _col_der(self, parent):
        # Actuadores
        tk.Label(parent, text="ACTUADORES", bg="#f0f0f0",
                 font=("Arial", 10, "bold"), fg="#555").pack(anchor="w", pady=(0,4))

        f = self._frame(parent)
        tk.Label(f, text="LED RGB — GPIO 5", bg="white", font=("Arial", 10)).pack(anchor="w")
        self.lbl_led = tk.Label(f, text="OFF", bg="white", fg="#e74c3c", font=("Arial", 12, "bold"))
        self.lbl_led.pack(anchor="w", pady=2)
        tk.Button(f, text="Encender / Apagar", font=("Arial", 9),
                  command=lambda: self._toggle(1)).pack(anchor="w", pady=(2,0))

        f = self._frame(parent)
        tk.Label(f, text="Buzzer — GPIO 18", bg="white", font=("Arial", 10)).pack(anchor="w")
        self.lbl_buz = tk.Label(f, text="OFF", bg="white", fg="#e74c3c", font=("Arial", 12, "bold"))
        self.lbl_buz.pack(anchor="w", pady=2)
        tk.Button(f, text="Encender / Apagar", font=("Arial", 9),
                  command=lambda: self._toggle(2)).pack(anchor="w", pady=(2,0))

        # Parámetros
        tk.Label(parent, text="PARÁMETROS", bg="#f0f0f0",
                 font=("Arial", 10, "bold"), fg="#555").pack(anchor="w", pady=(10,4))

        f = self._frame(parent)
        tk.Label(f, text="Período de sensado (seg)", bg="white", fg="#888", font=("Arial", 8)).pack(anchor="w")
        self.entry_periodo = tk.Entry(f, width=8, font=("Arial", 11))
        self.entry_periodo.insert(0, "5")
        self.entry_periodo.pack(anchor="w", pady=2)
        tk.Button(f, text="Aplicar", font=("Arial", 9),
                  command=lambda: self._aplicar("periodo_sensado", self.entry_periodo)).pack(anchor="w")
        self.fb_periodo = tk.Label(f, text="", bg="white", fg="#27ae60", font=("Arial", 8))
        self.fb_periodo.pack(anchor="w")

        f = self._frame(parent)
        tk.Label(f, text="Umbral temperatura (°C)", bg="white", fg="#888", font=("Arial", 8)).pack(anchor="w")
        self.entry_umbral = tk.Entry(f, width=8, font=("Arial", 11))
        self.entry_umbral.insert(0, "30")
        self.entry_umbral.pack(anchor="w", pady=2)
        tk.Button(f, text="Aplicar", font=("Arial", 9),
                  command=lambda: self._aplicar("umbral_temperatura", self.entry_umbral)).pack(anchor="w")
        self.fb_umbral = tk.Label(f, text="", bg="white", fg="#27ae60", font=("Arial", 8))
        self.fb_umbral.pack(anchor="w")

        # Sistema
        tk.Label(parent, text="SISTEMA", bg="#f0f0f0",
                 font=("Arial", 10, "bold"), fg="#555").pack(anchor="w", pady=(10,4))
        f = self._frame(parent)
        self.sys_labels = {}
        for campo in ["Estado", "IP", "RAM libre", "Uptime"]:
            fila = tk.Frame(f, bg="white")
            fila.pack(fill="x", pady=1)
            tk.Label(fila, text=campo+":", bg="white", fg="#888", font=("Arial", 9), width=8, anchor="w").pack(side="left")
            lbl = tk.Label(fila, text="--", bg="white", font=("Arial", 9))
            lbl.pack(side="left")
            self.sys_labels[campo] = lbl

    # ══════════════════════════════════════════
    #  WIDGETS HELPER
    # ══════════════════════════════════════════

    def _frame(self, parent):
        f = tk.Frame(parent, bg="white", relief="solid", bd=1)
        f.pack(fill="x", pady=(0, 6), ipady=4, ipadx=6)
        return f

    # ══════════════════════════════════════════
    #  LÓGICA
    # ══════════════════════════════════════════

    def _iniciar_recoleccion(self):
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        import time
        while self._corriendo:
            self._recolectar()
            time.sleep(INTERVALO_RECOLECCION_SEG)

    def _recolectar(self):
        lecturas = api.get_lecturas()
        if lecturas:
            t = lecturas.get("temperatura", 0)
            h = lecturas.get("humedad", 0)
            l = lecturas.get("luz", 0)
            m = lecturas.get("movimiento", False)
            db.insertar_lectura(1, t)
            db.insertar_lectura(2, h)
            db.insertar_lectura(4, l)
            if m:
                db.insertar_evento_movimiento()
            self.root.after(0, lambda: self._actualizar_sensores(t, h, l, m))

        status = api.get_status()
        if status:
            self.root.after(0, lambda: self._actualizar_status(status))

        self.root.after(0, self._actualizar_graficas)
        self.root.after(0, self._actualizar_stats)

    def _actualizar_sensores(self, t, h, l, m):
        self.lbl_temp.config(text=f"{t:.1f} °C")
        self.lbl_hum.config(text=f"{h:.1f} %")
        self.lbl_luz.config(text=f"{l:.0f} %")
        if m:
            self.lbl_mov.config(text="Detectado", fg="#e67e22")
            self.lbl_status.config(text="ALERTA", fg="#e74c3c")
        else:
            self.lbl_mov.config(text="Sin actividad", fg="#333")
            self.lbl_status.config(text="En línea", fg="#27ae60")

    def _actualizar_status(self, s):
        nombres = {0:"INIT",1:"SENSANDO",2:"ALERTA",3:"CONFIGURANDO",4:"ERROR"}
        self.sys_labels["Estado"].config(text=nombres.get(s.get("estado",0),"--"))
        self.sys_labels["IP"].config(text=s.get("ip","--"))
        self.sys_labels["RAM libre"].config(text=f"{s.get('heap_libre',0)//1024} KB")
        ms = s.get("uptime_ms", 0)
        seg = ms//1000; m = seg//60; h = m//60
        self.sys_labels["Uptime"].config(text=f"{h}h {m%60}m" if h>0 else f"{m}m {seg%60}s")

    def _actualizar_graficas(self):
        datos_t = db.get_historial_por_periodo(1, self._periodo_graf)
        if datos_t:
            xs = [r[0] for r in datos_t]
            ys = [float(r[1]) for r in datos_t]
            self.ax_temp.clear()
            self.ax_temp.plot(xs, ys, color="#2c3e50", linewidth=1.5)
            self.ax_temp.set_facecolor("#f8f8f8")
            self.ax_temp.tick_params(labelsize=7)
            self.canvas_temp.draw()

        datos_h = db.get_historial_por_periodo(2, self._periodo_graf)
        if datos_h:
            xs = [r[0] for r in datos_h]
            ys = [float(r[1]) for r in datos_h]
            self.ax_hum.clear()
            self.ax_hum.plot(xs, ys, color="#2980b9", linewidth=1.5)
            self.ax_hum.set_facecolor("#f8f8f8")
            self.ax_hum.tick_params(labelsize=7)
            self.canvas_hum.draw()

    def _actualizar_stats(self):
        et = db.get_estadisticas(1, self._periodo_graf)
        eh = db.get_estadisticas(2, self._periodo_graf)
        if et:
            self.stats["t_prom"].config(text=f"{et['promedio']}°C")
            self.stats["t_max"].config(text=f"{et['maximo']}°C")
            self.stats["t_min"].config(text=f"{et['minimo']}°C")
        if eh:
            self.stats["h_prom"].config(text=f"{eh['promedio']}%")

    def _cambiar_periodo(self, p):
        self._periodo_graf = p
        self._actualizar_graficas()
        self._actualizar_stats()

    def _toggle(self, id_act):
        if id_act == 1:
            self._estado_led = not self._estado_led
            api.set_actuador(1, self._estado_led)
            db.insertar_estado_actuador(1, self._estado_led)
            self.lbl_led.config(
                text="ON" if self._estado_led else "OFF",
                fg="#27ae60" if self._estado_led else "#e74c3c"
            )
        else:
            self._estado_buz = not self._estado_buz
            api.set_actuador(2, self._estado_buz)
            db.insertar_estado_actuador(2, self._estado_buz)
            self.lbl_buz.config(
                text="ON" if self._estado_buz else "OFF",
                fg="#27ae60" if self._estado_buz else "#e74c3c"
            )

    def _aplicar(self, clave, entry):
        try:
            valor = float(entry.get())
            api.set_parametro(clave, valor)
            fb = self.fb_periodo if clave == "periodo_sensado" else self.fb_umbral
            fb.config(text="Aplicado")
            self.root.after(2000, lambda: fb.config(text=""))
        except ValueError:
            messagebox.showerror("Error", "Valor inválido")

    def on_close(self):
        self._corriendo = False
        self.root.destroy()