from torfile import Torrent
from tracker import Tracker


class TorrentClient:
    def __init__(self, torrent: Torrent):
        self.tracker = Tracker(torrent)

    async def start(self):
        previous = None

        response = await self.tracker.connect(
            # TODO uncomment when piece_manager will be implemented
            # uploaded=self.piece_manager.bytes_uploaded,
            # downloaded=self.piece_manager.bytes_downloaded,
            first_call=previous if previous else False
        )
        print('TRACKER RESPONSE:')
        print(response.response)

        await self.stop()

    async def stop(self):
        await self.tracker.close()
