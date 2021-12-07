import xbmc


class PlayerClient:
    def __init__(self, config):
        self.current = None
        self.database = None
        self.config = config
        self.playmode = PlayMode()
        self.playlist = Playlist()
        self.xbmc_playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        self.xbmc_player = XBMCPlayer(self)
        self.queue = self.playlist
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

    @property
    def state(self):
        if self.xbmc_player.isPlayingAudio():
            return 'play'

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
            self.player.onAvStarted()

    def onAVChange(self) -> None:
        self.player.onAvChange()

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



class Playlist:
    def __init__(self):
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

    def __len__(self):
        return self.playlist.size()


class PlayerError(BaseException):
    pass

