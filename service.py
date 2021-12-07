import xbmc
from resources.lib.ko_sima.sima.core import KoSima
import web_pdb;
web_pdb.set_trace()

if __name__ == '__main__':
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    sima = KoSima()
    sima.load_plugins()
    sima.run()
