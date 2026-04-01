import json
import socket
import threading
import time
from datetime import datetime, timezone
import websocket


PAR = "pepeusdt"
BINANCE_WS = f"wss://stream.binance.com:9443/ws/{PAR}@trade"

HOST = "0.0.0.0"
PORT = 50007

ofi_acumulado = 0.0
clientes = set()
lock_clientes = threading.Lock()


def calcular_ofi(trade: dict) -> float:
    qty = float(trade["q"])
    buy_agresivo = trade["m"] is False
    return qty if buy_agresivo else -qty


def _quitar_cliente(conn: socket.socket) -> None:
    with lock_clientes:
        if conn in clientes:
            clientes.remove(conn)
    try:
        conn.close()
    except OSError:
        pass


def enviar_a_clientes(payload: dict) -> None:
    linea = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")

    with lock_clientes:
        lista_clientes = list(clientes)

    desconectados = []
    for conn in lista_clientes:
        try:
            conn.sendall(linea)
        except OSError:
            desconectados.append(conn)

    for conn in desconectados:
        _quitar_cliente(conn)


def on_message(_ws, msg: str) -> None:
    global ofi_acumulado

    trade = json.loads(msg)
    ofi_delta = calcular_ofi(trade)
    ofi_acumulado += ofi_delta

    event_ms = int(trade.get("E", int(time.time() * 1000)))
    ts = datetime.fromtimestamp(event_ms / 1000, tz=timezone.utc).isoformat()

    payload = {
        "ts": ts,
        "symbol": trade.get("s", PAR.upper()),
        "price": float(trade["p"]),
        "qty": float(trade["q"]),
        "ofi_delta": ofi_delta,
        "ofi_total": ofi_acumulado,
        "trade_id": int(trade.get("t", 0)),
    }
    enviar_a_clientes(payload)


def on_open(_ws) -> None:
    print(f"[WS] Conectado a Binance: {BINANCE_WS}")


def on_error(_ws, error) -> None:
    print(f"[WS] Error: {error}")


def on_close(_ws, code, reason) -> None:
    print(f"[WS] Socket cerrado code={code} reason={reason}")


def servidor_tcp() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(10)
        print(f"[TCP] OFI server escuchando en 0.0.0.0:{PORT}")

        while True:
            conn, addr = s.accept()
            with lock_clientes:
                clientes.add(conn)
            print(f"[TCP] Cliente conectado: {addr[0]}:{addr[1]}")


def main() -> None:
    hilo_tcp = threading.Thread(target=servidor_tcp, daemon=True)
    hilo_tcp.start()

    while True:
        ws = websocket.WebSocketApp(
            BINANCE_WS,
            on_message=on_message,
            on_open=on_open,
            on_error=on_error,
            on_close=on_close,
        )
        ws.run_forever(ping_interval=20, ping_timeout=10)
        print("[WS] Reintentando conexion en 3 segundos...")
        time.sleep(3)


if __name__ == "__main__":
    main()