import logging
import bitstring
import math
import os
import time

from collections import defaultdict
from typing import List

from torfile import Torrent
from peer_msg import REQUEST_SIZE


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


class Piece:
    def __init__(self, index: int, blocks: [Block], hash_value):
        self.index = index
        self.blocks = blocks
        self.hash = hash_value

    def next_request(self) -> Block:
        missing: (Block, None) = None

        for block in self.blocks:
            if block.status is Block.Missing:
                missing = block
                break
        if missing:
            missing.status = Block.Pending

        return missing

    def block_received(self, offset: int, data: bytes):
        block = None

        for b in self.blocks:
            if b.offset is offset:
                block = b
                break
        if block:
            block.status = Block.Retrieved
            block.data = data
        else:
            logging.warning('Trying to complete a non-existing block {}'.format(offset))

    def is_complete(self) -> bool:
        blocks = [block for block in self.blocks
                  if block.status is not Block.Retrieved]

        return len(blocks) is 0



class PieceManager:
    missing_pieces: [Piece] = []
    ongoing_piece: List[Piece] = []
    peers = {}
    pending_blocks: [Block] = []

    def __init__(self, torrent: Torrent):
        self.torrent = torrent
        self.missing_pieces = self._initiate_pieces()
        self.fd = os.open(self.torrent.output_file, os.O_RDWR | os.O_CREAT)

    def _initiate_pieces(self) -> [Piece]:
        pieces = [Piece]    # TODO
        num_pieces = len(self.torrent.pieces)
        std_piece_block = math.ceil(self.torrent.piece_length / REQUEST_SIZE)

        for index, hash_value in enumerate(self.torrent.pieces):
            if index < num_pieces - 1:
                blocks = [Block(index, offset * REQUEST_SIZE, REQUEST_SIZE)
                          for offset in range(std_piece_block)]
            else:
                last_length = self.torrent.total_size % self.torrent.piece_length
                num_blocks = math.ceil(last_length / REQUEST_SIZE)
                blocks = [Block(index, offset * REQUEST_SIZE, REQUEST_SIZE)
                          for offset in range(num_blocks)]

                if last_length % REQUEST_SIZE:
                    blocks[-1].length = last_length % REQUEST_SIZE

            pieces.append(Piece(index, blocks, hash_value))

        return pieces

    def close(self):
        if self.fd:
            os.close(self.fd)

    def add_peer(self, peer_id: str, bitfield: bitstring.BitArray):
        self.peers[peer_id] = bitfield

        logging.debug('add new peer to PieceManager\n {} {}'.format(peer_id, bitfield))

    def update_peer(self, peer_id: str, index: int):
        if peer_id in self.peers:
            self.peers[peer_id][index] = 1  # TODO

        logging.debug('update peer in PieceManager')

    def next_request(self, peer_id: str) -> Block:
        if peer_id not in self.peers:
            return None # TODO

        block = self._expired_requests(peer_id)
        if block is None:
            block = self._next_ongoing(peer_id)
            if block is None:
                block = self._get_rarest_piece(peer_id) #TODO NEXT_REQUEST

        return block

    def block_received(self, peer_id: str, piece_index: int, block_offset, data):
        logging.debug('Received block {0} for piece {1} from peer {2}: '.format(block_offset,
            piece_index, peer_id))

        for index, request in enumerate(self.pending_blocks):
            if request.block.piece == piece_index and \
                    request.block.offset == block_offset:
                del self.pending_blocks[index]
                break

        piece = None
        for p in self.ongoing_piece:
            if p.index == piece_index:
                piece = p
                break

        if piece:
            piece.block_received(block_offset, data)
            if piece.is_complete():
                pass #TODO continue here






    def _expired_requests(self, peer_id: str) -> Block:
        current = int(round(time.time() * 1000))

        for request in self.pending_blocks:
            if self.peers[peer_id][request.block.piece]: # TODO block and added may be in PendingRequest
                #if request.

        # TODO continue

        return None

    def _next_ongoing(self, peer_id: str) -> Block:
        for piece in self.ongoing_piece:
           if self.peers[peer_id][piece.index]:
               block = piece.next_request()
                #if block:
                    #self.pending_blocks.append(
                        #TODO PendingRequest
                    #)
                    #return block
        #return None


    def _get_rarest_piece(self, peer_id: str):
        piece_count = defaultdict(int)
        for piece in self.missing_pieces:
            if not self.peers[peer_id][piece.index]:
                continue
            for peer in self.peers:
                if self.peers[peer][piece.index]: # TODO strange peer
                    piece_count[piece] += 1

        rarest_piece = min(piece_count, key=lambda p: piece_count[p])

        self.missing_pieces.remove(rarest_piece)
        self.ongoing_piece.append(rarest_piece)

        return rarest_piece






