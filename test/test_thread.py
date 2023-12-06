import time

import threa
from threa import thread


def test_is_thread():
    result = []

    class IsThread(threa.IsThread):
        def callback(self):
            result.append(0)
            if len(result) >= 4:
                self.stop()

    it = IsThread()
    assert not it.running
    assert not it.stopped
    assert not result

    with it:
        pass

    assert it.stopped
    assert result == [0]

    result.clear()

    it = IsThread()
    it.looping = True

    with it:
        pass

    assert it.stopped
    assert result == [0, 0, 0, 0]


def test_has_thread(monkeypatch):
    result = []
    sleeps = []
    monkeypatch.setattr(thread, 'sleep', sleeps.append)

    def callback():
        result.append(0)
        if len(result) >= 4:
            ht.stop()

    ht = threa.HasThread(callback, pre_delay=2, post_delay=-1)
    with ht:
        pass

    assert ht.stopped
    assert result == [0]
    assert sleeps == [2]


if __name__ == '__main__':
    # A little sandbox for experimenting with threads.
    import logging

    logging.basicConfig(level=logging.DEBUG)
    start = time.time()
    LOOPING = True

    def cb(label='HasThread', dt=5):
        elapsed = time.time() - start
        print(label, elapsed)
        time.sleep(dt)
        if elapsed > 5:
            raise ValueError('Houston, do you read?')

    class Is(threa.IsThread):
        looping = LOOPING

        def callback(self):
            cb('IsThread ', 1.5)

    ht = threa.HasThread(cb, looping=LOOPING)
    ht.start()
    Is().start()
