from torfile import Torrent

import logging


class PieceManager:
    def __init__(self, torrent: Torrent):
        self.torrent = torrent

    def block_received(self, peer_id: str, piece_index: int, block_offset, data):
        logging.debug('Received block {0} for piece {1} from peer {2}: '.format(block_offset,
            piece_index, peer_id))


