import docker
import redis


class MaasaasWorker(object):

    queue = 'maasaas'

    @staticmethod
    def perform(cluster_spec):
        docker_clients = [
            docker.Client(docker_url)
            for docker_url in cluster_spec['docker_urls']
        ]
        redis_client = redis.StrictRedis(
            host=cluster_spec['redis_host'],
            port=cluster_spec['redis_port']
        )

        launch_mongo_replica_set(docker_client, redis_client,
                                 cluster_spec['name'])
