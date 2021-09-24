from torfile import Torrent


class PieceManager:
    def __init__(self, torrent: Torrent):
        self.torrent = torrent
