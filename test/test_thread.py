import time

import threa


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


def test_has_thread():
    result = []

    def callback():
        result.append(0)
        if len(result) >= 4:
            ht.stop()

    ht = threa.HasThread(callback)
    with ht:
        pass

    assert ht.stopped
    assert result == [0]


if __name__ == '__main__':
    # A little sandbox for experimenting with threads.
    import logging

    logging.basicConfig(level=logging.DEBUG)
    start = time.time()
    LOOPING = False

    def cb(label='was', dt=2):
        print(label, time.time() - start)
        time.sleep(dt)

    class Is(threa.IsThread):
        looping = LOOPING

        def callback(self):
            cb('is', 1.5)

    ht = threa.HasThread(cb, looping=LOOPING)
    ht.start()
    Is().start()
