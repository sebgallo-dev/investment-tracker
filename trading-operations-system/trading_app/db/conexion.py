#----BASE DE DATOS-----#
"""
Este archivo se encarga de crear y conectar la base de datos.
Acá se arma la tabla y después el resto del programa usa esta conexión.
"""

import sqlite3


class DBConnection:
    """
    Clase simple para manejar la conexión con el archivo db.
    """

    def __init__(self, ruta="trading.db"):
        self._ruta = ruta


    def crear_base(self):
        """
        Crea la tabla principal si no existe.
        Se usa try/except por si pasa algún error.
        """
        try:
            conexion = sqlite3.connect(self._ruta)
            cursor = conexion.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS operaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    activo TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    precio_entrada REAL NOT NULL,
                    precio_salida REAL NOT NULL,
                    resultado REAL NOT NULL
                );
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auditoria_operaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_hora TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    operacion_id INTEGER,
                    valor_anterior TEXT,
                    valor_nuevo TEXT
                );
            ''')

            conexion.commit()

        except Exception as e:
            print("Error al crear la base de datos:", e)

        finally:
            conexion.close()

    def obtener_conexion(self):
        """
        Devuelve una conexión nueva a la base de datos.
        Se usa en el controlador
        """
        return sqlite3.connect(self._ruta)


if __name__ == "__main__":
    pass
