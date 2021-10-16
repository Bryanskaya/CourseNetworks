from torfile import Torrent
from tracker import Tracker
from asyncio import Queue, sleep
from typing import List

import logging
import time
import bitstring

from protocol import PeerConnection
from piece_man import PieceManager

MAX_PEER_CONNECTIONS = 40  # 40


class TorrentClient:
    abort = False

    def __init__(self, torrent: Torrent, file_path: str):
        self.tracker = Tracker(torrent)
        self.available_peers = Queue()
        self.peers: List[PeerConnection] = []
        self.piece_manager = PieceManager(torrent, file_path)

    async def start(self):
        self.peers = [PeerConnection(i, self.available_peers,
                                     self.tracker.torrent.info_hash,
                                     self.tracker.peer_id, self.piece_manager,
                                     self._block_retrieved)
                      for i in range(MAX_PEER_CONNECTIONS)]

        previous = None
        interval = 30 * 60  # seconds between server requesting

        while True:
            if self.piece_manager.complete:
                print('Torrent fully downloaded!')
                logging.info('Torrent fully downloaded!')
                break
            if self.abort:
                logging.info(" Torrent is downloaded")
                break

            cur_time = time.time()
            if previous is None or cur_time - previous >= interval:
                response = await self.tracker.connect(
                    # TODO uncomment when piece_manager will be implemented
                    # uploaded=self.piece_manager.bytes_uploaded,
                    # downloaded=self.piece_manager.bytes_downloaded,
                    first_call=previous if previous else False
                )
                previous = cur_time
                interval = response.interval

                print('TRACKER RESPONSE:')
                print(response.peers)
                print(response.response)

                if not response:
                    continue

                self._empty_queue()
                for peer in response.peers:
                    print(peer)
                    self.available_peers.put_nowait(peer) # Put an item into the queue without blocking.
            else:
                await sleep(5)

        await self.stop()

    async def stop(self) -> None:
        self.abort = True

        for peer in self.peers:
            peer.stop()

        # TODO close piece_manager

        await self.tracker.close()

    def _empty_queue(self) -> None:
        while not self.available_peers.empty():
            self.available_peers.get_nowait()   # Remove and return an item from the queue

    def _block_retrieved(self, peer_id: str, piece_index: int, block_offset, data) -> None:
        self.piece_manager.block_received(peer_id, piece_index, block_offset, data)

    # TODO piece_manager

    @property
    def total_size(self) -> int:
        return self.tracker.torrent.total_size

    @property
    def active_peer_n(self) -> int:
        n = sum(1 if peer.remote_id is not None
                else 0
                for peer in self.peers)
        return n

    @property
    def loaded_bytes(self) -> int:
        return self.piece_manager.loaded_bytes

    @property
    def ongoing_map(self) -> bitstring.BitArray:
        return self.piece_manager.ongoing_map

    @property
    def loaded_map(self) -> bitstring.BitArray:
        return self.piece_manager.piecemap
