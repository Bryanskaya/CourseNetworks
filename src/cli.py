import asyncio
import logging

from torfile import Torrent
from client import TorrentClient

FNAME = 'tor.torrent'

logging.basicConfig(level=logging.INFO, filename='info.log', filemode='w',
                    format='%(asctime)s %(levelname)s:%(message)s')


def main():
    loop = asyncio.get_event_loop()
    client = TorrentClient(Torrent(FNAME))
    task = loop.create_task(client.start())

    try:
        loop.run_until_complete(task)
    except:
        logging.info(" event loop was cancelled")


if __name__ == '__main__':
    main()
