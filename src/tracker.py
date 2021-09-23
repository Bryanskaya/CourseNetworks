from urllib.parse import urlencode

PORT = 6889    #TODO port
class Tracker:
    def __init__(self, torrent):
        self.torrent = torrent


    async def connect(self, uploaded_bytes = 0, downloaded_bytes = 0):
        params = {
            'info_hash': self.torrent.info_hash,
            'peer_id': self.peer_id,
            'port': PORT,
            'uploaded_bytes': uploaded_bytes,
            'downloaded_bytes': downloaded_bytes,
            'left': self.torrent.total_size - downloaded_bytes,
            'compact': 1
        }
        url = self.torrent.announce + '?' + urlencode(params)