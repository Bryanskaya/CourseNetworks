import logging
import struct


class PeerMessage(object):
    id: int
    msg_struct: str

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


class BitFieldMsg(PeerMessage):
    id = 5


class RequestMsg(PeerMessage):
    id = 6


class PieceMsg(PeerMessage):
    id = 7


class CancelMsg(PeerMessage):
    id = 8


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
