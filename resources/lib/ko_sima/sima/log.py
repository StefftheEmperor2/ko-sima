import xbmc


class Log:
    def trace(self, message, *args):
        self.log(xbmc.LOGDEBUG, message, args)

    def debug(self, message, context):
        self.log(xbmc.LOGDEBUG, message, context)

    def info(self, message, *args):
        self.log(xbmc.LOGINFO, message, args)

    def warning(self, message, *args):
        self.log(xbmc.LOGWARNING, message, args)

    def error(self, message, *args):
        self.log(xbmc.LOGERROR, message, args)

    def log(self, level, message, context):
        xbmc.log(message % context, level)

