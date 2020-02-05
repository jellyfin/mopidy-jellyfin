from mopidy import backend, listener


class JellyfinListener(listener.Listener):
    # Receives internal Mopidy commands
    def __init__(self, listener):
        self.listener = listener

    def send(event, **kwargs):
        # Sends events to the EventListener for processing
        listener.send(JellyfinPlaybackListener, event, **kwargs)

