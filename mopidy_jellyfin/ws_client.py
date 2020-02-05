# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals

#################################################################################################

import json
import logging
import requests
import socket
import threading
import mopidy_jellyfin

import websocket

from mopidy import core
import mopidy

##################################################################################################

logger = logging.getLogger(__name__)

##################################################################################################


class WSClient(threading.Thread):

    wsc = None
    stop = False

    def __init__(self, client):

        logger.debug("WSClient initializing...")

        self.client = client
        threading.Thread.__init__(self)

    def send(self, message, data=""):

        if self.wsc is None:
            raise ValueError("The websocket client is not started.")

        self.wsc.send(json.dumps({'MessageType': message, "Data": data}))

    def _http_post(self, data):
        r = requests.post(f'{self.hostname}/Playing/Progress', headers=self.headers, json=data)

        return r

    def _login(self):
        self.hostname = self.client.config.get('hostname')
        username = self.client.config.get('username')
        password = self.client.config.get('password')
        cert = self.client.config.get('client_cert', None)

        auth_payload = {
            'username': username,
            'Pw': password
        }

        url = f'{self.hostname}/Users/AuthenticateByName'

        headers = {}

        authorization = (
            'MediaBrowser , '
            'Client="Mopidy", '
            'Device="{name}", '
            'DeviceId="{name}", '
            'Version="{version}"'
        ).format(
            name=socket.gethostname(),
            version=mopidy_jellyfin.__version__
        )

        headers['x-emby-authorization'] = authorization

        r = requests.post(
                url, headers=headers, data=auth_payload, cert=cert)

        r.raise_for_status()

        if r.json().get('AccessToken'):
            headers['x-mediabrowser-token'] = r.json().get('AccessToken')

        self.headers = headers

        return r.json()

    def run(self):

        credentials = self._login()

        device_id = name=socket.gethostname()
        token = credentials.get('AccessToken')
        server = self.client.config.get('hostname')
        server = server.replace('https', "wss") if server.startswith('https') else server.replace('http', "ws")
        wsc_url = "%s/socket?api_key=%s&device_id=%s" % (server, token, device_id)

        logger.info("Websocket url: %s", wsc_url)

        self.wsc = websocket.WebSocketApp(
            wsc_url,
            on_message=lambda ws, message: self.on_message(ws, message),
            on_error=lambda ws, error: self.on_error(ws, error))
        self.wsc.on_open = lambda ws: self.on_open(ws)


        while not self.stop:

            self.wsc.run_forever(ping_interval=10)

            if not self.stop:
                break

        logger.info("---<[ websocket ]")
        self.callback('WebSocketDisconnect', None)


    def on_error(self, ws, error):
        logger.error(error)
        self.callback('WebSocketError', error)

    def on_open(self, ws):
        logger.info("--->[ websocket ]")
        self.post_capabilities()
        self.callback('WebSocketConnect', None)

    def on_message(self, ws, message):

        message = json.loads(message)
        data = message.get('Data', {})

        if message['MessageType'] in ('RefreshProgress',):
            logger.debug("Ignoring %s", message)

            return

        #data['ServerId'] = self.client.remote.auth_details.get('ServerId')

        self.callback(message['MessageType'], data)

    def stop_client(self):

        self.stop = True

        if self.wsc is not None:
            self.wsc.close()

    def post_capabilities(self):
        data = {
            'PlayableMediaTypes': "Audio",
            'SupportsMediaControl': True,
            'SupportedCommands': (
                    "VolumeUp,VolumeDown,ToggleMute,SendString,DisplayMessage,"
                    "SetAudioStreamIndex,"
                    "SetRepeatMode,"
                    "Mute,Unmute,SetVolume,"
                    "Play,Playstate,PlayNext,PlayMediaSource"
            )
        }

        url = f'{self.hostname}/Sessions/Capabilities/Full'

        r = requests.post(url, headers=self.headers, json=data)

    def callback(self, message, data):
        #logger.info(f'Callback message: {message}')
        #logger.info(f'Callback data: {data}')
        # TODO:
            # Playback modes (shuffle/repeat)

        if message == 'Pause':
           self.client.playback.pause_track()
        elif message == 'Play':
            self.client.play_tracks(data)
        elif message == 'Playstate':
            self.client.playstate(data)
        elif message == 'GeneralCommand':
            self.client.general_command(data)
        pass
