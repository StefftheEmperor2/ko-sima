import xbmc


class Log:
    def trace(self, message, *args):
        self.log(xbmc.LOGDEBUG, message, args)

    def debug(self, message, context=None):
        self.log(xbmc.LOGDEBUG, message, context)

    def info(self, message, context=None):
        self.log(xbmc.LOGINFO, message, context)

    def warning(self, message, context=None):
        self.log(xbmc.LOGWARNING, message, context)

    def error(self, message, context=None):
        self.log(xbmc.LOGERROR, message, context)

    def log(self, level, message, context):
        if context is None:
            xbmc.log(message, level)
        else:
            xbmc.log(message % context, level)

