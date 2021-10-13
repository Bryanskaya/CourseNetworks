import asyncio
import logging

from torfile import Torrent
from client import TorrentClient

FNAME = 'tor.torrent'
log_lvl = logging.DEBUG

logging.basicConfig(level=log_lvl, filename='info.log', filemode='w',
                    format='%(asctime)s %(levelname)s: %(message)s')


def main():
    run_loading(FNAME, './')


def run_loading(tor_path: str, file_path: str):
    # loop = asyncio.get_event_loop()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TorrentClient(Torrent(tor_path), file_path)
    task = loop.create_task(client.start())

    try:
        loop.run_until_complete(task)
    except:
        logging.info(" event loop was cancelled")


if __name__ == '__main__':
    main()
