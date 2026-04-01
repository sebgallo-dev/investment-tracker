import time
from functools import wraps

def log_accion(nombre):
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[LOG] {nombre} INICIO")
            r = func(*args, **kwargs)
            print(f"[LOG] {nombre} FIN")
            return r
        return wrapper
    return deco

def medir_tiempo(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        r = func(*args, **kwargs)
        t1 = time.perf_counter()
        print(f"[TIME] {func.__name__} {t1-t0:.4f}s")
        return r
    return wrapper