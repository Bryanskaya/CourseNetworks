import logging
import struct
import bitstring

REQUEST_SIZE = 2**14    # The default request size for blocks of pieces is 2^14 bytes.


class PeerMessage(object):
    id: int
    msg_struct: str

    def action(self, actor):
        print('they called me')

    def encode(self) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, data: bytes):
        raise NotImplementedError


class ChokeMsg(PeerMessage):
    id = 0


class UnchokeMsg(PeerMessage):
    id = 1


class InterestedMsg(PeerMessage):
    id = 2
    msg_struct = '>Ib'

    def encode(self) -> bytes:
        return struct.pack(
            self.msg_struct,
            1,
            InterestedMsg.id
        )

    @classmethod
    def decode(cls, data: bytes):
        return InterestedMsg()


class NotInterestedMsg(PeerMessage):
    id = 3


class HaveMsg(PeerMessage):
    id = 4

    def __init__(self, index: int):
        self.index = index

    @classmethod
    def decode(cls, data: bytes):
        msg_struct = '>IbI'

        logging.debug('Decoding Have of length: {}'.format(len(data)))
        ind = struct.unpack(msg_struct, data)[2]

        return cls(ind)

    def __str__(self):
        return 'Have'


class BitFieldMsg(PeerMessage):
    id = 5

    def __init__(self, data: bytes):
        self.bitfield = bitstring.BitArray(data)

    @classmethod
    def decode(cls, data: bytes):
        msg_struct_UnInt = '>I'
        msg_struct_UnIntSChar = '>Ib'

        msg_len = struct.unpack(
            msg_struct_UnInt,
            data[: 4]
        )[0]

        logging.debug('Decoding BitField of length: {}'.format(msg_len))

        parts = struct.unpack(msg_struct_UnIntSChar + str(msg_len - 1) + 's', data)
        return cls(parts[2])

    def __str__(self):
        return 'BitField'


class RequestMsg(PeerMessage):
    id = 6
    msg_struct = '>IbIII'

    def __init__(self, index: int, begin: int, length: int = REQUEST_SIZE):
        self.index = index
        self.begin = begin
        self.length = length

    def encode(self) -> bytes:
        return struct.pack(
            self.msg_struct,
            13,
            self.id,
            self.index,
            self.begin,
            self.length
        )

    @classmethod
    def decode(cls, data: bytes):
        logging.debug('Decoding Request of length: {}'.format(len(data)))
        parts = struct.unpack(
            cls.msg_struct,
            data)

        return cls(parts[2], parts[3], parts[4])

    def __str__(self):
        return 'Request'


class PieceMsg(PeerMessage):
    id = 7

    msg_len = 9

    def __init__(self, index: int, begin: int, block: bytes):
        self.index = index
        self.begin = begin
        self.block = block

    @classmethod
    def decode(cls, data: bytes):
        msg_struct_UnInt = '>I'
        msg_struct = '>IbII'

        # TODO change to method
        logging.debug('Decoding Piece of length: {}'.format(len(data)))
        length = struct.unpack(
            msg_struct_UnInt,
            data[: 4])[0]
        parts = struct.unpack(
            msg_struct + str(length - PieceMsg.msg_len) + 's',
            data[: length + 4])

        return cls(parts[2], parts[3], parts[4])

    def __str__(self):
        return 'PieceMsg'


class CancelMsg(PeerMessage):
    id = 8

    def __init__(self, index: int, begin: int, length: int = REQUEST_SIZE):
        self.index = index
        self.begin = begin
        self.length = length

    @classmethod
    def decode(cls, data: bytes):
        msg_struct = '>IbIII'

        logging.debug('Decoding Cancel of length: {}'.format(len(data)))

        parts = struct.unpack(
            msg_struct,
            data)

        return cls(parts[2], parts[3], parts[4])

    def __str__(self):
        return 'Cancel'


class PortMsg(PeerMessage):
    id = 9


class HandshakeMsg(PeerMessage):
    id = None

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
        data = data[:cls.length]
        if len(data) != cls.length:
            return None
        fields = struct.unpack(cls.msg_struct, data)

        return cls(fields[2], fields[3])

    def __str__(self):
        return 'Handshake'


class KeepAliveMsg(PeerMessage):
    id = None

    def __str__(self):
        return 'KeepAlive'