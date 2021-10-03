from asyncio import Queue
from typing import Callable

import logging
import asyncio
import concurrent
import struct

from piece_man import PieceManager
from peer_msg import *


class PeerState(object):
    def __init__(self):
        self.is_stopped = False
        self.is_choked = True
        self.is_interested = True
        self.is_pending = False

    def stop(self):     self.is_stopped = True
    def choke(self):    self.is_choked = True
    def unchoke(self):  self.is_choked = False
    def interest(self): self.is_interested = True
    def uninterest(self): self.is_interested = False
    def start_pending(self): self.is_pending = True
    def stop_pending(self): self.is_pending = False


class OtherPeerState(PeerState):
    def __init__(self):
        super().__init__()
        self.is_choked = False
        self.is_interested = False


class PeerConnection:
    remote_id = None
    writer: asyncio.StreamWriter = None
    reader: asyncio.StreamReader = None

    def __init__(self, id: int, queue: Queue, info_hash: bytes, peer_id: str,
                 piece_manager: PieceManager, block_cb: Callable[[str, int, int, bytes], None]):
        self.state = PeerState()
        self.peer_state = OtherPeerState()

        self.id = id
        self.queue = queue
        self.info_hash = info_hash
        self.peer_id = peer_id
        self.piece_manager = piece_manager
        self.block_cb = block_cb  # Callback function. It is called when block is received from the remote peer.
        self.future = asyncio.ensure_future(self._start())

    def _log(self, lvl: int, msg: str = ''): logging.log(lvl, '|CONID {:2d}| '.format(self.id) + msg)
    def _info(self, msg: str): self._log(logging.INFO, msg)
    def _warn(self, msg: str): self._log(logging.WARN, msg)
    def _debug(self, msg: str): self._log(logging.DEBUG, msg)
    def _exep(self, exp: Exception):
        self._log(logging.ERROR)
        logging.exception(exp)

    async def _start(self):
        while not self.state.is_stopped:
            ip, port = await self.queue.get()
            self._info("assigned peer, ip = {}".format(ip))

            try:
                #TODO look at the comment in real src
                self.reader, self.writer = await asyncio.open_connection(ip, port)
                self._info("connection was opened, ip = " + ip)

                buf = await self._do_handshake()
                await self._send_interested()

                async for msg in PeerStreamIterator(self.reader, buf):
                    print(msg)
                    self._info("received {}".format(str(msg)))
                    if self.state.is_stopped:
                        break

                    await self._process_response(msg)
                    await self._create_message()

                    #TODO comment in real src

            except concurrent.futures._base.CancelledError as exp:
                print("Exception!!!")
                print(exp)
                logging.error("сейчас будет error")
                self._exep(exp)
                logging.error("ну вот")
                await self.cancel()
                raise exp

            except Exception as exp:
                print("Exception!")
                print(exp)
                logging.error("сейчас будет error")
                self._exep(exp)
                logging.error("ну вот")
                await self.cancel()
                raise exp
            self._info('Out of loop')
            await self.cancel()

    async def _process_response(self, msg: PeerMessage):
        if type(msg) is BitFieldMsg:
            msg: BitFieldMsg
            self.piece_manager.add_peer(self.remote_id, msg.bitfield)
        elif type(msg) is InterestedMsg:
            self.peer_state.interest()
        elif type(msg) is NotInterestedMsg:
            self.peer_state.uninterest()
        elif type(msg) is ChokeMsg:
            self.state.choke()
        elif type(msg) is UnchokeMsg:
            self.state.unchoke()
        elif type(msg) is HaveMsg:
            msg: HaveMsg
            self.piece_manager.update_peer(self.remote_id, msg.index)
        elif type(msg) is KeepAliveMsg:
            pass
        elif type(msg) is PieceMsg:
            msg: PieceMsg
            self.state.stop_pending()
            self.block_cb(
                self.remote_id,
                msg.index,
                msg.begin,
                msg.block
            )
        elif type(msg) is RequestMsg:
            pass
        elif type(msg) is CancelMsg:
            pass

    async def _create_message(self):
        if (not self.state.is_choked) and self.state.is_interested and (not self.state.is_pending):
            self.state.start_pending()
            success = await self._request_piece()
            if not success:
                self.state.stop_pending()

    async def cancel(self):
        self._info('closing peer {ip}'.format(ip=self.remote_id))
        if not self.future.done():
            pass # self.future.cancel()
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

        self.queue.task_done()

    def stop(self) -> None:
        self.state.stop()
        if not self.future.done():
            self.future.cancel()

    async def _do_handshake(self) -> bytes:
        self.writer.write(HandshakeMsg(self.info_hash, self.peer_id).encode())
        await self.writer.drain()

        buf = b''
        tries = 0
        while len(buf) < HandshakeMsg.length and tries < 10:
            tries += 1
            buf += await self.reader.read(PeerStreamIterator.CHUNK_SIZE)
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

    async def _request_piece(self) -> bool:
        block = self.piece_manager.next_request(self.remote_id)
        if block is None:
            return False

        msg = RequestMsg(block.piece, block.offset, block.length).encode()

        self._debug('Requesting block {} of piece {} from {}'.
                    format(block.offset, block.piece, self.remote_id))

        self.writer.write(msg)
        await self.writer.drain()
        return True


class PeerStreamIterator:
    CHUNK_SIZE = 10 * 1024

    def __init__(self, reader, initial: bytes = b''):
        self.reader = reader
        self.buffer = initial

    def __aiter__(self):
        return self

    async def __anext__(self) -> PeerMessage:
        while True:
            try:
                data = await self.reader.read(PeerStreamIterator.CHUNK_SIZE)
            except ConnectionResetError:
                logging.debug("Connection was closed by peer")
                raise StopAsyncIteration
            except Exception as exc:
                logging.exception('Error when iterating over stream!')
                raise StopAsyncIteration

            if data:
                self.buffer += data
                msg = self.parse()
                if msg: return msg
            else:
                logging.debug("There is no data to read from stream")

                if self.buffer:
                    msg = self.parse()
                    if msg: return msg  # TODO strange
                break

        raise StopAsyncIteration

    def parse(self):
        header_len = 4
        msg_struct_UnInt = '>I'
        msg_struct_SChar = '>b'

        if len(self.buffer) > 4:    # 4 - The `length prefix` is a four byte big-endian value. To identify the message
            msg_len = struct.unpack(
                msg_struct_UnInt,
                self.buffer[:4]
            )[0]

            if not msg_len:
                self.buffer = self.buffer[4:]
                return KeepAliveMsg()

            if len(self.buffer) >= msg_len:
                msg_id = struct.unpack(
                    msg_struct_SChar,
                    self.buffer[4:5]
                )[0]

                def _get_data():
                    return self.buffer[: header_len + msg_len]

                def _fix_buf():
                    self.buffer = self.buffer[header_len + msg_len :]

                if msg_id is BitFieldMsg.id:
                    data = _get_data()
                    _fix_buf()
                    return BitFieldMsg.decode(data)
                if msg_id is InterestedMsg.id:
                    _fix_buf()
                    return InterestedMsg()
                if msg_id is NotInterestedMsg.id:
                    _fix_buf()
                    return NotInterestedMsg()
                if msg_id is ChokeMsg.id:
                    _fix_buf()
                    return ChokeMsg()
                if msg_id is UnchokeMsg.id:
                    _fix_buf()
                    return UnchokeMsg()
                if msg_id is HaveMsg.id:
                    data = _get_data()
                    _fix_buf()
                    return HaveMsg.decode(data)
                if msg_id is PieceMsg.id:
                    data = _get_data()
                    _fix_buf()
                    return PieceMsg.decode(data)
                if msg_id is RequestMsg.id:
                    data = _get_data()
                    _fix_buf()
                    return RequestMsg.decode(data)
                if msg_id is CancelMsg.id:
                    data = _get_data()
                    _fix_buf()
                    return CancelMsg.decode(data)

                logging.info("Message {} is not defined".format(msg_id))
            else:
                logging.debug('Not enough space in buffer to parse')

        return None