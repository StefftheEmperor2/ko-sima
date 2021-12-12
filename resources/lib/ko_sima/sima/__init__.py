import xbmcvfs
import xbmc
import xbmcaddon
import importlib
import sys
from os import path
def load_sima():
    module_name = "sima"
    addon_base_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
    mpd_sima_path = path.join(addon_base_path, 'resources', 'lib', 'mpd-sima', 'sima', '__init__.py')
    xbmc.log(mpd_sima_path)
    sima_spec = importlib.util.spec_from_file_location(module_name, mpd_sima_path)
    mpdSima = importlib.util.module_from_spec(sima_spec)
    sys.modules[module_name] = mpdSima
    sima_spec.loader.exec_module(mpdSima)


def load_musicpd():
    musicpd_module_name = 'musicpd'
    addon_base_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('path'))
    musicpd_path = path.join(addon_base_path, 'resources', 'lib', 'ko_sima', 'sima', 'mpd_stubs', 'musicpd.py')
    musicpd_spec = importlib.util.spec_from_file_location(musicpd_module_name, musicpd_path)
    musicpd = importlib.util.module_from_spec(musicpd_spec)
    sys.modules[musicpd_module_name] = musicpd
    musicpd_spec.loader.exec_module(musicpd)

