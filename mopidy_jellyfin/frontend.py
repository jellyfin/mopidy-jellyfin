from mopidy import audio, core
import pykka
import logging
import threading
import os
import time

from .ws_client import WSClient
from mopidy_jellyfin import Extension

logger = logging.getLogger(__name__)

class EventMonitorFrontend(
        pykka.ThreadingActor,
        core.CoreListener,
        audio.AudioListener
):
    # Sends events and playback updates back to Jellyfin server

    def __init__(self, config, core):
        super(EventMonitorFrontend, self).__init__()
        self.core = core
        self.token = self._read_token(config)
        self.config = config
        self.hostname = self.config['jellyfin'].get('hostname')

        self.wsc = WSClient(self)
        response_url = self.wsc.http.check_redirect(self.hostname)
        if self.hostname != response_url:
            self.hostname = response_url
        self.reporting_thread = threading.Thread(target=self._check_status)
        # Kill thread immediately on program exit
        self.reporting_thread.daemon = True

    def on_start(self):
        # Start the websocket client and reporting thread
        self.wsc.start()
        self.reporting_thread.start()

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

        if sessions:
            session_id = sessions[0].get('Id')
        else:
            logger.debug('Unable to find playback session on server')
            session_id = None

        return session_id


    def _playback_state_changed(self, data):
        # When mopidy changes tracks, send an update to Jellyfin

        new_state = data.get('new_state')
        old_state = data.get('old_state')

        if new_state == 'playing' and old_state == 'playing':
            # Report playback stopped between songs for scrobbling purposes
            # https://github.com/jesseward/jellyfin-plugin-lastfm/issues/27#issuecomment-744031810
            self._stop_playback()

        if new_state in ['paused', 'playing']:
            data = self._create_progress_payload()
            if data:
                self._start_playback(data)
        elif new_state == 'stopped':
            self._stop_playback()

    def _stop_playback(self):
        # Report to Jellyfin that playback has stopped
        self.wsc.http.post(
            '{}/Sessions/Playing/Stopped'.format(self.hostname))

    def _start_playback(self, data):
        # Report to Jellyfin that playback has started
        self.wsc.http.post(
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

        data = self._create_progress_payload()
        if data:
            data.update(kwargs)

            # This should work, but isn't.  Using http post for now
            #self.wsc.send('ReportPlaybackProgress', data=data)
            self.wsc.http.post(
                '{}/Sessions/Playing/Progress'.format(self.hostname), data)

    def _create_progress_payload(self):
        # Build the json payload sent to the server for playback reporting

        session_id = self._get_session_id()
        track = self.core.playback.get_current_track().get()

        if session_id and track:
            item_id = track.uri.split(':')[-1]
            mute_state = self.core.mixer.get_mute().get()
            volume = self.core.mixer.get_volume().get()
            play_time = self.core.playback.get_time_position().get() * 10000

            state = self.core.playback.get_state().get()
            if state == 'paused':
                pause_state = True
            else:
                pause_state = False
            # Report current playlist and position to server
            track_index = self.core.tracklist.index().get()
            tracklist = self.core.tracklist.get_tracks().get()
            now_playing_queue = []
            for index, track in enumerate(tracklist):
                track_id = track.uri.split(':')[-1]
                now_playing_queue.append({
                    'Id': track_id,
                    'PlaylistItemId': f'playlistItem{index}'
                })
            playlist_item_id = f'playlistItem{track_index}'

            # json payload to server
            data = {
                "VolumeLevel": volume,
                "IsMuted": mute_state,
                "IsPaused": pause_state,
                "RepeatMode": "RepeatNone",
                "PositionTicks": play_time,
                "PlayMethod": "DirectPlay",
                "PlaySessionId": session_id,
                "MediaSourceId": item_id,
                "CanSeek": True,
                "ItemId": item_id,
                "NowPlayingQueue": now_playing_queue,
                "PlaylistItemId": playlist_item_id,
            }
        else:
            data = {}

        return data


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
        playcommand = data.get('PlayCommand', '')
        start_ticks = data.get('StartPositionTicks')
        if start_ticks:
            start_position = int(start_ticks / 10000)
        else:
            start_position = 0

        uris = ['jellyfin:track:{}'.format(item_id) for item_id in items]
        tracks = self.core.tracklist.add(uris=uris).get()
        # Allows adding to play queue without changing currently playing track
        if playcommand == 'PlayNow':
            start_index = data.get('StartIndex')
            if not start_index:
                start_index = 0
            self.core.playback.play(tlid=tracks[start_index].tlid)
        # If playing a track that already has playback progress, start at that
        # progress point, not the beginning
        if start_position:
            # Needs to wait a short time before seeking or else we lose
            # all control
            time.sleep(.5)
            self.core.playback.seek(int(start_position))


    def _read_token(self, config):
        # Reads authentication token generated by backend
        cache_dir = Extension.get_cache_dir(config)
        token_file = os.path.join(cache_dir, 'token')

        if not os.path.isfile(token_file):
            raise Exception('No authentication token found')

        with open(token_file, 'r') as f:
            token = f.read()

        return token

    def _check_status(self):
        # Reports status to Jellyfin server every 60 seconds
        while True:
            state = self.core.playback.get_state().get()
            if state in ['playing', 'paused']:
                self._update_playback()
            time.sleep(60)
