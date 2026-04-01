import tkinter as tk
from functools import wraps
from tkinter import ttk, messagebox, filedialog

from model.operaciones import Operacion


def requiere_validacion(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.validar():
            return
        return func(self, *args, **kwargs)

    return wrapper


def refrescar_y_notificar(mensaje):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            resultado = func(self, *args, **kwargs)
            if resultado is False:
                return
            self.actualizar_tabla()
            messagebox.showinfo("OK", mensaje)
            return resultado

        return wrapper

    return decorator


class ViewOperacionesTk:
    def __init__(self, root, controller):
        self.controller = controller
        self.root = root
        self.root.title("Gestor de Operaciones de Trading")

        frame_form = tk.Frame(self.root, padx=10, pady=10)
        frame_form.grid(row=0, column=0, sticky="nw")

        tk.Label(frame_form, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, sticky="w")
        self.entry_fecha = tk.Entry(frame_form)
        self.entry_fecha.grid(row=0, column=1)

        tk.Label(frame_form, text="Activo:").grid(row=1, column=0, sticky="w")
        self.entry_activo = tk.Entry(frame_form)
        self.entry_activo.grid(row=1, column=1)

        tk.Label(frame_form, text="Tipo:").grid(row=2, column=0, sticky="w")
        self.combo_tipo = ttk.Combobox(frame_form, values=["Compra", "Venta"], state="readonly")
        self.combo_tipo.grid(row=2, column=1)

        tk.Label(frame_form, text="Precio Entrada:").grid(row=3, column=0, sticky="w")
        self.entry_precio_entrada = tk.Entry(frame_form)
        self.entry_precio_entrada.grid(row=3, column=1)

        tk.Label(frame_form, text="Precio Salida:").grid(row=4, column=0, sticky="w")
        self.entry_precio_salida = tk.Entry(frame_form)
        self.entry_precio_salida.grid(row=4, column=1)

########### Botones ###########
        btn_frame = tk.Frame(frame_form, pady=10)
        btn_frame.grid(row=5, column=0, columnspan=2)

        tk.Button(btn_frame, text="Agregar", command=self.agregar).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Modificar", command=self.modificar).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Eliminar", command=self.eliminar).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Estad\u00edsticas", command=self.mostrar_resumen).grid(
            row=0, column=3, padx=5
        )
        tk.Button(btn_frame, text="Resumen mensual", command=self.mostrar_resumen_mensual).grid(
            row=1, column=0, padx=5, pady=5
        )
        tk.Button(btn_frame, text="Exportar CSV", command=self.exportar_resumen_mensual_csv).grid(
            row=1, column=1, padx=5, pady=5
        )
        tk.Button(btn_frame, text="Auditor\u00eda", command=self.mostrar_auditoria).grid(
            row=1, column=2, padx=5, pady=5
        )

########### TABLA ###########
        frame_tabla = tk.Frame(self.root)
        frame_tabla.grid(row=0, column=1, padx=10, pady=10)

        columnas = ("id", "fecha", "activo", "tipo", "entrada", "salida", "resultado")
        self.tabla = ttk.Treeview(frame_tabla, columns=columnas, show="headings", height=20)

        for col in columnas:
            self.tabla.heading(col, text=col.capitalize())
        self.tabla.heading("resultado", text="Resultado (%)")

        self.tabla.pack()

        self.label_rentabilidad = tk.Label(
            frame_tabla, text="Rentabilidad acumulada: 0.00 %", font=("Arial", 12, "bold")
        )
        self.label_rentabilidad.pack(pady=10)

        self.tabla.bind("<ButtonRelease-1>", self.cargar_desde_tabla)

        self.actualizar_tabla()

########### FUNCIONES ###########
    def validar(self):
        if self.entry_fecha.get() == "":
            messagebox.showerror("Error", "Falta la fecha.")
            return False

        if self.entry_activo.get() == "":
            messagebox.showerror("Error", "Falta el activo.")
            return False

        if self.combo_tipo.get() not in ["Compra", "Venta"]:
            messagebox.showerror("Error", "Seleccion\u00e1 un tipo v\u00e1lido.")
            return False

        try:
            float(self.entry_precio_entrada.get())
            float(self.entry_precio_salida.get())
        except ValueError:
            messagebox.showerror("Error", "Precios inv\u00e1lidos.")
            return False

        return True

    def obtener_operacion(self, incluir_id=False):
        fecha = self.entry_fecha.get()
        activo = self.entry_activo.get()
        tipo = self.combo_tipo.get()
        precio_entrada = float(self.entry_precio_entrada.get())
        precio_salida = float(self.entry_precio_salida.get())
        if precio_entrada == 0:
            resultado = 0.0
        elif tipo == "Venta":
            resultado = ((precio_entrada - precio_salida) / precio_entrada) * 100
        else:
            resultado = ((precio_salida - precio_entrada) / precio_entrada) * 100

        id_op = None
        if incluir_id:
            sel = self.tabla.selection()
            if not sel:
                messagebox.showerror("Error", "Seleccion\u00e1 una operaci\u00f3n.")
                return None
            id_op = self.tabla.item(sel)["values"][0]

        return Operacion(
            fecha=fecha,
            activo=activo,
            tipo=tipo,
            precio_entrada=precio_entrada,
            precio_salida=precio_salida,
            resultado=resultado,
            id_op=id_op,
        )

    @requiere_validacion
    @refrescar_y_notificar("Operaci\u00f3n agregada.")
    def agregar(self):
        oper = self.obtener_operacion()
        self.controller.agregar_operacion(oper)

    @requiere_validacion
    @refrescar_y_notificar("Operaci\u00f3n modificada.")
    def modificar(self):
        oper = self.obtener_operacion(incluir_id=True)
        if oper is None:
            return False
        self.controller.modificar_operacion(oper)

    @refrescar_y_notificar("Operaci\u00f3n eliminada.")
    def eliminar(self):
        sel = self.tabla.selection()
        if not sel:
            messagebox.showerror("Error", "Seleccion\u00e1 una operaci\u00f3n.")
            return False
        id_op = self.tabla.item(sel)["values"][0]
        self.controller.eliminar_operacion(id_op)

    def actualizar_tabla(self):
        for row in self.tabla.get_children():
            self.tabla.delete(row)

        for op in self.controller.listar_operaciones():
            self.tabla.insert(
                "",
                tk.END,
                values=(
                    op.id_op,
                    op.fecha,
                    op.activo,
                    op.tipo,
                    op.precio_entrada,
                    op.precio_salida,
                    f"{op.resultado:.2f}%",
                ),
            )

        self.actualizar_rentabilidad()

    def actualizar_rentabilidad(self):
        operaciones = self.controller.listar_operaciones()

        if not operaciones:
            self.label_rentabilidad.config(text="Rentabilidad acumulada: 0.00 %")
            return

        rendimiento = 1.0

        for op in operaciones:
            rendimiento *= 1 + (op.resultado / 100)

        rent_final = (rendimiento - 1) * 100
        self.label_rentabilidad.config(text=f"Rentabilidad acumulada: {rent_final:.2f} %")

    def cargar_desde_tabla(self, event):
        sel = self.tabla.selection()
        if not sel:
            return

        data = self.tabla.item(sel)["values"]

        self.entry_fecha.delete(0, tk.END)
        self.entry_fecha.insert(0, data[1])

        self.entry_activo.delete(0, tk.END)
        self.entry_activo.insert(0, data[2])

        self.combo_tipo.set(data[3])

        self.entry_precio_entrada.delete(0, tk.END)
        self.entry_precio_entrada.insert(0, data[4])

        self.entry_precio_salida.delete(0, tk.END)
        self.entry_precio_salida.insert(0, data[5])

    def mostrar_resumen(self):
        resumen = self.controller.resumen_estadistico()

        msg = (
            f"Total operaciones: {resumen['total_operaciones']}\n"
            f"Win rate: {resumen['win_rate']:.2f}%\n"
            f"Retorno promedio por operaci\u00f3n: {resumen['promedio_retorno_pct']:.2f}%\n"
            f"Mejor retorno: {resumen['mejor_retorno_pct']:.2f}%\n"
            f"Peor retorno: {resumen['peor_retorno_pct']:.2f}%\n"
            f"Rentabilidad acumulada: {resumen['rentabilidad_acumulada_pct']:.2f}%"
        )

        messagebox.showinfo("Resumen Estad\u00edstico", msg)

    def mostrar_resumen_mensual(self):
        resumen = self.controller.resumen_mensual()

        if not resumen:
            messagebox.showinfo("Resumen mensual", "No hay operaciones para resumir.")
            return

        lineas = []
        for fila in resumen:
            lineas.append(
                f"{fila['mes']} | Ops: {fila['cantidad_operaciones']} | "
                f"Win rate: {fila['win_rate']:.2f}% | "
                f"Promedio: {fila['retorno_promedio_pct']:.2f}% | "
                f"Mes (compuesto): {fila['retorno_mensual_pct']:.2f}% | "
                f"Acumulado (compuesto): {fila['retorno_acumulado_pct']:.2f}%"
            )

        messagebox.showinfo("Resumen mensual", "\n".join(lineas))

    def exportar_resumen_mensual_csv(self):
        ruta = filedialog.asksaveasfilename(
            title="Guardar resumen mensual",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialfile="resumen_mensual_trading.csv",
        )

        if not ruta:
            return

        try:
            self.controller.exportar_resumen_mensual_csv(ruta)
            messagebox.showinfo("Exportaci\u00f3n", f"Archivo exportado en:\n{ruta}")
        except PermissionError:
            messagebox.showerror(
                "Error de permisos",
                "No se pudo guardar el archivo.\n"
                "Posibles causas:\n"
                "- El CSV est\u00e1 abierto en Excel.\n"
                "- La carpeta elegida no tiene permisos de escritura.\n\n"
                "Cerr\u00e1 el archivo si est\u00e1 abierto y prob\u00e1 con otro nombre o carpeta.",
            )
        except OSError as e:
            messagebox.showerror(
                "Error al exportar",
                f"No se pudo guardar el archivo:\n{e}",
            )

    def mostrar_auditoria(self):
        registros = self.controller.listar_auditoria(50)

        if not registros:
            messagebox.showinfo("Auditor\u00eda", "No hay registros de auditor\u00eda.")
            return

        lineas = []
        for fecha_hora, accion, operacion_id, valor_anterior, valor_nuevo in registros:
            lineas.append(
                f"{fecha_hora} | {accion} | ID {operacion_id}\n"
                f"Anterior: {valor_anterior}\n"
                f"Nuevo: {valor_nuevo}\n"
            )

        messagebox.showinfo("Auditor\u00eda (ultimos 50)", "\n".join(lineas))
