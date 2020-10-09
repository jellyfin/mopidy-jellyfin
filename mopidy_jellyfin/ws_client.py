# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function, unicode_literals

#################################################################################################

import json
import logging
import requests
import threading
import mopidy_jellyfin
from .http import JellyfinHttpClient

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
        # Start in a second thread to not interfere with the main program

        logger.debug("WSClient initializing...")

        self.client = client
        self.device_id = mopidy_jellyfin.Extension.device_id
        # Load things from config file
        cert = None
        client_cert = self.client.config['jellyfin'].get('client_cert', None)
        client_key = self.client.config['jellyfin'].get('client_key', None)
        if client_cert is not None and client_key is not None:
            cert = (client_cert, client_key)
        self.hostname = self.client.config['jellyfin'].get('hostname')
        proxy = self.client.config.get('proxy', None)

        self.token = self.client.token
        headers = {'x-mediabrowser-token': self.token}
        self.http = JellyfinHttpClient(headers, cert, proxy)
        threading.Thread.__init__(self)

    def send(self, message, data=""):
        # Send message to the Jellyfin server

        if self.wsc is None:
            raise ValueError("The websocket client is not started.")

        self.wsc.send(json.dumps({'MessageType': message, "Data": data}))

    def run(self):
        # Starts the websocket event listener

        response_url = self.http.check_redirect(self.hostname)
        if self.hostname != response_url:
            self.hostname = response_url
        if self.hostname.startswith('https'):
            server = self.hostname.replace('https', "wss")
        else:
            server = self.hostname.replace('http', "ws")
        wsc_url = "%s/socket?api_key=%s&device_id=%s" % (server, self.token, self.device_id)

        self.wsc = websocket.WebSocketApp(
            wsc_url,
            on_message=lambda ws, message: self.on_message(ws, message),
            on_error=lambda ws, error: self.on_error(ws, error))
        self.wsc.on_open = lambda ws: self.on_open(ws)


        while not self.stop:

            self.wsc.run_forever(ping_interval=10)

            if not self.stop:
                break

        self.callback('WebSocketDisconnect', None)


    def on_error(self, ws, error):
        logger.error(error)
        self.callback('WebSocketError', error)

    def on_open(self, ws):
        self.post_capabilities()
        self.callback('WebSocketConnect', None)

    def on_message(self, ws, message):
        # Receive messages from Jellyfin, sends to callback for processing

        message = json.loads(message)
        data = message.get('Data', {})

        self.callback(message['MessageType'], data)

    def stop_client(self):
        # Stop the client websocket thread

        self.stop = True

        if self.wsc is not None:
            self.wsc.close()

    def post_capabilities(self):
        # Tell the server what media and controls we can handle

        data = {
            'PlayableMediaTypes': "Audio",
            'SupportsMediaControl': True,
            'SupportedCommands': (
                    "VolumeUp,VolumeDown,ToggleMute"
                    "SetAudioStreamIndex,"
                    "SetRepeatMode,"
                    "Mute,Unmute,SetVolume,"
                    "Play,Playstate,PlayNext,PlayMediaSource"
            )
        }

        url = '{}/Sessions/Capabilities/Full'.format(self.hostname)

        self.http.post(url, data)

    def callback(self, message, data):
        # Processes events from Jellyfin and sends them to EventListener

        if message == 'Pause':
           self.client.playback.pause_track()
        elif message == 'Play':
            self.client.play_tracks(data)
        elif message == 'Playstate':
            self.client.playstate(data)
        elif message == 'GeneralCommand':
            self.client.general_command(data)
