import napalm
from yahoo_panoptes.plugins.polling.napalm.napalm_polling_plugin import NapalmPollingPlugin

class EOSNapalmPollingPlugin(NapalmPollingPlugin):
    """
    Inherits everything from NapalmPollingPlugin
    """
    def __init__(self):
        super().__init__()
        self.driver = napalm.get_network_driver('eos')