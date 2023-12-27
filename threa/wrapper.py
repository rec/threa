import typing as t

from .runnable import Runnable


class Wrapper(Runnable):
    """Duck-type wrapper for runnable things"""

    def __init__(self, wrapped: t.Any) -> None:
        self.wrapped = wrapped
        super().__init__()

    def start(self) -> None:
        super().start()
        if (start := getattr(self.wrapped, 'start', None)) is not None:
            start()

    def stop(self) -> None:
        super().stop()
        if (stop := getattr(self.wrapped, 'stop', None)) is not None:
            stop()

    def join(self, timeout: t.Optional[float] = None) -> None:
        super().join(timeout)
        if (join := getattr(self.wrapped, 'join', None)) is not None:
            join(timeout)
