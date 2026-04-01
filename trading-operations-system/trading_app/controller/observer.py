class Observer:
    def update(self, event: str, payload: dict):
        raise NotImplementedError("Delegación de actualización")


class SubjectMixin:
    def __init__(self):
        self._observadores = []

    def agregar_observador(self, obs: Observer):
        self._observadores.append(obs)

    def quitar_observador(self, obs: Observer):
        if obs in self._observadores:
            self._observadores.remove(obs)

    def notificar(self, event: str, payload: dict):
        for obs in self._observadores:
            obs.update(event, payload)


class ConsoleObserver(Observer):
    def update(self, event: str, payload: dict):
        ################# salida simple para demostrar el patrón en la consola##################
        print(f"[OBSERVER] evento='{event}' payload={payload}")