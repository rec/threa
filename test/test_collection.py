import random
import time

import pytest

import threa


@pytest.mark.parametrize('thread_count', [1, 3])
def test_thread_queue(thread_count):
    result = []

    def callback(item):
        result.append(item)
        time.sleep(random.uniform(0.001, 0.010))

    with threa.ThreadQueue(callback, thread_count=thread_count) as tq:
        for i in range(8):
            tq.put(i)

    assert not tq.running
    assert sorted(result) == list(range(8))


@pytest.mark.parametrize('thread_count', [1, 3])
def test_thread_queue_exception(thread_count):
    result = []
    exceptions = []

    def callback(item):
        result.append(item)
        if len(result) == 5:
            result.append('EXCEPTION')
            raise ValueError('An', 'exception')

        time.sleep(random.uniform(0.001, 0.010))

    with threa.ThreadQueue(
        callback=callback, exception=exceptions.append, thread_count=thread_count
    ) as tq:
        for i in range(8):
            tq.put(i)

    assert not tq.running
    assert result == (list(range(5)) + ['EXCEPTION'])
    assert [e.args for e in exceptions] == [('An', 'exception')]
