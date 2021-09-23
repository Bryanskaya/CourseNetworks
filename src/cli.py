import asyncio
import logging

from torfile import Torrent
from client import TorrentClient

FNAME = 'tor.torrent'

def main():
    client = TorrentClient(Torrent(FNAME))


if __name__ == '__main__':
    main()