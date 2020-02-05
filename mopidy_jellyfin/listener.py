from mopidy import backend, listener


class JellyfinListener(listener.Listener):
    def __init__(self, listener):
        self.listener = listener

    def send(event, **kwargs):
        listener.send(JellyfinPlaybackListener, event, **kwargs)

