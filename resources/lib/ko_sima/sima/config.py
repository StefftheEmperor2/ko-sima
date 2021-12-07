import xbmcaddon


class Config:
    def __init__(self):
        self.addon = xbmcaddon.Addon()

    def get(self, module, setting):
        self.addon.getSetting('.'.join([module, setting]))

    def getint(self, module, setting):
        self.addon.getSettingInt('.'.join([module, setting]))

    def __getitem__(self, item):
        splitted = item.split('.')
        if splitted.length > 2:
            raise ConfigException

        if splitted.length == 2:
            [module, setting] = item.split('.')
            return self.get(module, setting)
        return self.get_section(item)
    def sections(self):
        return []

    def get_section(self, section):
        return ConfigSection()


class ConfigSection:
    pass

class ConfigException(BaseException):
    pass
