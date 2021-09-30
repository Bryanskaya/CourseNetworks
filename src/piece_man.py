from torfile import Torrent

import logging
import bitstring


class Block:
    Missing = 0
    Pending = 1
    Retrieved = 2

    data: bytes = None

    def __init__(self, piece: int, offset: int, length: int):
        self.piece = piece
        self.offset = offset
        self.length = length
        self.status = self.Missing


class PieceManager:
    def __init__(self, torrent: Torrent):
        self.torrent = torrent

    def block_received(self, peer_id: str, piece_index: int, block_offset, data):
        logging.debug('Received block {0} for piece {1} from peer {2}: '.format(block_offset,
            piece_index, peer_id))

    def add_peer(self, peer_id: str, bitfield: bitstring.BitArray):
        logging.debug('add new peer to PieceManager\n {} {}'.format(peer_id, bitfield))

    def update_peer(self, peer_id: str, index: int):
        logging.debug('update peer in PieceManager')
