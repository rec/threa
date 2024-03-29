import dataclasses as dc
import logging
import typing as t
from functools import cached_property
from queue import Empty, Queue

from .runnable import Runnable
from .thread import ExceptionHandler, HasThread, IsLog

_SENTINEL_MESSAGE = object()
T = t.TypeVar('T')


class HasRunnables(Runnable):
    """Collect zero or more Runnable into one"""

    runnables: t.Sequence[Runnable]

    def start(self) -> None:
        for r in self.runnables:
            r.running.on_set.append(self._on_start)
            r.stopped.on_set.append(self._on_stop)
            r.start()

    def stop(self) -> None:
        self.running.clear()
        for r in reversed(self.runnables):
            r.stop()

    def finish(self) -> None:
        for r in reversed(self.runnables):
            r.finish()

    def join(self, timeout: t.Optional[float] = None) -> None:
        for r in reversed(self.runnables):
            r.join(timeout)

    def _on_start(self) -> None:
        if not self.running and all(r.running for r in self.runnables):
            super().start()

    def _on_stop(self) -> None:
        if not self.stopped and all(r.stopped for r in self.runnables):
            super().stop()


class Runnables(HasRunnables):
    def __init__(self, *runnables: Runnable):
        self.runnables = runnables
        super().__init__()


@dc.dataclass
class ThreadQueue(HasRunnables, t.Generic[T]):
    """A simple multi-producer, multi-consumer queue with one thread per consumer.

    There is a special `finish_message` value, which when received shuts down
    that consumer.  ThreadQueue.finish() puts one `self.finish_message` onto the
    queue for each consumer.
    """

    #: `callback` is called on one of the worker threads for each entry
    #: that gets added to the queue
    callback: t.Callable[[T], None]

    #: Passed to threading.Thread
    daemon: bool = False

    #: If set, `exception` gets called on an Exception.
    exception: t.Optional[ExceptionHandler] = None

    #: Do we join the thread in __exit__?
    join_on_exit: bool = True

    #: Used for error and debug logging
    log: IsLog = logging

    #: Passed to queue.Queue
    maxsize: int = 0

    #: The print name of the thread, used for debugging
    name: str = 'thread_queue'

    #: Number of threads to service the queue
    thread_count: int = 1

    #: Timeout in polling the queue
    timeout: t.Optional[float] = 0.1

    def __post_init__(self) -> None:
        def thread(i: int) -> HasThread:
            return HasThread(
                callback=self._callback,
                exception=self.exception,
                join_on_exit=self.join_on_exit,
                name=f'{self.name}-{i}',
            )

        HasRunnables.__init__(self)
        self.runnables = tuple(thread(i) for i in range(self.thread_count))

    def put(self, item: T) -> None:
        self.queue.put(item)

    @cached_property
    def queue(self) -> 'Queue[T]':
        # See https://stackoverflow.com/a/57728797/43839
        return Queue(self.maxsize)

    def finish(self) -> None:
        """Put an empty message into the queue for each listener"""
        for _ in self.runnables:
            self.put(t.cast(T, _SENTINEL_MESSAGE))

        super().finish()

    def _callback(self) -> None:
        self.running.wait()

        while self.running:
            try:
                item = self.queue.get(timeout=self.timeout)
            except Empty:
                continue
            if item == _SENTINEL_MESSAGE:
                return
            try:
                self.callback(item)
            except Exception:
                self.stop()
                raise
