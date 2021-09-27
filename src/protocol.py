from asyncio import Queue
from typing import Callable

import logging
import asyncio
import struct

from piece_man import PieceManager
from peer_msg import *


class PeerState(object):
    is_stopped = False
    is_choked = True
    is_interested = True

    def stop(self):     self.is_stopped = True
    def choke(self):    self.is_choked = True
    def unchoke(self):  self.is_choked = False
    def interest(self): self.is_interested = True
    def uninterest(self): self.is_interested = False


class PeerConnection:
    remote_id = None
    writer: asyncio.StreamWriter = None
    reader: asyncio.StreamReader = None

    def __init__(self, id: int, queue: Queue, info_hash: bytes, peer_id: str,
                 piece_manager: PieceManager, block_cb: Callable[[str, None, None, None], None]): #TODO 3x None
        self.id = id
        self.state = PeerState()
        self.peer_state = set()
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.block_cb = block_cb  # Callback function. It is called when block is received from the remote peer.
        self.future = asyncio.ensure_future(self._start())

    def _log(self, lvl: int, msg: str = ''): logging.log(lvl, '|CONID {}| '.format(self.id) + msg)
    def _info(self, msg: str): self._log(logging.INFO, msg)
    def _warn(self, msg: str): self._log(logging.WARN, msg)
    def _debug(self, msg: str): self._log(logging.DEBUG, msg)
    def _exep(self, exp: Exception):
        self._log(logging.ERROR)
        logging.exception(exp)

    async def _start(self):
        while not self.state.is_stopped:
            ip, port = await self.queue.get()
            self._info(" assigned peer, ip = {}".format(ip))

            try:
                #TODO look at the comment in real src
                self.reader, self.writer = await asyncio.open_connection(ip, port)
                self._info(" connection was opened, ip = " + ip)

                buf = await self._do_handshake()
                await self._send_interested()

                #TODO comment in real src

            except Exception as e:
                print("Exception!", str(e))
                self._exep(e)
                self.cancel()
                raise e
            self.cancel()

    def cancel(self):
        self._info('closing peer {ip}'.format(ip=self.remote_id))
        if not self.future.done():
            self.future.cancel()
        if self.writer:
            self.writer.close()
        # TODO self.reader.close()

        self.queue.task_done()

    def stop(self) -> None:
        self.state.stop()
        #TODO smth with future

    async def _do_handshake(self) -> bytes:
        self.writer.write(HandshakeMsg(self.info_hash, self.peer_id).encode())
        await self.writer.drain()

        buf = b''
        tries = 0
        while len(buf) < HandshakeMsg.length and tries < 10:
            tries += 1
            buf = await self.reader.read(PeerStreamIterator.CHUNK_SIZE)
            # TODO read length of handshake message instead of chunk size => return value is None

        response = HandshakeMsg.decode(buf)
        if response is None:
            raise Exception()  # TODO protocol error (handshake are unable)
        elif response.info_hash != self.info_hash:
            raise Exception()  # TODO protocol error (invalid info_hash)

        self.remote_id = response.peer_id
        self._debug('handshake with peer {} are successful'.format(self.remote_id))

        return buf[HandshakeMsg.length:]

    async def _send_interested(self) -> None:
        msg = InterestedMsg()
        self.writer.write(msg.encode())
        await self.writer.drain()
        self._debug('sending interested msg to {}'.format(self.remote_id))


class PeerStreamIterator:
    CHUNK_SIZE = 10 * 1024

    def __init__(self, reader, initial: bytes = b''):
        self.reader = reader
        self.buffer = initial
