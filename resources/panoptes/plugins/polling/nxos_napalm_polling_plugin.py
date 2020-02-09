from napalm_polling_plugin import NapalmPollingPlugin

class IOSXRNapalmPollingPlugin(NapalmPollingPlugin):
    """
    Inherits everything from NapalmPollingPlugin
    """
    def __init__(self):
        super().__init__()
        self.driver = napalm.get_network_driver('nxos')