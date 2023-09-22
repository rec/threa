import abc
import dataclasses as dc
import functools
import logging
import traceback
import typing as t
from threading import Thread

from .runnable import Callback, Runnable

__all__ = 'ExceptionHandler', 'HasThread', 'IsLog', 'IsThread'

ExceptionHandler = t.Callable[[Exception], None]


class IsLog(t.Protocol):
    """A class that looks like a subset of Python's logging"""

    debug: t.Callable
    error: t.Callable


def _add_log(method=None, before=True, after=False):
    if method is None:
        return functools.partial(_add_log, before=before, after=after)

    @functools.wraps(method)
    def wrapped(self, *a, **ka):
        msg = f'{self}: {method.__name__}'

        try:
            before and self.log.debug(f'{msg}: before')
            return method(self, *a, **ka)
        finally:
            after and self.log.debug(f'{msg}: after')

    return wrapped


class ThreadBase(Runnable):
    """A base class for classes with a thread.

    It adds the following features to threading.Thread:

    * Has Events `running` and `stopped` with `on_set` callbacks
    * Handles exceptions and prints or redirects them
    * Runs once, or multiple times, depending on `self.looping`
    """

    #: `callback` is called one or more times in a new thread, depending
    #: on the value of `looping` and whether the thread gets stopped
    callback: Callback

    #: If set, `exception` gets called on an Exception.
    exception: t.Optional[ExceptionHandler] = None

    #: Passed to threading.Thread
    daemon: bool = False

    #: Used for error and debug logging
    log: IsLog = logging

    #: If True, `callback` is called repeated until `running` is unset
    #: If False, `callback` is called just once
    looping: bool = False

    #: The print name of the thread, used for debugging
    name: str = ''

    def __str__(self):
        return f'({self.__class__.__name__}){self.name}'

    @_add_log
    def pre_run(self):
        pass

    @_add_log(after=True)
    def run(self):
        self.pre_run()
        self.running.set()

        def tb():
            exc = traceback.format_exc()
            self.log.error(f'{self}: Exception\n{exc}')
            self.stop()

        while self.running:
            try:
                self.callback()
            except Exception as e:
                if self.exception:
                    try:
                        self.exception(e)
                    except Exception:
                        tb()
                    else:
                        self.stop()
                else:
                    tb()
            else:
                if not self.looping:
                    self.stop()

        self.stopped.set()

    @_add_log
    def stop(self):
        self.running.clear()

    @_add_log
    def finish(self):
        pass


class IsThread(ThreadBase, Thread, abc.ABC):
    """This ThreadBase inherits from threading.Thread.

    To use IsThread, derive from it and override either or both of
    self.callback() and self.pre_run()
    """

    def __init__(self, *args, **kwargs):
        ThreadBase.__init__(self, *args, **kwargs)
        Thread.__init__(self, daemon=self.daemon)

    @abc.abstractmethod
    def callback(self):
        """Called one or more times in a new thread"""

    @_add_log(after=True)
    def join(self, timeout: t.Optional[float] = None):
        Thread.join(self, timeout)

    @_add_log
    def start(self):
        Thread.start(self)


@dc.dataclass
class HasThread(ThreadBase):
    """This ThreadBase contains a thread, and is constructed with a callback"""

    #: `callback` is called one or more times in a new thread, depending
    #: on the value of `looping` and whether the thread gets stopped
    callback: Callback

    #: If set, `exception` gets called on an Exception.
    exception: t.Optional[ExceptionHandler] = None

    #: Passed to threading.Thread
    daemon: bool = False

    #: Used for error and debug logging
    log: IsLog = logging

    #: If True, `callback` is called repeated until `running` is unset
    #: If False, `callback` is called just once
    looping: bool = False

    #: The print name of the string, used for debugging
    name: str = ''

    def __post_init__(self):
        ThreadBase.__init__(self)

    @_add_log(after=True)
    def join(self, timeout: t.Optional[float] = None):
        self.thread.join(timeout)

    @_add_log
    def start(self):
        self.thread.start()

    def new_thread(self) -> Thread:
        return Thread(target=self.run, daemon=self.daemon)

    @functools.cached_property
    def thread(self) -> Thread:
        return self.new_thread()
