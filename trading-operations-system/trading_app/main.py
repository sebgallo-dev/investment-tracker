from db.conexion import DBConnection
from controller.control_op import ControllerOperaciones
from model.operaciones import Operacion


############ MENU PRINCIPAL ##############
def menu():
    print("\n===== SISTEMA DE OPERACIONES DE TRADING =====")
    print("1) Agregar operacion")
    print("2) Modificar operacion")
    print("3) Eliminar operacion")
    print("4) Ver operacion por ID")
    print("5) Listar todas las operaciones")
    print("6) Ver auditoria (ultimos 50)")
    print("7) Ver resumen mensual")
    print("8) Exportar resumen mensual CSV")
    print("0) Salir")
    return input("Seleccione una opcion: ")


############ PEDIR DATOS AL USUARIO #############
def pedir_operacion(para_modificar=False):
    fecha = input("Fecha (YYYY-MM-DD): ")
    activo = input("Activo (BTC, ETH, etc): ")
    tipo = input("Tipo (Compra/Venta): ")
    precio_entrada = float(input("Precio entrada: "))
    precio_salida = float(input("Precio salida: "))
    if precio_entrada == 0:
        resultado = 0.0
    elif tipo.strip().lower() == "venta":
        resultado = ((precio_entrada - precio_salida) / precio_entrada) * 100
    else:
        resultado = ((precio_salida - precio_entrada) / precio_entrada) * 100

    if para_modificar:
        id_op = int(input("ID de la operacion a modificar: "))

        return Operacion(
            fecha=fecha,
            activo=activo,
            tipo=tipo,
            precio_entrada=precio_entrada,
            precio_salida=precio_salida,
            resultado=resultado,
            id_op=id_op
        )

    return Operacion(
        fecha=fecha,
        activo=activo,
        tipo=tipo,
        precio_entrada=precio_entrada,
        precio_salida=precio_salida,
        resultado=resultado
    )


############### MAIN ##############
def main():
    conexion = DBConnection()
    conexion.crear_base()

    controller = ControllerOperaciones(conexion)

    while True:
        opcion = menu()

        if opcion == "1":
            print("\n--- Agregar operacion ---")
            op = pedir_operacion()
            controller.agregar_operacion(op)
            print("Operacion agregada correctamente.")

        elif opcion == "2":
            print("\n--- Modificar operacion ---")
            op = pedir_operacion(para_modificar=True)
            controller.modificar_operacion(op)
            print("Operacion modificada correctamente.")

        elif opcion == "3":
            print("\n--- Eliminar operacion ---")
            id_op = int(input("ID de la operacion a eliminar: "))
            controller.eliminar_operacion(id_op)
            print("Operacion eliminada correctamente.")

        elif opcion == "4":
            print("\n--- Buscar operacion ---")
            id_op = int(input("ID: "))
            op = controller.obtener_operacion(id_op)

            if op:
                print("\nOperacion encontrada:")
                print(op)
            else:
                print("No existe una operacion con ese ID.")

        elif opcion == "5":
            print("\n--- Listado de operaciones ---")
            lista = controller.listar_operaciones()

            if not lista:
                print("No hay operaciones registradas.")
            else:
                for oper in lista:
                    print(f"ID {oper.id_op} -> {oper}")

        elif opcion == "6":
            print("\n--- Auditoria (ultimos 50) ---")
            registros = controller.listar_auditoria(50)

            if not registros:
                print("No hay registros de auditoria.")
            else:
                for fecha_hora, accion, operacion_id, valor_anterior, valor_nuevo in registros:
                    print(f"{fecha_hora} | {accion} | ID {operacion_id}")
                    print(f"  Anterior: {valor_anterior}")
                    print(f"  Nuevo:    {valor_nuevo}")
                    print("-" * 80)

        elif opcion == "7":
            print("\n--- Resumen mensual ---")
            resumen = controller.resumen_mensual()

            if not resumen:
                print("No hay operaciones para resumir.")
            else:
                for fila in resumen:
                    print(
                        f"{fila['mes']} | Ops: {fila['cantidad_operaciones']} | "
                        f"Win rate: {fila['win_rate']:.2f}% | "
                        f"Promedio: {fila['retorno_promedio_pct']:.2f}% | "
                        f"Mes (compuesto): {fila['retorno_mensual_pct']:.2f}% | "
                        f"Acumulado (compuesto): {fila['retorno_acumulado_pct']:.2f}%"
                    )

        elif opcion == "8":
            print("\n--- Exportar resumen mensual CSV ---")
            ruta = input("Ruta archivo CSV (ej: resumen_mensual.csv): ").strip()

            if not ruta:
                print("No se ingreso ruta. Operacion cancelada.")
            else:
                controller.exportar_resumen_mensual_csv(ruta)
                print(f"Archivo exportado en: {ruta}")

        elif opcion == "0":
            print("Saliendo del sistema...")
            break

        else:
            print("Opcion invalida. Intenta de nuevo.")


if __name__ == "__main__":
    main()
