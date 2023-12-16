from threa import Wrapper


class Duck:
    def __init__(self):
        self.actions = []

    def join(self, t):
        self.actions.append('join')

    def stop(self):
        self.actions.append('stop')


def test_wrapper():
    d = Duck()

    with Wrapper(d):
        pass

    assert d.actions == ['stop', 'join']
