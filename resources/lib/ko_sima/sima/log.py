import xbmc
import collections.abc
import web_pdb

class Log:
    def trace(self, message, *args):
        self.log(xbmc.LOGDEBUG, message, args)

    def debug(self, message, *context):
        self.log(xbmc.LOGDEBUG, message, context)

    def info(self, message, *context):
        self.log(xbmc.LOGINFO, message, context)

    def warning(self, message, *context):
        self.log(xbmc.LOGWARNING, message, context)

    def error(self, message, *context):
        self.log(xbmc.LOGERROR, message, context)

    def log(self, level, message, context):
        if (context and len(context) == 1 and isinstance(context[0], collections.abc.Mapping)
                and context[0]):
            context = context[0]
        if context is None or len(context) == 0:
            xbmc.log(message, level)
        else:
            xbmc.log("[Ko-Sima] "+message % context, level)

