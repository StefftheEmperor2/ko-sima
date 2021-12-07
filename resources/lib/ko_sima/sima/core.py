import importlib.util
import xbmc
import xbmcaddon
import xbmcvfs
import sys
import time
from os.path import isfile
from os import path
from importlib import __import__ as sima_import
from .player_client import PlayerClient, PlayerError
from collections import deque
from .log import Log
from .config import Config
import web_pdb

MODULE_NAME = "sima"
addon_base_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
mpd_sima_path = path.join(addon_base_path, 'resources', 'lib', 'mpd-sima', 'sima', '__init__.py')
xbmc.log(mpd_sima_path)
sima_spec = importlib.util.spec_from_file_location(MODULE_NAME, mpd_sima_path)
mpdSima = importlib.util.module_from_spec(sima_spec)
sys.modules[MODULE_NAME] = mpdSima
sima_spec.loader.exec_module(mpdSima)

MUSICPD_MODULE_NAME = 'musicpd'
musicpd_path = path.join(addon_base_path, 'resources', 'lib', 'ko_sima', 'sima', 'mpd_stubs', 'musicpd.py')
musicpd_spec = importlib.util.spec_from_file_location(MUSICPD_MODULE_NAME, musicpd_path)
musicpd = importlib.util.module_from_spec(musicpd_spec)
sys.modules[MUSICPD_MODULE_NAME] = musicpd
musicpd_spec.loader.exec_module(musicpd)

# core plugins
from sima.plugins.core.history import History
from sima.plugins.core.mpdoptions import MpdOptions
from sima.plugins.core.uniq import Uniq
from sima.lib.simadb import SimaDB
from sima.lib.track import Track


def load_plugins(sima, source):
    """Handles internal/external plugins
        sima:   sima.core.Sima instance
        source: ['internal', 'contrib']
    """# pylint: disable=logging-not-lazy,logging-format-interpolation

    logger = sima.log
    # TODO: Sanity check for "sima.config.get('sima', source)" ?
    for plugin in sima.get_plugins(source):
        plugin = plugin.strip(' \n')
        module = f'sima.plugins.{source}.{plugin.lower()}'
        try:
            mod_obj = sima_import(module, fromlist=[plugin])
        except ImportError as err:
            logger.error(f'Failed to load "{plugin}" plugin\'s module: ' +
                         f'{module} ({err})')
            sima.shutdown()
            return
        try:
            plugin_obj = getattr(mod_obj, plugin)
        except AttributeError as err:
            logger.error('Failed to load plugin %s (%s)', (plugin, err))
            sima.shutdown()
            sys.exit(1)
        logger.info('Loading {0} plugin: {name} ({doc})'.format(
            source, **plugin_obj.info()))
        sima.register_plugin(plugin_obj)


class KoSima:
    """Main class, plugin and player management
    """

    def __init__(self):
        # Set daemon
        self.enabled = True
        self.log = Log()
        profile_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))

        if not xbmcvfs.exists(path.join(profile_path, '')):
            xbmcvfs.mkdirs(profile_path)

        db_file = path.join(profile_path, 'ko_sima.db')
        if not isfile(db_file):
            self.log.debug('Creating database in "%s"', db_file)
            SimaDB(db_path=db_file).create_db()

        self.sdb = SimaDB(db_path=db_file)
        PlayerClient.database = self.sdb
        self.config = Config()
        self._plugins = []
        self._core_plugins = []
        self.player = PlayerClient(self)
        self.short_history = deque(maxlen=60)
        self.changed = None
        self.xbmc_monitor = xbmc.Monitor()
        self.is_exiting = False

    def get_item_as_track(self, music_info):
        track = Track(file=music_info.getURL(), duration=music_info.getDuration())
        track.artist = music_info.getArtist()
        track.title = music_info.getTitle()
        track.album = music_info.getAlbum()
        track.albumartist = music_info.getAlbumArtist()
        track.genre = music_info.getGenre()
        track.musicbrainz_artistid = music_info.getMusicBrainzArtistID()
        track.musicbrainz_albumartistid = music_info.getMusicBrainzAlbumArtistID()
        track.musicbrainz_albumid = music_info.getMusicBrainzAlbumID()
        track.musicbrainz_trackid = music_info.getMusicBrainzTrackID()
        return track

    def load_plugins(self):
        # required core plugins
        core_plugins = [History, MpdOptions]
        for core_plugin in core_plugins:
            self.log.debug('Register core %(name)s (%(doc)s)', core_plugin.info())
            self.register_core_plugin(core_plugin)
        self.log.debug('core loaded, prioriy: %s',
                     ' > '.join(map(str, self.core_plugins)))

        #  Loading internal plugins
        load_plugins(self, 'internal')
        #  Loading contrib plugins
        load_plugins(self, 'contrib')
        self.log.info('plugins loaded, prioriy: %s', ' > '.join(map(str, self.plugins)))

    def add_history(self):
        """Handle local, in memory, short history"""
        self.short_history.appendleft(self.player.current)

    def register_plugin(self, plugin_class):
        """Registers plugin in Sima instance..."""
        plgn = plugin_class(self)
        prio = int(plgn.priority)
        self._plugins.append((prio, plgn))

    def register_core_plugin(self, plugin_class):
        """Registers core plugins"""
        plgn = plugin_class(self)
        prio = int(plgn.priority)
        self._core_plugins.append((prio, plgn))

    def foreach_plugin(self, method, *args, **kwds):
        """Plugin's callbacks dispatcher"""
        self.log.trace('dispatching %s to plugins', method)  # pylint: disable=no-member
        for plugin in self.core_plugins:
            getattr(plugin, method)(*args, **kwds)
        for plugin in self.plugins:
            getattr(plugin, method)(*args, **kwds)

    @property
    def core_plugins(self):
        return [plugin[1] for plugin in
                sorted(self._core_plugins, key=lambda pl: pl[0], reverse=True)]

    @property
    def plugins(self):
        return [plugin[1] for plugin in
                sorted(self._plugins, key=lambda pl: pl[0], reverse=True)]

    def get_plugins(self, source):
        if source == 'internal':
            return ['Crop', 'Genre', 'Lastfm', 'Random']
        if source == 'contrib':
            return []

    def need_tracks(self):
        """Is the player in need for tracks"""
        if not self.enabled:
            self.log.debug('Queueing disabled!')
            return False
        queue_trigger = self.config.getint('sima', 'queue_length')
        if self.player.playmode.get('random'):
            queue = self.player.playlist
            self.log.debug('Currently %s track(s) in the playlist. (target %s)',
                           len(queue), queue_trigger)
        else:
            queue = self.player.queue
            self.log.debug('Currently %s track(s) ahead. (target %s)', (len(queue), queue_trigger))
        if len(queue) < queue_trigger:
            return True
        return False

    def queue(self):
        to_add = []
        for plugin in self.plugins:
            self.log.debug('callback_need_track: %s', plugin)
            web_pdb.set_trace()
            pl_candidates = getattr(plugin, 'callback_need_track')()
            if pl_candidates:
                to_add.extend(pl_candidates)
            if to_add:
                break
        for track in to_add:
            self.player.add(track)

    def reconnect_player(self):
        """Trying to reconnect cycling through longer timeout
        cycle : 5s 10s 1m 5m 20m 1h
        """
        sleepfor = [5, 10, 60, 300, 1200, 3600]
        # reset change
        self.changed = None
        while True:
            tmp = sleepfor.pop(0)
            sleepfor.append(tmp)
            self.log.info('Trying to reconnect in %4d seconds', tmp)
            time.sleep(tmp)
            try:
                self.player.connect()
            except PlayerError as err:
                self.log.debug(err)
                continue
            self.log.info('Got reconnected')
            break
        self.foreach_plugin('start')

    def hup_handler(self, signum, frame):
        self.log.warning('Caught a sighup!')
        # Cleaning pending command
        self.player.clean()
        self.foreach_plugin('shutdown')
        self.player.disconnect()

    def shutdown(self):
        """General shutdown method
        """
        self.log.warning('Starting shutdown.')
        # Cleaning pending command
        try:
            self.player.clean()
            self.foreach_plugin('shutdown')
            self.player.disconnect()
        except PlayerError as err:
            self.log.error('Player error during shutdown: %s', err)
        self.log.info('The way is shut, it was made by those who are dead. '
                      'And the dead keep it…')
        self.log.info('bye...')

    def run(self):
        try:
            self.log.info('Starting up')
            self.player.connect()
            self.foreach_plugin('start')
        except PlayerError as err:
            self.log.warning('Player: %s', err)
            self.reconnect_player()
        while 42:
            if self.xbmc_monitor.abortRequested():
                self.is_exiting = True
                self.player.is_exiting = True

            try:
                self.loop()
            except PlayerError as err:
                self.log.warning('Player error: %s', err)
                self.reconnect_player()

    def loop(self):
        """Dispatching callbacks to plugins
        """
        # hanging here until a monitored event is raised in the player
        if self.changed is None:  # first iteration goes through else
            self.changed = ['playlist', 'player', 'skipped']
        else:  # Wait for a change
            self.changed = self.player.monitor()
            self.log.debug('changed: %s', ', '.join(self.changed))
        if 'playlist' in self.changed:
            self.foreach_plugin('callback_playlist')
        if 'player' in self.changed or 'options' in self.changed:
            self.foreach_plugin('callback_player')
        if 'database' in self.changed:
            self.foreach_plugin('callback_player_database')
        if 'skipped' in self.changed:
            if self.player.state == 'play':
                self.log.info('Playing: %s', self.player.current)
                self.add_history()
                self.foreach_plugin('callback_next_song')
        if self.need_tracks():
            self.queue()

# VIM MODLINE
# vim: ai ts=4 sw=4 sts=4 expandtab