import asyncio
import logging

from torfile import Torrent
from client import TorrentClient

FNAME = 'tor.torrent'


def main():
    loop = asyncio.get_event_loop()
    client = TorrentClient(Torrent(FNAME))
    task = loop.create_task(client.start())

    try:
        loop.run_until_complete(task)
    except:
        logging.info("INFO: event loop was cancelled")


if __name__ == '__main__':
    main()
