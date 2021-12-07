import xbmc
from resources.lib.ko_sima.sima.core import KoSima
import pydevd
pydevd.settrace(stdoutToServer=True, stderrToServer=True, port=63340)

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    sima = KoSima()
    sima.load_plugins()
    sima.run()
