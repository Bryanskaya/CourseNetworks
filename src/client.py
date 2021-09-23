from torfile import Torrent
from tracker import Tracker

class TorrentClient:
    def __init__(self, torrent: Torrent):
        self.tracker = Tracker(torrent)