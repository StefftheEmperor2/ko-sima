from sima.lib.plugin import Plugin


"""
    Deal with Kodi options - idle, repeat and party mode
"""
class KodiOptions(Plugin):
    """
    Deal with Kodi options - idle, repeat and party mode
    """

    def __init__(self, daemon):
        Plugin.__init__(self, daemon)
        self.daemon = daemon

    def callback_player(self):
        """
        Called on player changes
        """
        player = self.daemon.player
        if self.daemon.enabled and player.playmode.get('single') and self.daemon.config.getboolean('sima', 'single_disable_queue'):
                self.log.info('Kodi "single" mode activated.')
                self.daemon.enabled = False
        elif self.daemon.enabled and  player.playmode.get('repeat') and self.daemon.config.getboolean('sima', 'repeat_disable_queue'):
                self.log.info('Kodi "repeat" mode activated.')
                self.daemon.enabled = False
        elif self.daemon.enabled and player.get_kodi_playmode().is_in_party_mode() and self.daemon.config.getboolean('sima', 'party_mode_disable_queue'):
                self.log.info('Kodi "party" mode activated.')
                self.daemon.enabled = False
        elif self.daemon.enabled and player.playmode.get('repeat') and self.daemon.config.getboolean('sima', 'repeat_disable_queue'):
                self.log.info('Kodi "repeat" mode activated.')
                self.daemon.enabled = False
        elif self.daemon.enabled is False:
                self.log.debug('enabling queuing (leaving single|repeat mode)')
                self.daemon.enabled = True

    def shutdown(self):
        pass
