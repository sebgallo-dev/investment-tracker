import json
import queue
import socket
import threading
import time
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


HOST = "127.0.0.1"
PORT = 50007
MAX_PUNTOS = 1200

cola_ticks = queue.Queue()
ofi_historial = []
ultimo_tick = {}
def recibir_ticks(stop_event: threading.Event) -> None:
    while not stop_event.is_set():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((HOST, PORT))
                s.settimeout(1)
                print(f"[TCP] Conectado a {HOST}:{PORT}")

                buffer = ""
                while not stop_event.is_set():
                    try:
                        data = s.recv(4096)
                    except socket.timeout:
                        continue

                    if not data:
                        print("[TCP] Servidor desconectado")
                        break

                    buffer += data.decode("utf-8")
                    while "\n" in buffer:
                        linea, buffer = buffer.split("\n", 1)
                        if not linea.strip():
                            continue
                        try:
                            tick = json.loads(linea)
                            cola_ticks.put(tick)
                        except json.JSONDecodeError:
                            pass

        except OSError as e:
            print(f"[TCP] Error de conexion: {e}")

        if not stop_event.is_set():
            time.sleep(2)


def procesar_cola() -> None:
    global ultimo_tick

    procesados = 0
    while procesados < 1000:
        try:
            tick = cola_ticks.get_nowait()
        except queue.Empty:
            break

        ultimo_tick = tick

        if "ofi_total" in tick:
            valor_ofi = float(tick["ofi_total"])
        elif "ofi" in tick:
            valor_ofi = float(tick["ofi"])
        else:
            valor_ofi = 0.0

        ofi_historial.append(valor_ofi)
        if len(ofi_historial) > MAX_PUNTOS:
            ofi_historial.pop(0)

        procesados += 1


fig, ax = plt.subplots(figsize=(10, 6))
linea, = ax.plot([], [], color="tab:blue", linewidth=1.6)
ax.set_title("OFI en tiempo real")
ax.set_xlabel("Ticks")
ax.set_ylabel("OFI acumulado")
ax.grid(True, alpha=0.3)
texto_estado = ax.text(0.01, 0.97, "Esperando datos...", transform=ax.transAxes, va="top")


def animar(_i):
    procesar_cola()

    if not ofi_historial:
        return linea, texto_estado

    y = np.array(ofi_historial, dtype=float)
    x = np.arange(len(y))
    linea.set_data(x, y)

    ax.relim()
    ax.autoscale_view()

    symbol = ultimo_tick.get("symbol", "-")
    price = ultimo_tick.get("price", "-")
    texto_estado.set_text(f"symbol={symbol}  price={price}  ofi_total={y[-1]:.6f}")

    return linea, texto_estado


def main() -> None:
    stop_event = threading.Event()
    hilo_rx = threading.Thread(target=recibir_ticks, args=(stop_event,), daemon=True)
    hilo_rx.start()

    ani = animation.FuncAnimation(fig, animar, interval=250, cache_frame_data=False)

    try:
        plt.show()
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()