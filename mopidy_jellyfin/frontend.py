from mopidy import audio, core
import pykka
import logging
import threading

from .ws_client import WSClient
from mopidy_jellyfin import listener, Extension

logger = logging.getLogger(__name__)

class EventMonitorFrontend(
        pykka.ThreadingActor,
        core.CoreListener,
        audio.AudioListener,
        listener.JellyfinListener,
):
    # Sends events and playback updates back to Jellyfin server

    def __init__(self, config, core):
        super(EventMonitorFrontend, self).__init__()
        self.core = core
        self.token = self._read_token(config)
        self.config = config
        self.hostname = self.config['jellyfin'].get('hostname')

        self.wsc = WSClient(self)


    def on_start(self):
        # Start the websocket client
        self.wsc.start()

    def on_stop(self):
        # Stop the websocket client and tell the server playback has stopped
        self._stop_playback()
        self.wsc.stop_client()

    def on_event(self, event, **kwargs):
        # Receives internal Mopidy events
        super(EventMonitorFrontend, self).on_event(event, **kwargs)

        if event == 'playback_state_changed':
            self._playback_state_changed(kwargs)
        elif event == 'seeked':
            self._seeked(kwargs)
        elif event == 'volume_changed':
            self._volume_changed(kwargs)

    def _get_session_id(self):
        # Get the current playback session ID from the Jellyfin server
        device_id = Extension.device_id
        sessions = self.wsc.http.get(
            '{}/Sessions?DeviceId={}'.format(self.hostname, device_id))

        session_id = sessions[0].get('Id')

        return session_id


    def _playback_state_changed(self, data):
        # When mopidy changes tracks, send an update to Jellyfin

        session_id = self._get_session_id()

        new_state = data.get('new_state')
        if new_state in ['paused', 'playing']:
            play_time = self.core.playback.get_time_position().get() * 10000
            track = self.core.playback.get_current_track().get()
            item_id = track.uri.split(':')[-1]
            playback_ms = self.core.playback.get_time_position().get()
            playback_ticks = playback_ms * 10000
            volume = self.core.mixer.get_volume().get()

            if new_state == 'paused':
                pause_state = True
            else:
                pause_state = False

            data = {
                "VolumeLevel": volume,
                "IsMuted": False,
                "IsPaused": pause_state,
                "RepeatMode": "RepeatNone",
                "PositionTicks": play_time,
                "PlayMethod": "DirectPlay",
                "PlaySessionId": session_id,
                "MediaSourceId": item_id,
                "CanSeek": True,
                "ItemId": item_id,
            }

            self._start_playback(data)

        elif new_state == 'stopped':
            self._stop_playback()

    def _stop_playback(self):
        # Report to Jellyfin that playback has stopped
        r = self.wsc.http.post(
            '{}/Sessions/Playing/Stopped'.format(self.hostname))

    def _start_playback(self, data):
        # Report to Jellyfin that playback has started
        report = self.wsc.http.post(
            '{}/Sessions/Playing'.format(self.hostname), data)

    def _seeked(self, kwargs):
        # Report to Jellyfin the new playback position
        playback_time = kwargs.get('time_position') * 10000
        self._update_playback(PositionTicks=playback_time,
                              EventName='TimeUpdate')

    def _volume_changed(self, kwargs):
        # Report to Jellyfin the new volume level
        volume = kwargs.get('volume')

        self._update_playback(Volume=volume, EventName='VolumeChange')

    def _update_playback(self, **kwargs):
        # Send an update to Jellyfin about the current playback status
        session_id = self._get_session_id()
        track = self.core.playback.get_current_track().get()
        if track:
            item_id = track.uri.split(':')[-1]
            volume = self.core.mixer.get_volume().get()
            data = {
                "VolumeLevel": volume,
                "IsMuted": False,
                "IsPaused": False,
                "RepeatMode": "RepeatNone",
                "PositionTicks": 0,
                "PlayMethod": "DirectPlay",
                "PlaySessionId": session_id,
                "MediaSourceId": item_id,
                "CanSeek": True,
                "ItemId": item_id,
            }
            data.update(kwargs)

            # This should work, but isn't.  Using http post for now
            #self.wsc.send('ReportPlaybackProgress', data=data)
            r = self.wsc.http.post(
                '{}/Sessions/Playing/Progress'.format(self.hostname), data)

    def playstate(self, data):
        # Processes Playstate commands received from the Jellyfin server
        command = data.get('Command')
        if command == 'NextTrack':
            self.core.playback.next()
        elif command == 'PreviousTrack':
            self.core.playback.previous()
        elif command == 'PlayPause':
            state = self.core.playback.get_state().get()
            if state == 'playing':
                self.core.playback.pause()
            else:
                self.core.playback.resume()
        elif command == 'Stop':
            self.core.playback.stop()
        elif command == 'Seek':
            position_ticks = data.get('SeekPositionTicks')
            position_ms = int(position_ticks / 10000)
            self.core.playback.seek(position_ms)

    def general_command(self, data):
        # Processes General commands received from the Jellyfin server
        command = data.get('Name')
        if command == 'SetVolume':
            volume = data['Arguments'].get('Volume')
            self.core.mixer.set_volume(int(volume))
        elif command == 'ToggleMute':
            if self.core.mixer.get_mute().get():
                self.core.mixer.set_mute(False)
            else:
                self.core.mixer.set_mute(True)

    def play_tracks(self, data):
        # Receives the "Play To" commands from the Jellyfin server
        items = data.get('ItemIds')
        uris = ['jellyfin:track:{}'.format(item_id) for item_id in items]
        tracks = self.core.tracklist.add(uris=uris).get()
        self.core.playback.play(tlid=tracks[0].tlid)

    def _read_token(self, config):
        # Reads authentication token generated by backend
        cache_dir = Extension.get_cache_dir(config)
        token_file = cache_dir / 'token'

        with open(token_file, 'r') as f:
            token = f.read()

        return token
