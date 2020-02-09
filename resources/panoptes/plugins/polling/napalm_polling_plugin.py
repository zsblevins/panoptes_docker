### TODO THIS WAS JUST COPIED FROM THE TUTORIAL
from typing import Dict, Any
import time
import napalm
from yahoo_panoptes.polling.polling_plugin import PanoptesPollingPlugin
from yahoo_panoptes.framework.metrics import PanoptesMetricsGroupSet, \
    PanoptesMetricsGroup, PanoptesMetric, \
    PanoptesMetricType, PanoptesMetricDimension
from yahoo_panoptes.framework.plugins.context import PanoptesPluginContext
from yahoo_panoptes.framework.resources import PanoptesResource


class NapalmPollingPlugin(PanoptesPollingPlugin):
    """
    Only classes that inherit from PanoptesPollingPlugin are loaded. (Upstream Configuration Knobs Control This)
    """
    def __init__(self):
        self._plugin_context: PanoptesPluginContext = None
        self._config: Dict[str, Any] = {}
        self._panoptes_metrics_group_set: PanoptesMetricsGroupSet = PanoptesMetricsGroupSet()
        self._device: PanoptesResource = None
        self._execute_frequency: int = 60
        self._logger = None
        self.napalm_device_connection = None
        super(NapalmPollingPlugin, self).__init__()

    def populateMetricsGroupSetWithTimeSeries(self) -> None:
        """
        PanoptesMetricsGroupSet<set>{
            PanoptesMetricsGroup<dict>{
                dimensions<set>: {
                    PanoptesMetricDimension(name: str, value: str),
                    PanoptesMetricDimension(name: str, value: str),
                    ....
                },
                metrics<set>: {
                    PanoptesMetric(metric_name: str, metric_value: number, metric_type: {1: 'COUNTER', 0: 'GAUGE'}),
                    PanoptesMetric(metric_name: str, metric_value: number, metric_type: {1: 'COUNTER', 0: 'GAUGE'}),
                }
            },
            PanoptesMetricsGroup<dict>{...},
            PanoptesMetricsGroup<dict>{...}
        }

        Signatures:
            PanoptesMetricsGroup(resource: PanoptesResource, group_type: str, interval: int)
                - Timeseries container which is able to hold any number of metrics & dimensions.

            PanoptesMetricDimension(name: string_types, value: string_types)
            PanoptesMetric(metric_name: string_types, metric_value: number, metric_type: {1: 'COUNTER', 0: 'GAUGE'})
                - Note: Panoptes performs rate conversions specified in the .panoptes-plugin file

        The text above shows the structure of how time series data is stored within the PanoptesMetricsGroupSet.
        """
        interfaces = self.napalm_device_connection.get_interfaces()
        interface_counters = self.napalm_device_connection.get_interfaces_counters()
        for interface, object in self.napalm_device_connection.get_lldp_neighbors().items():
            panoptes_metrics_group = PanoptesMetricsGroup(self._device, 'napalm_interface', self._execute_frequency)

            panoptes_metrics_group.add_dimension(PanoptesMetricDimension('interface_name', interface))

            panoptes_metrics_group.add_dimension(PanoptesMetricDimension('neighbor', object['hostname'] or 'no_hostname_description'))
            panoptes_metrics_group.add_dimension(PanoptesMetricDimension('neighbor_port', object['port'] or 'no_port_description'))
            #if interface in interface_counters:
            panoptes_metrics_group.add_metrics(
                  PanoptesMetric('input_rate', interface_counters[interface]['rx_unicast_packets'],PanoptesMetricType.GAUGE)
                  )
            panoptes_metrics_group.add_metrics(
                  PanoptesMetric('output_rate', interface_counters[interface]['tx_unicast_packets'],PanoptesMetricType.GAUGE)
                  )
            #if interface in interfaces:
            panoptes_metrics_group.add_metrics(
                  PanoptesMetric('speed', interfaces[interface]['speed'],PanoptesMetricType.GAUGE)
                  )
            self._panoptes_metrics_group_set.add(panoptes_metrics_group)

    def run(self, context: PanoptesPluginContext) -> PanoptesMetricsGroupSet:
        """
        This function is called by the runner.py::class PanoptesPluginRunner::execute_plugin()::177
        The PluginRunner creates an instance of the PanoptesPluginManager which recursively searches the directory tree
        and collects all .panoptes-plugin files, loading them into the PanoptesPluginInfo class. The PanoptesPluginInfo
        class contains all metadata associated with a plugin: last execution time, device to run the plugin against
        (if applicable), last results time, key value store, the zookeeper lock, along with a link to the plugin itself.
        The PluginManager uses these provided functions to verify that the plugin should be run. Once verifications
        are complete, a lock is acquired and this function called. The PanoptesMetricsGroupSet (timeseries container)
        object returned is passed to the callback function `_process_metrics_group_set`. The callback function emits
        the provided metrics groups set on to the message bus (Kafka).
        Returns:
            PanoptesMetricsGroupSet: Timeseries Container

            JSON from the PanoptesMetricsGroupSet created in the `populatedMetricsGroupSetWithTimeSeries` function.
        """
        self._plugin_context = context
        self._config = context.config
        self._logger = context.logger
        self._device = context.data
        self._execute_frequency = int(context.config['main']['execute_frequency'])

        self.napalm_device_connection = self.driver(
            hostname=self._device.resource_endpoint,
            username=context.config['napalm']['username'],
            password=context.config['napalm']['password']
        )

        self.napalm_device_connection.open()

        self._logger.info("Running {} against {}".format(type(self).__name__, self._device))

        start_time = time.time()
        self.populateMetricsGroupSetWithTimeSeries()
        end_time = time.time()

        self._logger.info(
            "{} ran against device {} in {:.2f} seconds, {} metrics produced".format(
                type(self).__name__, self._device, end_time - start_time, len(self._panoptes_metrics_group_set))
        )

        return self._panoptes_metrics_group_set
