import xbmcaddon
import xbmcvfs
from os import path


class Config:
    def __init__(self, core):
        self.core = core
        self.log = core.log
        self.addon = xbmcaddon.Addon()
        self._sections = {
            "crop": CropConfigSection(self),
            "genre": GenreConfigSection(self),
            "lastfm": LastFMConfigSection(self),
            "random": RandomConfigSection(self),
            "tags": TagsConfigSection(self),
            "sima": CoreConfigSection(self)
        }

    def get(self, module, setting):
        return self.get_kodi_setting('.'.join([module, setting]))

    def getint(self, module, setting):
        return self.get_kodi_setting_int('.'.join([module, setting]))

    def getboolean(self, module, setting):
        if module == 'lastfm':
            module = 'sima.plugin.lastfm'
        return self.get_kodi_setting_bool('.'.join([module, setting]))

    def get_kodi_setting_int(self, key):
        value = self.addon.getSettingInt(key)
        self.log.debug('Got int config %s: %s', key, value)
        return value

    def get_kodi_setting(self, key):
        value = self.addon.getSetting(key)
        self.log.debug('Got config %s: %s', key, value)
        return value

    def get_kodi_setting_bool(self, key):
        value = self.addon.getSettingBool(key)
        self.log.debug('Got bool config %s: %s', key, 'true' if value else 'false')
        return value

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
    def __init__(self, config):
        self.config = config
        self._items = {}

    def __contains__(self, item):
        return item in self._items

    def __getitem__(self, item):
        if isinstance(self._items[item], DeferredConfig):
            return self._items[item].get_value()
        return self._items[item]

    def __setitem__(self, key, value):
        self._items[key] = value

    def items(self):
        return [(k, self.__getitem__(k)) for k in self._items.keys()]

    def keys(self):
        return self._items.keys()

    def getint(self, key):
        return int(self.get(key))

    def getboolean(self, key, *args):
        return bool(self.get(key))

    def get(self, key, default_value=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default_value

    def register(self, key, value):
        self._items[key] = value


class CoreConfigSection(ConfigSection):
    def __init__(self, config):
        super(CoreConfigSection, self).__init__(config)
        var_dir = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        cache_dir = path.join(var_dir, 'http', 'LastFM')
        if not xbmcvfs.exists(path.join(cache_dir, '')):
            xbmcvfs.mkdirs(cache_dir)
        self.register('var_dir', var_dir)


class TagsConfigSection(ConfigSection):
    def __init__(self, config):
        super(TagsConfigSection, self).__init__(config)
        self.register('comment', DeferredConfig(config, 'sima.plugin.tags.comment', str))
        self.register('date', DeferredConfig(config, 'sima.plugin.tags.date', str))
        self.register('genre', DeferredConfig(config, 'sima.plugin.tags.genre', str))
        self.register('label', DeferredConfig(config, 'sima.plugin.tags.label', str))
        self.register('originaldate', DeferredConfig(config, 'sima.plugin.tags.originaldate', str))
        self.register('filter', DeferredConfig(config, 'sima.plugin.tags.filter', str))
        self.register('queue_mode', DeferredConfig(
            config,
            'sima.plugin.tags.queue_mode',
            DeferredConfigEnumMapping({
                32047: 'track',
                32048: 'album'
            })
        ))
        self.register('single_album', DeferredConfig(config, 'sima.plugin.tags.single_album', bool))
        self.register('track_to_add', DeferredConfig(config, 'sima.plugin.tags.track_to_add', int))
        self.register('album_to_add', DeferredConfig(config, 'sima.plugin.tags.album_to_add', int))
        self.register('priority', 80)


class LastFMConfigSection(ConfigSection):
    def __init__(self, config):
        super(LastFMConfigSection, self).__init__(config)
        self.register('queue_mode', DeferredConfig(
            config,
            'sima.plugin.lastfm.queue_mode',
            DeferredConfigEnumMapping({
                32028: 'track',
                32029: 'top',
                32030: 'album'
            })
        ))
        self.register('track_to_add', DeferredConfig(config, 'sima.plugin.lastfm.track_to_add', int))
        self.register('album_to_add', DeferredConfig(config, 'sima.plugin.lastfm.album_to_add', int))
        self.register('track_to_add_from_album', DeferredConfig(config, 'sima.plugin.lastfm.track_to_add_from_album', int))
        self.register('max_art', DeferredConfig(config, 'sima.plugin.lastfm.max_art', int))
        self.register('single_album', DeferredConfig(config, 'sima.plugin.lastfm.single_album', bool))
        self.register('depth', DeferredConfig(config, 'sima.plugin.lastfm.depth', int))
        self.register('priority', 100)


class RandomConfigSection(ConfigSection):
    def __init__(self, config):
        super(RandomConfigSection, self).__init__(config)
        self.register('track_to_add', DeferredConfig(config, 'sima.plugin.random.track_to_add', int))
        self.register('priority', 50)


class CropConfigSection(ConfigSection):
    def __init__(self, config):
        super(CropConfigSection, self).__init__(config)
        self.register('consume', DeferredConfig(config, 'sima.plugin.crop.consume', int))
        self.register('priority', 0)


class GenreConfigSection(ConfigSection):
    def __init__(self, config):
        super(GenreConfigSection, self).__init__(config)
        self.register('queue_mode', DeferredConfig(
            config,
            'sima.plugin.genre.queue_mode',
            DeferredConfigEnumMapping({
                32011: 'track',
                32012: 'album'
            })
        ))
        self.register('single_album', DeferredConfig(config, 'sima.plugin.genre.single_album', bool))
        self.register('track_to_add', DeferredConfig(config, 'sima.plugin.genre.track_to_add', int))
        self.register('album_to_add', DeferredConfig(config, 'sima.plugin.genre.album_to_add', int))
        self.register('priority', 79)


class DeferredConfigEnumMapping:
    def __init__(self, config_map):
        self.config_map = config_map

    def get_value(self, config, key):
        value = self.config_map[int(key)]
        config.log.debug('mapped config %s to %s', key, value)
        return value


class DeferredConfig:
    def __init__(self, config, key, value_type):
        self.config = config
        self.key = key
        self.type = value_type

    def get_value(self):
        if self.type is int:
            return self.config.get_kodi_setting_int(self.key)
        if self.type is bool:
            return self.config.get_kodi_setting_bool(self.key)
        if isinstance(self.type, DeferredConfigEnumMapping):
            return self.type.get_value(self.config, self.config.get_kodi_setting(self.key))
        return xbmcaddon.Addon().getSetting(self.key)


class ConfigException(BaseException):
    pass
