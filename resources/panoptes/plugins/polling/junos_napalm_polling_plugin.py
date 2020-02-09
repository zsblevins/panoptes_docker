class JunosNapalmPollingPlugin(NapalmPollingPlugin):
    """
    Inherits everything from NapalmPollingPlugin
    """
    def __init__(self):
        super().__init__()
        self.driver = napalm.get_network_driver('junos')