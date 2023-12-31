import threading
import types
import typing as t

Callback = t.Callable[[], None]


class Event(threading.Event):
    """
    A threading.Event that also calls back to zero or more functions when its state
    is set or reset, and has a __bool__ method.

    Note that the callback might happen on some completely different thread,
    so these functions cannot block"""

    on_set: t.List[Callback]

    def __init__(self, *on_set: Callback) -> None:
        self.on_set = list(on_set)
        super().__init__()

    def set(self) -> None:
        super().set()
        [c() for c in self.on_set]

    def clear(self) -> None:
        super().clear()
        [c() for c in self.on_set]

    def __bool__(self) -> bool:
        return self.is_set()


class _Event:
    def __set_name__(self, owner: t.Any, name: str) -> None:
        self.name = '_' + name

    def __get__(self, obj: t.Any, objtype: t.Any = None) -> Event:
        event: t.Optional[Event] = getattr(obj, self.name, None)
        if event is not None:
            return event

        setattr(obj, self.name, event := Event())
        return event

    def __set__(self, obj: t.Any, value: t.Union[bool, Event]) -> None:
        if isinstance(value, Event):
            setattr(obj, self.name, value)
        elif value:
            self.__get__(obj).set()
        else:
            self.__get__(obj).clear()


class Runnable:
    """A base class for things that start, run, finish, stop and join

    Stopping is requesting immediate termination: finishing is saying that
    there is no more work to be done, finish what you are doing.

    A Runnable has two `Event`s, `running` and `stopped`, and you can either
    `wait` on either of these conditions to be true, or add a callback function
    (which must be non-blocking) to either of them.

    `running` is not set until the setup for a `Runnable` has finished;
    `stopped` is not set until all the computations in a thread have ceased.

    An Runnable can be used as a context manager:

        with runnable:
            # The runnable is running by this point
            do_stuff()
        # By the time you get to here, the runnable has completely stopped

    The above means roughly the same as

        runnable.start()
        try:
            do_stuff()
            runnable.finish()
            runnable.join()
        finally:
            runnable.stop()

    """

    running = _Event()
    stopped = _Event()

    #: Do we join the thread in __exit__?
    join_on_exit: bool = True

    def start(self) -> None:
        """Start this object.

        Note that self.running might not be immediately true after this method completes
        """
        self.running = True

    def stop(self) -> None:
        """Stop as soon as possible. might not do anything, should never raise.

        Note that self.stopped might not be immediately true after this method completes
        """
        self.running = False
        self.stopped = True

    def finish(self) -> None:
        """Request an orderly shutdown where all existing work is completed.

        Note that self.stopped might not be immediately true after this method completes
        """
        self.stop()

    def join(self, timeout: t.Optional[float] = None) -> None:
        """Join this thread or process.  Might block indefinitely, might do nothing"""

    def __enter__(self) -> 'Runnable':
        self.start()
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_val: t.Optional[BaseException],
        exc_tb: t.Optional[types.TracebackType],
    ) -> None:
        if exc_type in (None, KeyboardInterrupt):
            self.finish()
            if self.join_on_exit:
                self.join()
        else:
            self.stop()
