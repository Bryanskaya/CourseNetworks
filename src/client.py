from torfile import Torrent
from tracker import Tracker
from asyncio import Queue, sleep
from typing import List

import logging
import time

from protocol import PeerConnection


MAX_PEER_CONNECTIONS = 40


class TorrentClient:
    def __init__(self, torrent: Torrent):
        self.tracker = Tracker(torrent)
        self.peers = List[PeerConnection]
        self.available_peers = Queue()
        self.abort = False
        self.piece_manager = PieceManager(torrent)

    async def start(self):
        self.peers = [PeerConnection(self.available_peers, self.tracker.torrent.info_hash,
                                     self.tracker.peer_id, self.piece_manager,
                                     self._block_retrieved)
                      for _ in range(MAX_PEER_CONNECTIONS)]

        previous = None
        interval = 30 * 60 # Seconds

        while True:
            #TODO
            if self.abort:
                logging.info("INFO: Torrent is downloaded")
                break

            cur_time = time.time()
            if not previous or previous + interval < cur_time:
                response = await self.tracker.connect(
                    # TODO uncomment when piece_manager will be implemented
                    # uploaded=self.piece_manager.bytes_uploaded,
                    # downloaded=self.piece_manager.bytes_downloaded,
                    first_call=previous if previous else False
                )

                print('TRACKER RESPONSE:')
                print(response.response)

                if response:
                    previous = cur_time
                    interval = response.interval

                    self._empty_queue()

                    for peer in response.peers:
                        self.available_peers.put_nowait(peer) # Put an item into the queue without blocking.
            else:
                await sleep(5)

        await self.stop()


    def stop(self) -> None:
        self.abort = True

        for peer in self.peers:
            peer.stop()

        #TODO close piece_manager

        self.tracker.close()

    def _empty_queue(self) -> None:
        while not self.available_peers.empty():
            self.available_peers.get_nowait()   # Remove and return an item from the queue

    def _block_retrieved(self, peer_id: str, piece_index, block_offset, data) -> None:
    #TODO piece_manager





    async def stop(self):
        await self.tracker.close()




class PieceManager:
    def __init__(self, torrent: Torrent):
        self.torrent = torrent


