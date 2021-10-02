import bencodepy
from hashlib import sha1


class TorFile(object):
    name = ''
    length = 0

    def __init__(self, file_dict: dict):
        self.name = file_dict[b'name'].decode('utf-8')
        self.length = file_dict[b'length']


class Torrent(object):
    content = {}
    file: TorFile = None
    info_hash = None

    def __init__(self, f_name: str):
        with open(f_name, 'rb') as file:
            self.content = bencodepy.decode(file.read())

        info = bencodepy.encode(self.content[b'info'])
        self.info_hash = sha1(info).digest()
        self.file = TorFile(self.content[b'info'])

    @property
    def announce(self) -> str:
        return self.content[b'announce'].decode('utf-8')

    @property
    def total_size(self) -> int:
        return self.file.length

    @property
    def pieces(self):
        data = self.content[b'info'][b'pieces']
        pieces = []
        offset = 0
        length = len(data)

        while offset < length:
            pieces.append(data[offset: offset + 20])   # The info pieces is a string representing all pieces SHA1 hashes (each 20 bytes long)
            offset += 20

        return pieces

    @property
    def piece_length(self) -> int:
        return self.content[b'info'][b'piece length']

    @property
    def output_file(self):
        return self.content[b'info'][b'name'].decode('utf-8')


if __name__ == "__main__":
    Torrent('tor.torrent')
