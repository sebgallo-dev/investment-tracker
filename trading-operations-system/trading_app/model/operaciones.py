class Operacion:
    def __init__(self, fecha, activo, tipo, precio_entrada, precio_salida, resultado, id_op=None):
        self.id_op = id_op         
        self.fecha = fecha
        self.activo = activo
        self.tipo = tipo
        self.precio_entrada = precio_entrada
        self.precio_salida = precio_salida
        self.resultado = resultado

    def como_tupla(self, incluir_id=False):
        if incluir_id:
            return (
                self.fecha,
                self.activo,
                self.tipo,
                self.precio_entrada,
                self.precio_salida,
                self.resultado,
                self.id_op
            )
        return (
            self.fecha,
            self.activo,
            self.tipo,
            self.precio_entrada,
            self.precio_salida,
            self.resultado
        )

    def __str__(self):
        return (
            f"[{self.activo} - {self.tipo}] Entrada: {self.precio_entrada} | "
            f"Salida: {self.precio_salida} | Resultado: {self.resultado:.2f}%"
        )
