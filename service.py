import xbmc
from resources.lib.ko_sima.sima.core import KoSima

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    sima = KoSima()
    sima.load_plugins()
    sima.run()
