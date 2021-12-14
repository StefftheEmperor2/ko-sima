import xbmc
from .rpc import RPC
from .rpc.filter import SimpleFilter, ComplexFilter, FilterParser
from . import load_sima, load_musicpd
load_sima()
load_musicpd()
from sima.mpdclient import MPD
from sima.lib.track import Track
import web_pdb


class PlayerClient(MPD):
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
        self.core = core
        self.log = core.log
        self.config = core.config
        self.kodi_sima_playlist = Playlist(core)
        self.kodi_playmode = PlayMode()
        self.kodi_playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
        self.kodi_player = XBMCPlayer(self)
        self.kodi_monitor = XBMCMonitor(self)
        self.kodi_sima_queue = PlayQueue(core)
        self.is_exiting = False
        self.has_exited = False
        self.idle = []
        self.xbmc_monitor = xbmc.Monitor()
        self.loaded_genres = {}
        self._cache = None
        self.use_mbid = True
        self.play_is_triggering_skip = True

    def onAVStarted(self) -> None:
        self.log.debug('state changed in player due to AVStarted')
        if self.play_is_triggering_skip:
            self.idle.append('skipped')
            self.play_is_triggering_skip = False
        self.idle.append('player')

    def onAVChange(self) -> None:
        self.log.debug('state changed in player due to AVChange')
        self.play_is_triggering_skip = True
        self.idle.append('player')

    def onPlayBackPaused(self) -> None:
        self.log.debug('state changed in player due to PlayBackPaused')
        self.idle.append('player')

    def onPlayBackResumed(self) -> None:
        self.log.debug('state changed in player due to PlayBackResumed')
        self.idle.append('player')

    def onPlayBackStopped(self) -> None:
        self.log.debug('state chamged in player due to PlayBackStopped')
        self.play_is_triggering_skip = True
        self.idle.append('player')

    def onPlayBackEnded(self) -> None:
        self.log.debug('state chamged in player due to PlayBackEnded')
        self.play_is_triggering_skip = True
        self.idle.append('player')

    def onSettingsChanged(self):
        self.log.debug('settings changed -> reloading config')
        self.idle.append('config')

    def onScanFinished(self):
        self.log.debug('scan finished -> reloading database')
        self.idle.append('database')

    def add(self, track):
        self.log.debug('Adding track %s', str(track))
        self.kodi_playlist.add(url=track.file)

    def connect(self):
        self._reset_cache()

    def disconnect(self):
        pass

    def clean(self):
        pass

    def delete(self, pos):
        self.log.debug(f'Removing item {pos} from playlist')
        playlist_id = self.kodi_playlist.getPlayListId()
        length_before = self.get_playlist_length(playlist_id)
        rpc = RPC(self.core, 'Playlist.Remove', 1)
        rpc.add_param('playlistid', playlist_id)
        rpc.add_param('position', pos)
        res = rpc.execute()

        while self.get_playlist_length(playlist_id) == length_before:
            xbmc.sleep(20)
        self.log.debug(f'Result of removing {res}')

    @property
    def state(self):
        if self.kodi_player.isPlayingAudio():
            return 'play'

    @property
    def playlist(self):
        return self.kodi_sima_playlist

    @property
    def queue(self):
        return self.kodi_sima_queue

    def currentsong(self):
        if self.state == 'play':
            current_playlist_position = self.get_current_playlist_position()
            self.log.debug(f'current playlist position {current_playlist_position}')
            current_playing_item = self.core.get_item_as_track(
                self.kodi_player.getMusicInfoTag(),
                pos=current_playlist_position
            )

            return current_playing_item
        return Track()

    def get_active_player(self):
        rpc = RPC(self.core, 'Player.GetActivePlayers', 1)
        result = rpc.execute()
        for player in result['result']:
            if player['type'] == 'audio':
                return player['playerid']
        return None

    def get_current_playlist_position(self):
        playerid = self.get_active_player()
        if playerid is not None:
            rpc = RPC(self.core, 'Player.GetProperties', 1)
            rpc.add_property('position')
            rpc.add_param('playerid', playerid)
            result = rpc.execute()
            return result['result']['position']
        return None

    def get_playlist_length(self, playlist_id):
        rpc = RPC(self.core, 'Playlist.GetItems', 1)
        rpc.add_param('playlistid', playlist_id)
        rpc.set_limits(0, 0)
        result = rpc.execute()
        return result['result']['limits']['total']

    def kodi_find(self, what, mpd_filter=None):
        if what == 'artist':
            return self.find_tracks_by_artist(mpd_filter)
        if mpd_filter is None:
            return self.find_tracks_by_filter(what)
        # if what == 'musicbrainz_artistid':
        #     return []
        web_pdb.set_trace()

    def find_tracks_by_artist(self, artist):
        search_more = True
        page = 0
        songs = []
        while search_more:
            page = page + 1
            rpc = RPC(self.core, 'AudioLibrary.GetSongs', 'libSongs')
            rpc.set_page(page)
            rpc.set_sort_field('title')
            rpc.add_property('title')
            rpc.add_property('musicbrainztrackid')
            rpc.add_property('musicbrainzalbumid')
            rpc.add_property('musicbrainzartistid')
            rpc.add_property('musicbrainzalbumartistid')
            rpc.add_property('file')
            rpc.add_property('duration')
            rpc.add_property('artist')
            rpc.add_property('albumartist')
            rpc.add_property('album')
            rpc.add_property('genreid')
            rpc.add_param('allroles', True)
            rpc.set_filter(
                ComplexFilter()
                .set_operator_or()
                .add_compound(
                    SimpleFilter('artist', SimpleFilter.OPERATOR_IS, artist)
                )
                .add_compound(
                    SimpleFilter('albumartist', SimpleFilter.OPERATOR_IS, artist)
                )
            )
            response = rpc.execute()
            self.core.log.debug(str(response))
            if "songs" in response['result']:
                genre_ids = []
                for song in response['result']['songs']:
                    for genre_id in song['genreid']:
                        genre_ids.append(genre_id)
                self.assure_genre_ids_loaded(genre_ids)
                for song in response['result']['songs']:
                    songs.append(self.core.create_mpd_track_by_kodi_data(song, self.get_genres_by_ids(song['genreid'])))
                rpc.set_page(page + 1)
                search_more = len(response['result']['songs']) > 0 and rpc.limits.start <= \
                              response['result']['limits']['total']
            else:
                self.core.log.warning('no more results in list')
                search_more = False
        return songs


    def find_tracks_by_filter(self, filter_condition):
        search_more = True
        page = 0
        songs = []
        raw_filter = kodi_filter = None
        if filter_condition:
            raw_filter = FilterParser(filter_condition)
            kodi_filter = raw_filter.get_kodi_filter(FilterParser.SECTION_SONGS)
        while search_more:
            page = page + 1
            rpc = RPC(self.core, 'AudioLibrary.GetSongs', 'libSongs')
            rpc.set_page(page)
            rpc.set_sort_field('title')
            rpc.add_property('title')
            rpc.add_property('musicbrainztrackid')
            rpc.add_property('musicbrainzalbumid')
            rpc.add_property('musicbrainzartistid')
            rpc.add_property('musicbrainzalbumartistid')
            rpc.add_property('file')
            rpc.add_property('duration')
            rpc.add_property('artist')
            rpc.add_property('albumartist')
            rpc.add_property('album')
            rpc.add_property('genreid')
            rpc.add_param('allroles', True)
            if kodi_filter:
                rpc.filter = kodi_filter
            response = rpc.execute()
            self.core.log.debug(str(response))
            if "songs" in response['result']:
                genre_ids = []
                for song in response['result']['songs']:
                    for genre_id in song['genreid']:
                        genre_ids.append(genre_id)
                self.assure_genre_ids_loaded(genre_ids)
                for song_data in response['result']['songs']:
                    if not raw_filter or raw_filter.matches_song_data(song_data):
                        songs.append(
                            self.core.create_mpd_track_by_kodi_data(
                                song_data,
                                self.get_genres_by_ids(
                                    song_data['genreid']
                                )
                            )
                        )
                rpc.set_page(page + 1)
                search_more = len(response['result']['songs']) > 0 and rpc.limits.start <= \
                              response['result']['limits']['total']
            else:
                self.core.log.warning('no more results in list')
                search_more = False
        return songs

    def fetch_idle(self):
        idle = []
        while len(self.idle):
            idle.append(self.idle.pop(0))
        return idle

    def monitor(self):
        while len(self.idle) == 0:
            if self.is_exiting or self.xbmc_monitor.abortRequested():
                break
            self.xbmc_monitor.waitForAbort(1)
        if self.is_exiting:
            self.has_exited = True
        return self.fetch_idle()

    def list(self, subject, filter_condition=None):
        if subject == 'album':
            return self.list_albums(filter_condition)
        if subject == 'artist':
            return self.list_artists(filter_condition)
        if subject == 'MUSICBRAINZ_ARTISTID':
            return self.list_music_brainz_artist_ids(filter_condition)
        if subject == 'MUSICBRAINZ_ALBUMID' or subject == 'musicbrainz_albumid':
            return self.list_music_brainz_album_ids(filter_condition)
        web_pdb.set_trace()

    def list_artists(self, filter_condition=None):
        search_more = True
        page = 0
        artists = []
        raw_filter = kodi_filter = None
        if filter_condition:
            raw_filter = FilterParser(filter_condition)
            kodi_filter = raw_filter.get_kodi_filter(FilterParser.SECTION_ARTISTS)
        while search_more:
            page = page + 1
            rpc = RPC(self.core, 'AudioLibrary.GetArtists', 1)
            rpc.set_page(page)
            rpc.set_sort_field('artist')
            rpc.add_property('musicbrainzartistid')
            rpc.add_property('isalbumartist')
            rpc.add_property('genre')
            rpc.add_property('songgenres')
            rpc.add_param('albumartistsonly', False)
            if kodi_filter:
                rpc.filter = kodi_filter
            response = rpc.execute()
            self.core.log.debug(str(response))
            if "artists" in response['result']:
                for artist_data in response['result']['artists']:
                    if not raw_filter or raw_filter.matches_artist_data(artist_data):
                        artists.append(artist_data['artist'])
                rpc.set_page(page + 1)
                search_more = len(response['result']['artists']) > 0 and rpc.limits.start <= \
                              response['result']['limits']['total']
            else:
                self.core.log.warning('no more results in list')
                search_more = False

        return artists

    def list_albums(self, filter_condition=None):
        search_more = True
        page = 0
        albums = []
        raw_filter = kodi_filter = None
        if filter_condition:
            raw_filter = FilterParser(filter_condition)
            kodi_filter = raw_filter.get_kodi_filter(FilterParser.SECTION_ALBUMS)
        while search_more:
            page = page + 1
            rpc = RPC(self.core, 'AudioLibrary.GetAlbums', 1)
            rpc.set_page(page)
            rpc.set_sort_field('album')
            rpc.add_property('musicbrainzalbumid')
            rpc.add_property('musicbrainzalbumartistid')
            rpc.add_property('artist')
            rpc.add_property('title')
            rpc.add_property('genre')
            rpc.add_property('songgenres')
            rpc.add_param('includesingles', True)
            if kodi_filter:
                rpc.filter = kodi_filter
            response = rpc.execute()
            self.core.log.debug(str(response))
            if "albums" in response['result']:
                for album_data in response['result']['albums']:
                    if not raw_filter or raw_filter.matches_album_data(album_data):
                        albums.append(album_data['title'])
                rpc.set_page(page + 1)
                search_more = len(response['result']['albums']) > 0 and rpc.limits.start <= \
                              response['result']['limits']['total']
            else:
                self.core.log.warning('no more results in list')
                search_more = False

        return albums


    def list_music_brainz_album_ids(self, filter_condition=None):
        search_more = True
        page = 0
        mb_ids = []
        raw_filter = kodi_filter = None
        if filter_condition:
            raw_filter = FilterParser(filter_condition)
            kodi_filter = raw_filter.get_kodi_filter(FilterParser.SECTION_ALBUMS)
        while search_more:
            page = page + 1
            rpc = RPC(self.core, 'AudioLibrary.GetAlbums', 1)
            rpc.set_page(page)
            rpc.set_sort_field('album')
            rpc.add_property('musicbrainzalbumid')
            rpc.add_property('musicbrainzalbumartistid')
            rpc.add_property('artist')
            rpc.add_property('title')
            rpc.add_property('genre')
            rpc.add_property('songgenres')
            rpc.add_param('includesingles', True)
            if kodi_filter:
                rpc.filter = kodi_filter
            response = rpc.execute()
            self.core.log.debug(str(response))
            if "albums" in response['result']:
                for album_data in response['result']['albums']:
                    if not raw_filter or raw_filter.matches_album_data(album_data):
                        music_brainz_album_id = next(iter(album_data['musicbrainzalbumid'] or []), None) or None
                        if music_brainz_album_id:
                            mb_ids.append(music_brainz_album_id)
                rpc.set_page(page + 1)
                search_more = len(response['result']['albums']) > 0 and rpc.limits.start <= \
                              response['result']['limits']['total']
            else:
                self.core.log.warning('no more results in list')
                search_more = False

        return mb_ids

    def list_music_brainz_artist_ids(self, filter_condition=None):
        search_more = True
        page = 0
        mb_ids = []
        raw_filter = kodi_filter = None
        if filter_condition:
            raw_filter = FilterParser(filter_condition)
            kodi_filter = raw_filter.get_kodi_filter(FilterParser.SECTION_ARTISTS)
        while search_more:
            page = page + 1
            rpc = RPC(self.core, 'AudioLibrary.GetArtists', 1)
            rpc.set_page(page)
            rpc.set_sort_field('artist')
            rpc.add_property('musicbrainzartistid')
            rpc.add_property('isalbumartist')
            rpc.add_property('genre')
            rpc.add_property('songgenres')
            rpc.add_param('albumartistsonly', False)
            if kodi_filter:
                rpc.filter = kodi_filter
            response = rpc.execute()
            self.core.log.debug(str(response))
            if "artists" in response['result']:
                for artist_data in response['result']['artists']:
                    if not raw_filter or raw_filter.matches_artist_data(artist_data):
                        music_brainz_artist_id = next(iter(artist_data['musicbrainzartistid'] or []), None) or None
                        if music_brainz_artist_id:
                            mb_ids.append(music_brainz_artist_id)
                        mb_ids.append(music_brainz_artist_id)
                rpc.set_page(page + 1)
                search_more = len(response['result']['artists']) > 0 and rpc.limits.start <= \
                              response['result']['limits']['total']
            else:
                self.core.log.warning('no more results in list')
                search_more = False

        return mb_ids

    def assure_genre_ids_loaded(self, genre_ids):
        keys_to_load = self.diff(genre_ids, self.loaded_genres.keys())
        if len(keys_to_load) > 0:
            search_more = True
            page = 0
            while search_more:
                page = page + 1
                rpc = RPC(self.core, 'AudioLibrary.GetGenres', 1)
                rpc.set_page(page)
                rpc.set_sort_field('title')
                rpc.add_property('title')
                response = rpc.execute()
                self.core.log.debug(str(response))
                if "genres" in response['result']:
                    for genre_data in response['result']['genres']:
                        self.loaded_genres[genre_data['genreid']] = genre_data['title']
                    rpc.set_page(page + 1)
                    search_more = len(response['result']['genres']) > 0 and rpc.limits.start <= \
                                  response['result']['limits']['total']
                else:
                    self.core.log.warning('no more results in list')
                    search_more = False

    def get_genre_by_id(self, genre_id):
        self.assure_genre_ids_loaded([genre_id])
        return self.loaded_genres[genre_id]

    def get_genres_by_ids(self, genre_ids):
        genres = []
        for genre_id in genre_ids:
            genres.append(self.get_genre_by_id(genre_id))
        return genres

    @staticmethod
    def diff(first, second):
        second = set(second)
        return [item for item in first if item not in second]
    #
    # def find_tracks(self, artist):
    #     search_more = True
    #     page = 0
    #     songs = []
    #     web_pdb.set_trace()
    #     while search_more:
    #         page = page + 1
    #         rpc = RPC(self.core, 'AudioLibrary.GetSongs', 'libSongs')
    #         rpc.set_page(page)
    #         rpc.set_sort_field('title')
    #         rpc.add_property('title')
    #         rpc.add_property('musicbrainztrackid')
    #         rpc.add_property('musicbrainzalbumid')
    #         rpc.add_property('musicbrainzartistid')
    #         rpc.add_property('musicbrainzalbumartistid')
    #         rpc.add_property('file')
    #         rpc.add_property('duration')
    #         rpc.add_property('artist')
    #         rpc.add_property('albumartist')
    #         rpc.add_property('album')
    #         rpc.add_property('genreid')
    #         rpc.add_param('allroles', True)
    #         rpc.set_filter(
    #             ComplexFilter()
    #             .set_operator_or()
    #             .add_compound(
    #                 SimpleFilter('artist', SimpleFilter.OPERATOR_IS, artist.name)
    #             )
    #             .add_compound(
    #                 SimpleFilter('albumartist', SimpleFilter.OPERATOR_IS, artist.name)
    #             )
    #         )
    #         response = rpc.execute()
    #         self.core.log.debug(str(response))
    #         if "songs" in response['result']:
    #             genre_ids = []
    #             for song in response['result']['songs']:
    #                 for genre_id in song['genreid']:
    #                     genre_ids.append(genre_id)
    #             self.assure_genre_ids_loaded(genre_ids)
    #             for song in response['result']['songs']:
    #                 songs.append(self.core.create_song_by_kodi_data(song, self.get_genres_by_ids(song['genreid'])))
    #             rpc.set_page(page + 1)
    #             search_more = len(response['result']['songs']) > 0 and rpc.limits.start <= \
    #                           response['result']['limits']['total']
    #         else:
    #             self.core.log.warning('no more results in list')
    #             search_more = False
    #
    # def search_artist(self, artist):
    #     rpc = RPC(self.core, 'AudioLibrary.GetArtists', 1)
    #     rpc.set_sort_field('artist')
    #     rpc.add_property('musicbrainzartistid')
    #     rpc.add_property('isalbumartist')
    #     rpc.add_param('albumartistsonly', False)
    #     rpc.limits.start = 0
    #     rpc.limits.end = 1
    #     filter = ComplexFilter()\
    #         .set_operator_or()\
    #         .add_compound(
    #             SimpleFilter('artist', SimpleFilter.OPERATOR_IS, artist.name)
    #         )
    #     # if artist.mbid:
    #     #     filter.add_compound(
    #     #         SimpleFilter('musicbrainzartistid', SimpleFilter.OPERATOR_IS, artist.mbid)
    #     #     )
    #
    #     # if artist.albumartist and artist.albumartist != artist.name:
    #     #     filter.add_compound(
    #     #         SimpleFilter('albumartist', SimpleFilter.OPERATOR_IS, artist.name)
    #     #     )
    #     rpc.set_filter(
    #         filter
    #     )
    #     response = rpc.execute()
    #     self.core.log.debug(str(response))
    #     if "artists" in response['result']:
    #         artist_data = next(iter(response['result']['artists'] or []), None) or None
    #         if artist_data:
    #             return self.core.create_artist_by_kodi_data(artist_data)
    #     return None

    def get_kodi_playmode(self):
        return self.kodi_playmode

    def get_status(self):
        return lambda: {
            'repeat': self.kodi_playmode.is_repeat(),
            'random': self.kodi_playmode.is_random(),
            'single': self.kodi_playmode.is_single()
        }

    def __getattr__(self, item):
        if item == 'status':
            return self.get_status()
        return super(PlayerClient, self).__getattr__(item)


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


class XBMCMonitor(xbmc.Monitor):
    def __init__(self, player):
        super(XBMCMonitor, self).__init__()
        self.player = player

    def onSettingsChanged(self):
            self.player.onSettingsChanged()

    def onScanFinished(self, library):
        if library == 'music':
            self.player.onScanFinished()

class PlayMode:
    def get(self, prop):
        if prop == 'random':
            return self.is_random()
        if prop == 'single':
            return self.is_single()
        if prop == 'repeat':
            return self.is_repeat()

    def is_random(self):
        return xbmc.getCondVisibility('Playlist.IsRandom')

    def is_single(self):
        return xbmc.getCondVisibility('Playlist.IsRepeatOne')

    def is_repeat(self):
        return xbmc.getCondVisibility('Playlist.IsRepeat')

    def is_in_party_mode(self):
        return xbmc.getCondVisibility('MusicPartyMode.Enabled')


class Playlist:
    def __init__(self, core):
        self.core = core
        self.playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)

    def __len__(self):
        return self.playlist.size()

    def __getitem__(self, item):
        if item < 0:
            item = len(self) + item
        self.core.log.debug('getting item %s of %s from playlist', item + 1, len(self))
        if len(self) < item + 1:
            raise IndexError
        return self.core.get_item_as_track(self.playlist.__getitem__(item).getMusicInfoTag())


class PlayQueue(Playlist):
    def __init__(self, core):
        super(PlayQueue, self).__init__(core)

    def __getitem__(self, item):
        playlist_position = max(self.playlist.getposition(), 0)
        if item < 0:
            item = len(self) + item
        #web_pdb.set_trace()
        self.core.log.debug('getting item %s of %s from queue', item + 1, len(self))
        if len(self) < item + 1:
            raise IndexError
        return self.core.get_item_as_track(self.playlist.__getitem__(item + playlist_position).getMusicInfoTag())

    def __len__(self):
        playlist_size = self.playlist.size()
        playlist_position = self.playlist.getposition()
        if playlist_size == 0 or playlist_position == -1:
            return 0
        return self.playlist.size() - self.playlist.getposition()


class PlayerError(BaseException):
    pass
