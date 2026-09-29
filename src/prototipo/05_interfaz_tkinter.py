# Interfaz de escritorio tipo Wireshark para el prototipo IDS.

from __future__ import annotations

from pathlib import Path
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from inferencia_ids import IDSInferencia


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
LIMITE_PREVISUALIZACION = 10_000


class Tooltip:
    """Mostrar una descripción breve al pasar el cursor sobre un control."""

    def __init__(self, widget: tk.Widget, texto: str) -> None:
        self.widget = widget
        self.texto = texto
        self.ventana: tk.Toplevel | None = None
        self.identificador: str | None = None
        widget.bind("<Enter>", self.programar, add="+")
        widget.bind("<Leave>", self.ocultar, add="+")

    def programar(self, _evento=None) -> None:
        self.ocultar()
        self.identificador = self.widget.after(500, self.mostrar)

    def mostrar(self) -> None:
        if self.ventana is not None:
            return
        self.ventana = tk.Toplevel(self.widget)
        self.ventana.wm_overrideredirect(True)
        self.ventana.configure(bg="#0f172a")
        posicion_x = self.widget.winfo_rootx() + self.widget.winfo_width() + 6
        posicion_y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.ventana.geometry(f"+{posicion_x}+{posicion_y}")
        tk.Label(
            self.ventana,
            text=self.texto,
            bg="#0f172a",
            fg="white",
            padx=7,
            pady=4,
        ).pack()

    def ocultar(self, _evento=None) -> None:
        if self.identificador is not None:
            self.widget.after_cancel(self.identificador)
            self.identificador = None
        if self.ventana is not None:
            self.ventana.destroy()
            self.ventana = None


class InterfazIDS:
    """Ventana principal del IDS por lotes."""

    def __init__(self, ventana: tk.Tk) -> None:
        self.ventana = ventana
        self.ventana.title("IDS ML | Analizador de flujos")
        self.ventana.geometry("1280x760")
        self.ventana.minsize(960, 600)

        self.motor = IDSInferencia()
        self.ruta_archivo: Path | None = None
        self.datos_entrada: pd.DataFrame | None = None
        self.resultados: pd.DataFrame | None = None
        self.estado_var = tk.StringVar(value="LISTO PARA ANALIZAR")
        self.indicadores: dict[str, tk.StringVar] = {}

        self._crear_estilos()
        self._crear_interfaz()

    def _crear_estilos(self) -> None:
        estilo = ttk.Style(self.ventana)
        estilo.theme_use("clam")
        self.ventana.configure(bg="#f3f6fb")
        estilo.configure("App.TFrame", background="#f3f6fb")
        estilo.configure("Surface.TFrame", background="#ffffff")
        estilo.configure("Toolbar.TFrame", background="#172554")
        estilo.configure(
            "Action.TButton",
            background="#4f46e5",
            foreground="#ffffff",
            borderwidth=0,
            padding=(14, 8),
            font=("Segoe UI", 10, "bold"),
        )
        estilo.map(
            "Action.TButton",
            background=[("disabled", "#c7d2fe"), ("active", "#4338ca")],
            foreground=[("disabled", "#eef2ff"), ("active", "#ffffff")],
        )
        estilo.configure(
            "Secondary.TButton",
            background="#e0e7ff",
            foreground="#3730a3",
            borderwidth=0,
            padding=(12, 8),
            font=("Segoe UI", 10, "bold"),
        )
        estilo.map("Secondary.TButton", background=[("active", "#c7d2fe")])
        estilo.configure(
            "Filter.TEntry",
            fieldbackground="#f8fafc",
            foreground="#1e293b",
            padding=7,
        )
        estilo.configure(
            "File.TLabel",
            background="#eef2ff",
            foreground="#3730a3",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 9),
        )
        estilo.configure(
            "Section.TLabel",
            background="#ffffff",
            foreground="#172554",
            font=("Segoe UI", 11, "bold"),
        )
        estilo.configure(
            "Status.TLabel",
            background="#172554",
            foreground="#e0e7ff",
            font=("Segoe UI", 9),
        )
        estilo.configure(
            "Treeview",
            background="#ffffff",
            fieldbackground="#ffffff",
            foreground="#26334d",
            rowheight=29,
            font=("Segoe UI", 9),
        )
        estilo.configure(
            "Treeview.Heading",
            background="#e0e7ff",
            foreground="#312e81",
            font=("Segoe UI", 9, "bold"),
            padding=(7, 7),
        )
        estilo.map(
            "Treeview",
            background=[("selected", "#c7d2fe")],
            foreground=[("selected", "#1e1b4b")],
        )

    def _crear_interfaz(self) -> None:
        cabecera = tk.Frame(self.ventana, bg="#172554", padx=24, pady=18)
        cabecera.pack(fill="x")
        tk.Label(
            cabecera,
            text="SENTINEL IDS",
            bg="#172554",
            fg="#c4b5fd",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")
        fila_cabecera = tk.Frame(cabecera, bg="#172554")
        fila_cabecera.pack(fill="x", pady=(2, 0))
        tk.Label(
            fila_cabecera,
            text="Analizador inteligente de flujos de red",
            bg="#172554",
            fg="#ffffff",
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left")
        tk.Label(
            fila_cabecera,
            textvariable=self.estado_var,
            bg="#312e81",
            fg="#ddd6fe",
            padx=12,
            pady=5,
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right", pady=3)
        tk.Label(
            cabecera,
            text="Carga un archivo, analiza sus flujos y revisa las alertas detectadas.",
            bg="#172554",
            fg="#bfdbfe",
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        contenido = ttk.Frame(self.ventana, style="App.TFrame", padding=(16, 14, 16, 8))
        contenido.pack(fill="both", expand=True)

        barra = ttk.Frame(contenido, style="Surface.TFrame", padding=(14, 12))
        barra.pack(fill="x", pady=(0, 10))
        boton_abrir = ttk.Button(
            barra,
            text="Abrir archivo",
            command=self.seleccionar_archivo,
            style="Action.TButton",
        )
        boton_abrir.pack(side="left", padx=3)
        Tooltip(boton_abrir, "Abrir archivo CSV o Parquet")
        self.boton_analizar = ttk.Button(
            barra,
            text="Analizar flujos",
            command=self.analizar_archivo,
            state="disabled",
            style="Secondary.TButton",
        )
        self.boton_analizar.pack(side="left", padx=3)
        Tooltip(self.boton_analizar, "Analizar los flujos seleccionados")
        boton_limpiar = ttk.Button(
            barra,
            text="Limpiar",
            command=self.limpiar,
            style="Secondary.TButton",
        )
        boton_limpiar.pack(side="left", padx=3)
        Tooltip(boton_limpiar, "Limpiar resultados y detalles")

        ttk.Separator(barra, orient="vertical").pack(side="left", fill="y", padx=14)
        ttk.Label(barra, text="Buscar en resultados", style="Section.TLabel").pack(
            side="left", padx=(0, 8)
        )
        self.filtro = tk.StringVar()
        entrada_filtro = ttk.Entry(
            barra, textvariable=self.filtro, width=30, style="Filter.TEntry"
        )
        entrada_filtro.pack(side="left", padx=3)
        entrada_filtro.bind("<Return>", lambda _evento: self.aplicar_filtro())
        boton_filtro = ttk.Button(
            barra, text="Filtrar", command=self.aplicar_filtro, style="Secondary.TButton"
        )
        boton_filtro.pack(side="left", padx=3)
        Tooltip(boton_filtro, "Aplicar filtro de visualización")

        self.etiqueta_archivo = ttk.Label(
            contenido,
            text="Ningún archivo seleccionado",
            style="File.TLabel",
        )
        self.etiqueta_archivo.pack(fill="x")

        tarjetas = tk.Frame(contenido, bg="#f3f6fb")
        tarjetas.pack(fill="x", pady=(12, 14))
        for columna in range(4):
            tarjetas.columnconfigure(columna, weight=1, uniform="tarjetas")
        self._crear_tarjeta(tarjetas, 0, "Flujos revisados", "total", "#4f46e5")
        self._crear_tarjeta(tarjetas, 1, "Tráfico benigno", "benign", "#0f9d78")
        self._crear_tarjeta(tarjetas, 2, "Amenazas detectadas", "malicious", "#e05252")
        self._crear_tarjeta(tarjetas, 3, "Datos con error", "errores", "#d97706")

        panel_principal = ttk.PanedWindow(contenido, orient="vertical")
        panel_principal.pack(fill="both", expand=True)

        panel_tabla = ttk.Frame(panel_principal, style="Surface.TFrame", padding=8)
        panel_detalle = ttk.Frame(panel_principal, style="Surface.TFrame", padding=8)
        panel_principal.add(panel_tabla, weight=3)
        panel_principal.add(panel_detalle, weight=1)

        columnas = (
            "No.",
            "Predicción",
            "Confianza",
            "Alerta",
            "Estado",
            "Etiqueta real",
            "Timestamp",
            "Flow ID",
            "Source IP",
            "Destination IP",
            "Protocol",
        )
        self.tabla = ttk.Treeview(
            panel_tabla,
            columns=columnas,
            show="headings",
            selectmode="browse",
        )
        anchos = {
            "No.": 60,
            "Predicción": 115,
            "Confianza": 90,
            "Alerta": 100,
            "Estado": 110,
            "Etiqueta real": 110,
            "Timestamp": 150,
            "Flow ID": 180,
            "Source IP": 125,
            "Destination IP": 125,
            "Protocol": 75,
        }
        for columna in columnas:
            self.tabla.heading(columna, text=columna)
            self.tabla.column(columna, width=anchos[columna], anchor="center")
        self.tabla.tag_configure("malicioso", background="#fee2e2", foreground="#991b1b")
        self.tabla.tag_configure("benigno", background="#dcfce7", foreground="#166534")
        self.tabla.tag_configure("error", background="#fef3c7", foreground="#92400e")
        self.tabla.bind("<<TreeviewSelect>>", self.mostrar_detalle)

        barra_vertical = ttk.Scrollbar(
            panel_tabla, orient="vertical", command=self.tabla.yview
        )
        barra_horizontal = ttk.Scrollbar(
            panel_tabla, orient="horizontal", command=self.tabla.xview
        )
        self.tabla.configure(
            yscrollcommand=barra_vertical.set,
            xscrollcommand=barra_horizontal.set,
        )
        self.tabla.grid(row=0, column=0, sticky="nsew")
        barra_vertical.grid(row=0, column=1, sticky="ns")
        barra_horizontal.grid(row=1, column=0, sticky="ew")
        panel_tabla.rowconfigure(0, weight=1)
        panel_tabla.columnconfigure(0, weight=1)

        ttk.Label(panel_detalle, text="Detalles del flujo seleccionado", style="Section.TLabel").pack(
            anchor="w", padx=4, pady=(2, 6)
        )
        contenedor_detalle = ttk.Frame(panel_detalle, style="Surface.TFrame")
        contenedor_detalle.pack(fill="both", expand=True, padx=4, pady=4)
        self.detalle = tk.Text(
            contenedor_detalle,
            height=8,
            wrap="none",
            state="disabled",
            bg="#f8fafc",
            fg="#334155",
            insertbackground="#4f46e5",
            relief="flat",
            padx=12,
            pady=10,
            font=("Consolas", 9),
        )
        barra_detalle = ttk.Scrollbar(
            contenedor_detalle, orient="vertical", command=self.detalle.yview
        )
        self.detalle.configure(yscrollcommand=barra_detalle.set)
        self.detalle.pack(side="left", fill="both", expand=True)
        barra_detalle.pack(side="right", fill="y")

        self.barra_estado = ttk.Label(
            contenido,
            text="Listo | Total: 0 | Benigno: 0 | Malicioso: 0 | Errores: 0",
            style="Status.TLabel",
            padding=(12, 7),
        )
        self.barra_estado.pack(fill="x", pady=(8, 0))

    def _crear_tarjeta(
        self, contenedor: tk.Frame, columna: int, titulo: str, clave: str, color: str
    ) -> None:
        tarjeta = tk.Frame(
            contenedor,
            bg="#ffffff",
            highlightbackground="#e2e8f0",
            highlightthickness=1,
            padx=14,
            pady=11,
        )
        tarjeta.grid(row=0, column=columna, sticky="nsew", padx=4)
        tk.Frame(tarjeta, bg=color, height=4).pack(fill="x", pady=(0, 8))
        tk.Label(
            tarjeta,
            text=titulo.upper(),
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        valor = tk.StringVar(value="0")
        self.indicadores[clave] = valor
        tk.Label(
            tarjeta,
            textvariable=valor,
            bg="#ffffff",
            fg="#172554",
            font=("Segoe UI", 20, "bold"),
        ).pack(anchor="w", pady=(2, 0))

    def seleccionar_archivo(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo de flujos",
            initialdir=RAIZ_PROYECTO / "data",
            filetypes=[("CSV y Parquet", "*.csv *.parquet"), ("Todos", "*.*")],
        )
        if ruta:
            self.ruta_archivo = Path(ruta)
            self.etiqueta_archivo.configure(text=f"Archivo seleccionado - {self.ruta_archivo}")
            self.boton_analizar.configure(state="normal")
            self.estado_var.set("ARCHIVO CARGADO")
            self.barra_estado.configure(text="Archivo listo para analizar")

    def analizar_archivo(self) -> None:
        if self.ruta_archivo is None:
            return
        self.boton_analizar.configure(state="disabled")
        self.barra_estado.configure(text="Analizando flujos...")
        self.estado_var.set("ANALIZANDO")
        threading.Thread(target=self._analizar_en_segundo_plano, daemon=True).start()

    def _analizar_en_segundo_plano(self) -> None:
        try:
            ruta_archivo = self.ruta_archivo
            if ruta_archivo is None:
                raise ValueError("No se ha seleccionado un archivo de entrada.")
            datos_entrada = self.motor.cargar_archivo(
                ruta_archivo, LIMITE_PREVISUALIZACION
            )
            resultados = self.motor.clasificar(datos_entrada)
            self.motor.guardar_resultados(resultados)
            self.ventana.after(
                0,
                lambda resultado=resultados, entrada=datos_entrada: self.mostrar_resultados(
                    resultado, entrada
                ),
            )
        except Exception as error:  # pragma: no cover - mostrado en la interfaz
            mensaje_error = str(error)
            self.ventana.after(
                0, lambda mensaje=mensaje_error: self.mostrar_error(mensaje)
            )

    def mostrar_resultados(
        self, resultados: pd.DataFrame, datos_entrada: pd.DataFrame
    ) -> None:
        self.datos_entrada = datos_entrada
        self.resultados = resultados
        self.rellenar_tabla(resultados)
        resumen = self.motor.resumen(resultados)
        self._actualizar_indicadores(resumen)
        self.estado_var.set("ANALISIS COMPLETADO")
        self.barra_estado.configure(
            text=(
                f"Listo | Total: {resumen['total']} | "
                f"Benigno: {resumen['benign']} | "
                f"Malicioso: {resumen['malicious']} | "
                f"Errores: {resumen['errores']}"
            )
        )
        self.boton_analizar.configure(state="normal")

    def _actualizar_indicadores(self, resumen: dict[str, int]) -> None:
        for clave, valor in resumen.items():
            indicador = self.indicadores.get(clave)
            if indicador is not None:
                indicador.set(f"{valor:,}")

    def rellenar_tabla(self, resultados: pd.DataFrame) -> None:
        for elemento in self.tabla.get_children():
            self.tabla.delete(elemento)
        for _, fila in resultados.iterrows():
            valores = []
            for columna in self.tabla["columns"]:
                valor = fila.get(columna, "")
                if columna == "Confianza" and valor != "":
                    valor = f"{float(valor):.4f}"
                valores.append(str(valor))
            if fila.get("Estado") == "ERROR_DATOS":
                etiqueta = "error"
            elif fila.get("Predicción") == "MALICIOUS":
                etiqueta = "malicioso"
            else:
                etiqueta = "benigno"
            self.tabla.insert("", "end", values=valores, tags=(etiqueta,))

    def aplicar_filtro(self) -> None:
        if self.resultados is not None:
            self.rellenar_tabla(self.motor.filtrar(self.resultados, self.filtro.get()))

    def mostrar_detalle(self, _evento=None) -> None:
        seleccion = self.tabla.selection()
        if not seleccion:
            return
        valores = self.tabla.item(seleccion[0], "values")
        resumen = "\n".join(
            f"{columna}: {valor}"
            for columna, valor in zip(self.tabla["columns"], valores)
        )
        lineas = ["Resumen de clasificación", resumen, "", "Características del flujo"]
        if self.datos_entrada is not None:
            try:
                numero_fila = int(valores[0]) - 1
                fila_original = self.datos_entrada.iloc[numero_fila]
                columnas_mostradas = set(fila_original.index)
                for columna, valor in fila_original.items():
                    if pd.isna(valor):
                        valor = ""
                    lineas.append(f"{columna}: {valor}")
                for columna in (
                    "Timestamp",
                    "Flow ID",
                    "Source IP",
                    "Destination IP",
                ):
                    if columna not in columnas_mostradas:
                        lineas.append(f"{columna}: NO DISPONIBLE EN ENTRADA")
            except (IndexError, ValueError):
                lineas.append("No fue posible recuperar el flujo original.")
        detalle = "\n".join(lineas)
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.insert("1.0", detalle)
        self.detalle.configure(state="disabled")

    def mostrar_error(self, mensaje: str) -> None:
        self.barra_estado.configure(text="Error de análisis")
        self.boton_analizar.configure(state="normal")
        self.estado_var.set("ERROR")
        messagebox.showerror("Error del IDS", mensaje)

    def limpiar(self) -> None:
        for elemento in self.tabla.get_children():
            self.tabla.delete(elemento)
        self.datos_entrada = None
        self.resultados = None
        self.filtro.set("")
        self.detalle.configure(state="normal")
        self.detalle.delete("1.0", "end")
        self.detalle.configure(state="disabled")
        for indicador in self.indicadores.values():
            indicador.set("0")
        self.estado_var.set("LISTO PARA ANALIZAR")
        self.barra_estado.configure(
            text="Listo | Total: 0 | Benigno: 0 | Malicioso: 0 | Errores: 0"
        )


def main() -> None:
    ventana = tk.Tk()
    InterfazIDS(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()
