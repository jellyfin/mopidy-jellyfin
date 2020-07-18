from mopidy import httpclient
import requests
import mopidy_jellyfin
import logging

logger = logging.getLogger(__name__)

class JellyfinHttpClient(object):
    def __init__(self, headers, cert=None, proxy=None):
        http_proxy = httpclient.format_proxy(proxy)
        user_agent = httpclient.format_user_agent(
            '/'.join(
                (
                    mopidy_jellyfin.Extension.dist_name,
                    mopidy_jellyfin.__version__
                )
            )
        )

        self.headers = headers
        self.session = requests.Session()
        self.session.cert = cert
        self.session.proxies.update({'http': http_proxy, 'https': http_proxy})
        self.session.headers.update(self.headers)
        self.session.headers.update({'user-agent': user_agent})

    def get(self, url):
        # Perform HTTP Get to the provided URL
        counter = 0
        self.session.headers.update(self.headers)
        while counter <= 5:

            try:
                r = self.session.get(url)
                try:
                    rv = r.json()
                except Exception as e:
                    logger.info(
                        'Error parsing Jellyfin data: {}'.format(e)
                    )
                    rv = {}

                logger.debug(str(rv))

                return rv

            except Exception as e:
                logger.info(
                    'Jellyfin connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Jellyfin API')

    def post(self, url, payload={}):
        # Perform HTTP Post to the provided URL
        self.session.headers.update(self.headers)

        counter = 0
        while counter <= 5:

            try:
                r = self.session.post(url, json=payload)
                if r.text:
                    rv = r.json()
                else:
                    rv = r.text

                logger.debug(rv)

                return rv

            except Exception as e:
                logger.info(
                    'Jellyfin connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Jellyfin API')

    def delete(self, url):
        # Perform HTTP Delete to the provided URL
        counter = 0
        self.session.headers.update(self.headers)
        while counter <= 5:

            try:
                r = self.session.delete(url)

                logger.debug(str(r))

                return r

            except Exception as e:
                logger.info(
                    'Jellyfin connection on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Cant connect to Jellyfin API')

    def check_redirect(self, server):
        # Perform HTTP Get to public endpoint to check for redirects
        counter = 0
        self.session.headers.update(self.headers)
        path = '/system/info/public'

        if 'http' not in server:
            server = 'http://' + server

        while counter <= 5:

            try:
                r = self.session.get(f'{server}{path}')
                r.raise_for_status()

                return r.url.replace(path, '')

            except Exception as e:
                logger.error(
                    'Failed to reach Jellyfin public API on try {} with problem: {}'.format(
                        counter, e
                    )
                )
                counter += 1

        raise Exception('Unable to find Jellyfin server, check hostname config')
