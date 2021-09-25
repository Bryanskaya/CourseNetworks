from asyncio import Queue
from typing import Callable

import logging
import asyncio
import struct

from piece_man import PieceManager


STOPPED = 'stopped'
CHOKED = 'choked'


class PeerConnection:
    remote_id = None
    writer: asyncio.StreamWriter = None
    reader: asyncio.StreamReader = None

    def __init__(self, queue: Queue, info_hash: bytes, peer_id: str,
                 piece_manager: PieceManager, block_cb: Callable[[str, None, None, None], None]): #TODO 3x None
        self.state = set()
        self.peer_state = set()
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.block_cb = block_cb  # Callback function. It is called when block is received from the remote peer.
        self.future = asyncio.ensure_future(self._start())

    async def _start(self):
        while STOPPED not in self.state:
            ip, port = await self.queue.get()
            print("Grab", ip, port)
            logging.info(" assigned peer, id = " + ip)

            try:
                #TODO look at the comment in real src
                self.reader, self.writer = await asyncio.open_connection(ip, port)
                logging.info(" connection was opened, ip = " + ip)

                buf = await self._do_handshake()
                self.state.add(CHOKED)

                #TODO comment in real src

            except Exception as e:
                print("Exception!", str(e))
                logging.exception(e)
                self.cancel()
                raise e
            self.cancel()

    def cancel(self):
        logging.info(' closing peer {ip}'.format(ip=self.remote_id))
        if not self.future.done():
            self.future.cancel()
        if self.writer:
            self.writer.close()
        # TODO self.reader.close()

        self.queue.task_done()

    def stop(self) -> None:
        self.state.append(STOPPED)
        #TODO smth with future


    async def _do_handshake(self):
        self.writer.write(Handshake(self.info_hash, self.peer_id).encode())
        await self.writer.drain()

        buf = b''
        tries = 0
        while len(buf) < Handshake.length and tries < 10:
            tries += 1
            buf = await self.reader.read(PeerStreamIterator.CHUNK_SIZE)

        response = Handshake.decode(buf)
        if response is None:
            raise Exception()  # TODO protocol error (handshake are unable)
        elif response.info_hash != self.info_hash:
            raise Exception()  # TODO protocol error (invalid info_hash)

        self.remote_id = response.peer_id
        logging.info('handshake with peer {} are successful'.format(self.remote_id))

        return buf[Handshake.length:]


class PeerStreamIterator:
    CHUNK_SIZE = 10 * 1024

    def __init__(self, reader, initial: bytes = None):
        self.reader = reader
        self.buffer = initial if initial else b''


class PeerMessage:
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    BitField = 5
    Request = 6
    Piece = 7
    Cancel = 8
    Port = 9
    Handshake = None  # not part of the messages
    KeepAlive = None


class Handshake(PeerMessage):
    pname = b'BitTorrent protocol'
    length = 49 + len(pname)
    msg_struct = '>B19s8x20s20s'

    def __init__(self, info_hash: bytes, peer_id: str):  #TODO bytes/str
        if isinstance(info_hash, str):
            info_hash = info_hash.encode('utf-8')
        if isinstance(peer_id, str):
            peer_id = peer_id.encode('utf-8')

        self.info_hash = info_hash
        self.peer_id = peer_id

    def encode(self) -> bytes:
        return struct.pack(
            self.msg_struct,
            len(self.pname),            # Single byte (B)
            self.pname,                 # String 19s
                                        # Reserved 8x (pad byte, no value)
            self.info_hash,             # String 20s
            self.peer_id                # String 20s
        )

    @classmethod
    def decode(cls, data: bytes):
        data = data[:Handshake.length]
        logging.debug('decoding handshake: {}'.format(data))
        if len(data) != Handshake.length:
            return None
        fields = struct.unpack(cls.msg_struct, data)
        return cls(fields[2], fields[3])

    def __str__(self):
        return 'Handshake'
