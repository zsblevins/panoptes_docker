from kafka import KafkaConsumer
from datetime import datetime
import json

from neomodel import config, db, StructuredNode, StringProperty, StructuredRel, IntegerProperty, DateTimeProperty, \
    RelationshipTo

config.DATABASE_URL = 'bolt://neo4j:test@host.docker.internal:7687'


class LinkRel(StructuredRel):
    local_port = StringProperty()
    remote_port = StringProperty()
    input_rate = IntegerProperty()
    output_rate = IntegerProperty()
    speed = IntegerProperty()


class Router(StructuredNode):
    name = StringProperty()
    connects = RelationshipTo('Router', 'CONNECTS')

def main():
    consumer = KafkaConsumer('local-processed', bootstrap_servers=['localhost:9092'], group_id='topology')

    while True:
        for message in consumer:
            metric = json.loads(message.value.decode())


            dimensions = {dim['dimension_name']: dim['dimension_value'] for dim in metric['dimensions']}
            metrics = {m['metric_name'] + '_' + m['metric_type']: m['metric_value'] for m in metric['metrics']}

            if metric['metrics_group_type'] == 'napalm_interface':
                print(json.dumps(dimensions, indent=4))

                local_router = metric['resource']['resource_id'].replace('.nanog78.panoptes.cloud.tesuto.com', '')
                local_port = dimensions['interface_name']
                remote_router = dimensions['neighbor'].replace('.local', '')
                remote_port = dimensions['neighbor_port']
                input_rate = metrics.get('input_rate_gauge', 0)
                output_rate = metrics.get('output_rate_gauge', 0)
                speed = dimensions['speed']


                try:
                    router_a = Router.nodes.get(name=local_router)
                except:
                    router_a = Router(name=local_router).save()

                try:
                    router_z = Router.nodes.get(name=remote_router)
                except:
                    router_z = Router(name=remote_router).save()

                # links = router_a.connects.match(local_port=local_port)
                # for link in links:
                #     link.delete()
                #
                # links = router_z.connects.match(local_port=remote_port)
                # for link in links:
                #     link.delete()


                router_a.connects.connect(router_z)
                router_z.connects.connect(router_a)

                # router_a.connects.connect(router_z, {
                #     'input_rate': int(input_rate),
                #     'output_rate': int(output_rate),
                #     'speed': int(speed),
                #     'local_port': local_port,
                #     'remote_port': remote_port
                # })

                # router_z.connects.connect(router_a, {
                #     'input_rate': int(output_rate),
                #     'output_rate': int(input_rate),
                #     'speed': int(speed),
                #     'local_port': remote_port,
                #     'remote_port': local_port
                # })



if __name__ == '__main__':
    main()