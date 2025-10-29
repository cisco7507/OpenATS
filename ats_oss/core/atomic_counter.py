import threading

class AtomicCounter:
    """
    A simple thread-safe counter.
    Used to generate unique, sequential step indices when branches
    of a workflow are executing in parallel.
    """
    def __init__(self, initial_value: int = 0):
        self._value = initial_value
        self._lock = threading.Lock()

    def increment(self) -> int:
        """
        Increments the counter by 1 and returns the new value.
        """
        with self._lock:
            self._value += 1
            return self._value

    def get_value(self) -> int:
        """
        Returns the current value of the counter.
        """
        with self._lock:
            return self._value
