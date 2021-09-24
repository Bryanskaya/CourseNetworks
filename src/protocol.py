from asyncio import Queue
from typing import Callable

import logging
import asyncio

from piece_man import PieceManager


STOPPED = 'stopped'
CHOKED = 'choked'


class PeerConnection:
    remote_id = None
    writer: asyncio.StreamWriter = None
    reader: asyncio.StreamReader = None

    def __init__(self, queue: Queue, info_hash: bytes, peer_id: str,
                 piece_manager: PieceManager, block_cb: Callable[[str, None, None, None], None]): #TODO 3x None
        self.state = [] # TODO why array
        self.peer_state = []
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.block_cb = block_cb  # Callback function. It is called when block is received from the remote peer.
        self.future = asyncio.ensure_future(self._start())

    async def _start(self):
        while STOPPED not in self.state:
            ip, port = await self.queue.get()  # TODO why get returns ip/port
            print("Grab", ip, port)
            logging.info("INFO: assigned peer, id = " + ip)

            try:
                #TODO look at the comment in real src
                self.reader, self.writer = await asyncio.open_connection(ip, port)
                logging.info("INFO: connection was opened, ip = " + ip)

                #TODO handshake

                #TODO comment in real src

                self.state.append(CHOKED)
            except Exception as e:
                print("Exception!", str(e))
                logging.exception('Exception: ' + str(e))
                self.cancel()
                raise e
            self.cancel()

    def cancel(self):
        logging.info('Closing peer {id}'.format(id=self.remote_id))
        if not self.future.done():
            self.future.cancel()
        if self.writer:
            self.writer.close()

        self.queue.task_done()

    def stop(self) -> None:
        self.state.append(STOPPED)
        #TODO smth with future
