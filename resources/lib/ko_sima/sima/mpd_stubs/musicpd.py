VERSION = '0.0'


class MPDError:
    pass


class MPDClient:
    def kodi_find(self):
        pass

    def __getattr__(self, item):
        if item == 'find':
            return self.kodi_find
        raise StubException(item)


class CommandError(BaseException):
    pass


class PlayerError:
    pass


class Album(dict):
    def __init__(self):
        super().__init__()
        self.name = None

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getattr__(self, item):
        return self.__getitem__(item)


class Track(dict):
    def __init__(self):
        super().__init__()
        self.update({
            'Album': Album(),
            'album': None,
            'artist': None,
            'file': None,
            'musicbrainz_artistid': None,
            'musicbrainz_albumid': None,
            'title': None,
        })

    def __setattr__(self, key, value):
        self.__setitem__(key, value)

    def __getattr__(self, item):
        return self.__getitem__(item)


class StubException(BaseException):
    pass
