import xbmcaddon
import xbmcvfs
from os import path

import web_pdb

class Config:
    def __init__(self):
        self.addon = xbmcaddon.Addon()
        self._sections = {
            "crop": CropConfigSection(),
            "genre": GenreConfigSection(),
            "lastfm": ConfigSection(),
            "random": ConfigSection(),
            "Tags": ConfigSection(),
            "sima": CoreConfigSection()
        }

    def get(self, module, setting):
        return self.addon.getSetting('.'.join([module, setting]))

    def getint(self, module, setting):
        return self.addon.getSettingInt('.'.join([module, setting]))

    def getboolean(self, module, setting):
        if module == 'lastfm':
            module = 'sima.plugin.lastfm'
        return self.addon.getSettingBool('.'.join([module, setting]))

    def __getitem__(self, item):
        splitted = item.split('.')
        if len(splitted) > 2:
            raise ConfigException

        if len(splitted) == 2:
            [module, setting] = item.split('.')
            return self.get(module, setting)
        return self.get_section(item)

    def sections(self):
        return self._sections

    def get_section(self, section):
        return self._sections[section]


class ConfigSection:
    def __init__(self):
        self.items = {}

    def __contains__(self, item):
        return item in self.items

    def __getitem__(self, item):
        if isinstance(self.items[item], DeferredConfig):
            return self.items[item].get_value()
        return self.items[item]

    def __setitem__(self, key, value):
        self.items[key] = value

    def getint(self, key):
        return int(self.get(key))

    def get(self, key, default_value=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default_value


class CoreConfigSection(ConfigSection):
    def __init__(self):
        super(CoreConfigSection, self).__init__()
        var_dir = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        cache_dir = path.join(var_dir, 'http', 'LastFM')
        if not xbmcvfs.exists(path.join(cache_dir, '')):
            xbmcvfs.mkdirs(cache_dir)
        self.items['var_dir'] = var_dir


class CropConfigSection(ConfigSection):
    def __init__(self):
        super(CropConfigSection, self).__init__()
        self.items['consume'] = DeferredConfig('sima.plugin.crop.consume', int)


class GenreConfigSection(ConfigSection):
    def __init__(self):
        super(GenreConfigSection, self).__init__()
        self.items['queue_mode'] = DeferredConfig(
            'sima.plugin.genre.queue_mode',
            DeferredConfigEnumMapping({
                32011: 'track',
                32012: 'album'
            })
        )
        self.items['single_album'] = DeferredConfig('sima.plugin.genre.single_album', bool)
        self.items['track_to_add'] = DeferredConfig('sima.plugin.genre.track_to_add', int)
        self.items['album_to_add'] = DeferredConfig('sima.plugin.genre.album_to_add', int)


class DeferredConfigEnumMapping:
    def __init__(self, map):
        self.map = map

    def get_value(self, key):
        return self.map[key]

class DeferredConfig:
    def __init__(self, key, value_type):
        self.key = key
        self.type = value_type

    def get_value(self):
        if self.type is int:
            return xbmcaddon.Addon().getSettingInt(self.key)
        if self.type is bool:
            return xbmcaddon.Addon().getSettingBool(self.key)
        if isinstance(self.type, DeferredConfigEnumMapping):
            return self.type.get_value(xbmcaddon.Addon().getSetting(self.key))
        return xbmcaddon.Addon().getSetting(self.key)




class ConfigException(BaseException):
    pass
