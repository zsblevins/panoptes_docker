from kafka import KafkaConsumer
from datetime import datetime
import json

from neomodel import config, db, StructuredNode, StringProperty, StructuredRel, IntegerProperty, DateTimeProperty, \
    RelationshipTo

config.DATABASE_URL = 'bolt://neo4j:test@host.docker.internal:7687'


class LinkRel(StructuredRel):
    last_seen = DateTimeProperty(default=lambda: datetime.now())
    input_rate = IntegerProperty()
    output_rate = IntegerProperty()
    speed = IntegerProperty()
    local_port = StringProperty()
    remote_port = StringProperty()


class Router(StructuredNode):
    name = StringProperty()
    vendor = StringProperty()
    connects = RelationshipTo('Router', 'CONNECTS', model=LinkRel)


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

                if local_port in ['Management1', 'mgmt0'] or remote_port in ['Management1', 'mgmt0']:
                    continue

                with db.transaction:
                    router_a = Router.nodes.get_or_none(name=local_router)
                    if not router_a:
                        router_a = Router(name=local_router).save()

                    router_z = Router.nodes.get_or_none(name=remote_router)
                    if not router_z:
                        router_z = Router(name=remote_router).save()

                    router_a.connects.disconnect(router_z)
                    router_z.connects.disconnect(router_a)
                    router_a.connects.connect(router_z, {
                        'local_port': local_port,
                        'remote_port': remote_port,
                        'input_rate': input_rate,
                        'output_rate': output_rate,
                        'speed': speed
                    })

                    router_z.connects.connect(router_a, {
                        'local_port': remote_port,
                        'remote_port': local_port,
                        'input_rate': output_rate,
                        'output_rate': input_rate,
                        'speed': speed
                    })


if __name__ == '__main__':
    main()
