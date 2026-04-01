from db.conexion import DBConnection
from model.operaciones import Operacion
from controller.decorators import log_accion, medir_tiempo
from controller.observer import SubjectMixin, ConsoleObserver
from datetime import datetime
import csv
import json


class ControllerOperaciones(SubjectMixin):
    """
    El controlador principal encargado de relacionar las operaciones a la base de datos SQLite
    """

    def __init__(self, conexion: DBConnection):
        super().__init__() 
        self._conexion = conexion

        self.agregar_observador(ConsoleObserver())

    @staticmethod
    def _calcular_resultado_pct(precio_entrada, precio_salida, tipo):
        if precio_entrada == 0:
            return 0.0
        if (tipo or "").strip().lower() == "venta":
            return ((precio_entrada - precio_salida) / precio_entrada) * 100
        return ((precio_salida - precio_entrada) / precio_entrada) * 100

    @staticmethod
    def _operacion_a_dict(operacion):
        if operacion is None:
            return None
        return {
            "id": operacion.id_op,
            "fecha": operacion.fecha,
            "activo": operacion.activo,
            "tipo": operacion.tipo,
            "precio_entrada": operacion.precio_entrada,
            "precio_salida": operacion.precio_salida,
            "resultado": operacion.resultado,
        }

    @staticmethod
    def _desde_row(row):
        if not row:
            return None
        resultado_pct = ControllerOperaciones._calcular_resultado_pct(row[4], row[5], row[3])
        return Operacion(
            fecha=row[1],
            activo=row[2],
            tipo=row[3],
            precio_entrada=row[4],
            precio_salida=row[5],
            resultado=resultado_pct,
            id_op=row[0]
        )

    def _buscar_operacion_por_id(self, cursor, id_operacion):
        cursor.execute("SELECT * FROM operaciones WHERE id = ?", (id_operacion,))
        row = cursor.fetchone()
        return self._desde_row(row)

    def _registrar_auditoria(self, cursor, accion, id_operacion, valor_anterior, valor_nuevo):
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
                INSERT INTO auditoria_operaciones
                (fecha_hora, accion, operacion_id, valor_anterior, valor_nuevo)
                VALUES (?, ?, ?, ?, ?)
            """,
            (
                fecha_hora,
                accion,
                id_operacion,
                json.dumps(valor_anterior, ensure_ascii=False) if valor_anterior is not None else None,
                json.dumps(valor_nuevo, ensure_ascii=False) if valor_nuevo is not None else None,
            ),
        )



    @log_accion("AGREGAR_OPERACION")
    @medir_tiempo
    def agregar_operacion(self, operacion: Operacion):
        try:
            con = self._conexion.obtener_conexion()
            cursor = con.cursor()
            operacion.resultado = self._calcular_resultado_pct(
                operacion.precio_entrada, operacion.precio_salida, operacion.tipo
            )

            cursor.execute("""
                INSERT INTO operaciones (fecha, activo, tipo, precio_entrada, precio_salida, resultado)
                VALUES (?, ?, ?, ?, ?, ?)
            """, operacion.como_tupla())

            con.commit()

            self.notificar("operacion_agregada", {
                "activo": operacion.activo,
                "tipo": operacion.tipo,
                "resultado": operacion.resultado
            })

        except Exception as e:
            print("Error al agregar operación:", e)
        finally:
            con.close()


    @log_accion("MODIFICAR_OPERACION")
    @medir_tiempo
    def modificar_operacion(self, operacion: Operacion):
        try:
            con = self._conexion.obtener_conexion()
            cursor = con.cursor()
            operacion_anterior = self._buscar_operacion_por_id(cursor, operacion.id_op)
            operacion.resultado = self._calcular_resultado_pct(
                operacion.precio_entrada, operacion.precio_salida, operacion.tipo
            )

            if operacion_anterior is None:
                print("No existe la operación para modificar.")
                return

            cursor.execute("""
                UPDATE operaciones
                SET fecha = ?, activo = ?, tipo = ?, precio_entrada = ?, precio_salida = ?, resultado = ?
                WHERE id = ?
            """, (
                operacion.fecha,
                operacion.activo,
                operacion.tipo,
                operacion.precio_entrada,
                operacion.precio_salida,
                operacion.resultado,
                operacion.id_op,
            ))

            self._registrar_auditoria(
                cursor,
                "MODIFICAR",
                operacion.id_op,
                self._operacion_a_dict(operacion_anterior),
                self._operacion_a_dict(operacion),
            )

            con.commit()

            self.notificar("operacion_modificada", {
                "id": operacion.id_op,
                "activo": operacion.activo,
                "tipo": operacion.tipo,
                "resultado": operacion.resultado
            })

        except Exception as e:
            print("Error al modificar operación:", e)
        finally:
            con.close()


    @log_accion("ELIMINAR_OPERACION")
    @medir_tiempo
    def eliminar_operacion(self, id_operacion):
        try:
            con = self._conexion.obtener_conexion()
            cursor = con.cursor()
            operacion_anterior = self._buscar_operacion_por_id(cursor, id_operacion)

            if operacion_anterior is None:
                print("No existe la operación para eliminar.")
                return

            cursor.execute("DELETE FROM operaciones WHERE id = ?", (id_operacion,))

            self._registrar_auditoria(
                cursor,
                "ELIMINAR",
                id_operacion,
                self._operacion_a_dict(operacion_anterior),
                None,
            )

            con.commit()

            self.notificar("operacion_eliminada", {"id": id_operacion})

        except Exception as e:
            print("Error al eliminar operación:", e)
        finally:
            con.close()



    def obtener_operacion(self, id_operacion):
        con = self._conexion.obtener_conexion()
        cursor = con.cursor()

        cursor.execute("SELECT * FROM operaciones WHERE id = ?", (id_operacion,))
        row = cursor.fetchone()
        con.close()
        return self._desde_row(row)


    def listar_operaciones(self):
        con = self._conexion.obtener_conexion()
        cursor = con.cursor()

        cursor.execute("SELECT * FROM operaciones ORDER BY id DESC")
        rows = cursor.fetchall()
        con.close()

        operaciones = []
        for row in rows:
            operaciones.append(self._desde_row(row))
        return operaciones

    def listar_auditoria(self, limite=50):
        con = self._conexion.obtener_conexion()
        cursor = con.cursor()

        cursor.execute(
            """
                SELECT fecha_hora, accion, operacion_id, valor_anterior, valor_nuevo
                FROM auditoria_operaciones
                ORDER BY id DESC
                LIMIT ?
            """,
            (limite,),
        )
        rows = cursor.fetchall()
        con.close()
        return rows



    def rentabilidad_acumulada(self):
        con = self._conexion.obtener_conexion()
        cursor = con.cursor()
        expr_retorno_pct = """
            CASE
                WHEN precio_entrada = 0 THEN 0
                WHEN lower(tipo) = 'venta' THEN ((precio_entrada - precio_salida) / precio_entrada) * 100.0
                ELSE ((precio_salida - precio_entrada) / precio_entrada) * 100.0
            END
        """
        cursor.execute(f"SELECT {expr_retorno_pct} FROM operaciones ORDER BY id")
        rendimiento = 1.0
        for (retorno_pct,) in cursor.fetchall():
            rendimiento *= 1 + (retorno_pct or 0) / 100
        con.close()
        return (rendimiento - 1) * 100


    @log_accion("RESUMEN_ESTADISTICO")
    @medir_tiempo
    def resumen_estadistico(self):
        con = self._conexion.obtener_conexion()
        cursor = con.cursor()

        resumen = {}
        expr_retorno_pct = """
            CASE
                WHEN precio_entrada = 0 THEN 0
                WHEN lower(tipo) = 'venta' THEN ((precio_entrada - precio_salida) / precio_entrada) * 100.0
                ELSE ((precio_salida - precio_entrada) / precio_entrada) * 100.0
            END
        """

        try:
            cursor.execute("BEGIN")

            cursor.execute("SELECT COUNT(*) FROM operaciones")
            resumen["total_operaciones"] = cursor.fetchone()[0]

            cursor.execute(f"SELECT COUNT(*) FROM operaciones WHERE {expr_retorno_pct} > 0")
            ganadoras = cursor.fetchone()[0]

            resumen["win_rate"] = (
                (ganadoras / resumen["total_operaciones"]) * 100
                if resumen["total_operaciones"] > 0 else 0
            )

            cursor.execute(f"SELECT AVG({expr_retorno_pct}) FROM operaciones")
            resumen["promedio_retorno_pct"] = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT MAX({expr_retorno_pct}) FROM operaciones")
            resumen["mejor_retorno_pct"] = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT MIN({expr_retorno_pct}) FROM operaciones")
            resumen["peor_retorno_pct"] = cursor.fetchone()[0] or 0

            cursor.execute(f"SELECT {expr_retorno_pct} FROM operaciones ORDER BY id")
            rendimiento = 1.0
            for (retorno_pct,) in cursor.fetchall():
                rendimiento *= 1 + (retorno_pct or 0) / 100
            resumen["rentabilidad_acumulada_pct"] = (rendimiento - 1) * 100

            con.commit()

            self.notificar("resumen_generado", {
                "total_operaciones": resumen.get("total_operaciones", 0),
                "rentabilidad_acumulada_pct": resumen.get("rentabilidad_acumulada_pct", 0)
            })

        except Exception as e:
            con.rollback()
            print("Error en resumen estadístico:", e)

        finally:
            con.close()

        return resumen

    @log_accion("RESUMEN_MENSUAL")
    @medir_tiempo
    def resumen_mensual(self):
        con = self._conexion.obtener_conexion()
        cursor = con.cursor()
        resumen = []
        expr_retorno_pct = """
            CASE
                WHEN precio_entrada = 0 THEN 0
                WHEN lower(tipo) = 'venta' THEN ((precio_entrada - precio_salida) / precio_entrada) * 100.0
                ELSE ((precio_salida - precio_entrada) / precio_entrada) * 100.0
            END
        """

        cursor.execute(
            f"""
                SELECT
                    strftime('%Y-%m', fecha) AS mes,
                    {expr_retorno_pct} AS retorno_pct
                FROM operaciones
                ORDER BY mes, id
            """
        )
        rows = cursor.fetchall()
        con.close()

        mes_actual = None
        cantidad = 0
        ganadoras = 0
        suma_retorno = 0.0
        factor_mes = 1.0
        factor_acumulado = 1.0

        for mes, retorno_pct in rows:
            retorno_pct = retorno_pct or 0

            if mes_actual is None:
                mes_actual = mes

            if mes != mes_actual:
                resumen.append(
                    {
                        "mes": mes_actual,
                        "cantidad_operaciones": cantidad,
                        "win_rate": (ganadoras / cantidad) * 100 if cantidad else 0,
                        "retorno_promedio_pct": (suma_retorno / cantidad) if cantidad else 0,
                        "retorno_mensual_pct": (factor_mes - 1) * 100,
                        "retorno_acumulado_pct": (factor_acumulado - 1) * 100,
                    }
                )
                mes_actual = mes
                cantidad = 0
                ganadoras = 0
                suma_retorno = 0.0
                factor_mes = 1.0

            cantidad += 1
            if retorno_pct > 0:
                ganadoras += 1
            suma_retorno += retorno_pct
            factor_mes *= 1 + retorno_pct / 100
            factor_acumulado *= 1 + retorno_pct / 100

        if mes_actual is not None:
            resumen.append(
                {
                    "mes": mes_actual,
                    "cantidad_operaciones": cantidad,
                    "win_rate": (ganadoras / cantidad) * 100 if cantidad else 0,
                    "retorno_promedio_pct": (suma_retorno / cantidad) if cantidad else 0,
                    "retorno_mensual_pct": (factor_mes - 1) * 100,
                    "retorno_acumulado_pct": (factor_acumulado - 1) * 100,
                }
            )

        return resumen

    @log_accion("EXPORTAR_RESUMEN_MENSUAL_CSV")
    @medir_tiempo
    def exportar_resumen_mensual_csv(self, ruta_archivo):
        resumen = self.resumen_mensual()

        def fmt_pct(valor):
            return f"{valor:.2f}%".replace(".", ",")

        with open(ruta_archivo, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                [
                    "Mes",
                    "Operaciones",
                    "Win rate",
                    "Retorno promedio",
                    "Retorno mensual compuesto",
                    "Retorno acumulado compuesto",
                ]
            )

            for fila in resumen:
                writer.writerow(
                    [
                        fila["mes"],
                        fila["cantidad_operaciones"],
                        fmt_pct(fila["win_rate"]),
                        fmt_pct(fila["retorno_promedio_pct"]),
                        fmt_pct(fila["retorno_mensual_pct"]),
                        fmt_pct(fila["retorno_acumulado_pct"]),
                    ]
                )


    @log_accion("RESETEAR_BASE")
    @medir_tiempo
    def resetear_base(self):
        try:
            con = self._conexion.obtener_conexion()
            cursor = con.cursor()

            cursor.execute("DELETE FROM operaciones")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='operaciones'")

            con.commit()

            self.notificar("base_reseteada", {})

        except Exception as e:
            print("Error al resetear la base:", e)
        finally:
            con.close()
