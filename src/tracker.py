from urllib.parse import urlencode
import logging
import bencodepy
import random
import aiohttp
import socket
import struct

from torfile import Torrent

PORT = 6889  # Port used by BitTorrent


def decode_peer(bpeer: bytes) -> (str, int):
    ip = socket.inet_ntoa(bpeer[:4])
    port = int.from_bytes(bpeer[4:], "big")
    return ip, port


class TrackerResponse:
    def __init__(self, response: dict):
        self.response = response

    @property
    def interval(self) -> int:
        # 10 if interval not mentioned in response
        return self.response.get(b'interval', 10)

    @property
    def peers(self):
        peers = self.response[b'peers']
        if type(peers) is list:
            return None
        else:   # string
            peers = [decode_peer(peers[i:i+6])
                     for i in range(0, len(peers), 6)]
            return peers


class Tracker:
    def __init__(self, torrent: Torrent):
        self.torrent = torrent
        self.peer_id = _get_peer_id()
        self.http_client = aiohttp.ClientSession()

    def raise_error(self, tr_response: bytes):
        try:
            msg = tr_response.decode("utf-8")
            if "failure" in msg:
                raise ConnectionError(" connection to tracker failed. "
                                      "Code = " + msg)
        except UnicodeDecodeError:
            pass

    async def connect(self, uploaded: int = 0,
                      downloaded: int = 0, first_call: bool = None):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'port': PORT,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.torrent.total_size - downloaded,
            'compact': 1
        }

        if first_call:
            params['event'] = 'started'
        try:
            url = self.torrent.announce + '?' + urlencode(params)
            logging.info('connecting to tracker. URL: ' + url)

            async with self.http_client.get(url, ssl=False) as response:
                if response.status != 200:
                    raise ConnectionError("ERROR: connection to tracker failed. "
                                          "Code = " + str(response.status))

                data = await response.read()
                self.raise_error(data)

                return TrackerResponse(bencodepy.decode(data))
        except Exception as exp:
            print(exp)

    async def close(self):
        await self.http_client.close()


# Style: "-PC1000-<12-random-characters>"
def _get_peer_id() -> str:
    return '-PC1000-' + ''.join([str(random.randint(0, 9)) for _ in range(12)])
