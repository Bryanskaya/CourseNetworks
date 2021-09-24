from asyncio import Queue
from typing import Callable

import logging
import asyncio

from client import PieceManager


STOPPED = 'stopped'
CHOKED = 'choked'


class PeerConnection:
    def __init__(self, queue: Queue, info_hash: bytes, peer_id: str,
                 piece_manager: PieceManager, block_cb: Callable[[str, None, None, None], None]): #TODO 3x None
        self.own_state = [] #TODO why array
        self.peer_state = []
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.remote_id = None
        self.writer = None
        self.reader = None
        self.piece_manager = piece_manager
        self.block_cb = block_cb  # Callback function. It is called when block is received from the remote peer.
        #TODO self.future

    async def _start(self):
        while STOPPED not in self.own_state:
            ip, port = await self.queue.get() #TODO why get returns ip/port

            logging.info("INFO: assigned peer, id = " + ip)

            try:
                #TODO look at the comment in real src
                self.reader, self.writer = await asyncio.open_connection(ip, port)
                logging.info("INFO: connection was opened, ip = " + ip)

                #TODO handshake

                #TODO comment in real src

                self.own_state.append(CHOKED)


    def stop(self) -> None:
        self.own_state.append(STOPPED)
        #TODO smth with future
