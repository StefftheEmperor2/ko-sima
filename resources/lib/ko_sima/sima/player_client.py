import xbmc
import web_pdb

class PlayerClient:
    needed_tags = {'Artist', 'Album', 'AlbumArtist', 'Title', 'Track'}
    MPD_supported_tags = {'Artist', 'ArtistSort', 'Album', 'AlbumSort', 'AlbumArtist',
                          'AlbumArtistSort', 'Title', 'Track', 'Name', 'Genre',
                          'Date', 'OriginalDate', 'Composer', 'Performer',
                          'Conductor', 'Work', 'Grouping', 'Disc', 'Label',
                          'MUSICBRAINZ_ARTISTID', 'MUSICBRAINZ_ALBUMID',
                          'MUSICBRAINZ_ALBUMARTISTID', 'MUSICBRAINZ_TRACKID',
                          'MUSICBRAINZ_RELEASETRACKID', 'MUSICBRAINZ_WORKID'}
    needed_mbid_tags = {'MUSICBRAINZ_ARTISTID', 'MUSICBRAINZ_ALBUMID',
                        'MUSICBRAINZ_ALBUMARTISTID', 'MUSICBRAINZ_TRACKID'}
    mpd_version = '0.22.0'
    def __init__(self, core):
        self.current = None
        self.database = None
        self.core = core
        self.config = core.config
        self.playmode = PlayMode()
        self.playlist = Playlist(core)
        self.xbmc_playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        self.xbmc_player = XBMCPlayer(self)
        self.queue = PlayQueue()
        self.is_exiting = False
        self.idle = []
        self.xbmc_monitor = xbmc.Monitor()

    def onAVStarted(self) -> None:
        self.idle.append('player')

    def onAVChange(self) -> None:
        self.idle.append('player')

    def onPlayBackPaused(self) -> None:
        self.idle.append('player')

    def onPlayBackResumed(self) -> None:
        self.idle.append('player')

    def onPlayBackStopped(self) -> None:
        self.idle.append('player')

    def onPlayBackEnded(self) -> None:
        self.idle.append('player')

    def add(self, track):
        self.xbmc_playlist.add(track.file)

    def connect(self):
        pass

    def disconnect(self):
        pass

    def clean(self):
        pass

    def delete(self, pos):
        self.xbmc_playlist.remove(self.xbmc_playlist[pos].getMusicInfoTag().getURL())

    @property
    def state(self):
        if self.xbmc_player.isPlayingAudio():
            return 'play'

    def currentsong(self):
        if self.state == 'play':
            current_playing_item = self.core.get_item_as_track(self.xbmc_player.getMusicInfoTag())
            if self.xbmc_playlist:
                current_playing_item.pos = int(self.xbmc_playlist.getposition())
            return current_playing_item
        return None

    def fetch_idle(self):
        idle = []
        while len(self.idle):
            idle.append(self.idle.pop(0))
        return self.idle

    def monitor(self):
        while len(self.idle) == 0:
            if self.is_exiting or self.xbmc_monitor.abortRequested():
                break
            self.xbmc_monitor.waitForAbort(1)
        return self.fetch_idle()


class XBMCPlayer(xbmc.Player):
    def __init__(self, player):
        super(XBMCPlayer, self).__init__()
        self.player = player

    def onAVStarted(self) -> None:
        if self.isPlayingAudio():
            self.player.onAVStarted()

    def onAVChange(self) -> None:
        self.player.onAVChange()

    def onPlayBackPaused(self) -> None:
        self.player.onPlayBackPaused()

    def onPlayBackResumed(self) -> None:
        self.player.onPlayBackResumed()

    def onPlayBackStopped(self) -> None:
        self.player.onPlayBackStopped()

    def onPlayBackEnded(self) -> None:
        self.player.onPlayBackEnded()

class PlayMode:
    def get(self, prop):
        if prop == 'random':
            return xbmc.getCondVisibility('Playlist.IsRandom')
        if prop == 'single':
            return xbmc.getCondVisibility('Playlist.IsRepeatOne')
        if prop == 'repeat':
            return xbmc.getCondVisibility('Playlist.IsRepeat')

class PlayQueue:
    def __init__(self):
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

    def __len__(self):
        return self.playlist.size() - self.playlist.getposition()


class Playlist:
    def __init__(self, core):
        self.core = core
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

    def __len__(self):
        return self.playlist.size()

    def __getitem__(self, item):
        return self.core.get_item_as_track(self.playlist.__getitem__(item).getMusicInfoTag())


class PlayerError(BaseException):
    pass

