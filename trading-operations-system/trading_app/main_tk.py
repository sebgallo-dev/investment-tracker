from db.conexion import DBConnection
from controller.control_op import ControllerOperaciones
from view.vista_tk import ViewOperacionesTk
import tkinter as tk

def main():
    conexion = DBConnection()
    conexion.crear_base()

    controller = ControllerOperaciones(conexion)

    root = tk.Tk()
    root.geometry("1000x600")
    root.title("Sistema de Operaciones de Trading")

    ViewOperacionesTk(root, controller)

    root.mainloop()

if __name__ == "__main__":
    main()