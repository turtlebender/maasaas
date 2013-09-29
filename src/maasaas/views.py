import json

from flask import Flask, request, url_for, make_response
import maasaas.mongo_cluster as mongo_cluster


def make_json(content, pretty=False):
    if pretty:
        return json.dumps(content, indent=2)
    return json.dumps(content)


def create_app(redis_client, docker_clients):
    app = Flask('maasaas')

    @route('/mongo_clusters/', methods=['POST'])
    def create_mongo_cluster():
        cluster_request = request.json
        name = cluster_request['name']
        request_id = mongo_cluster.async_launch_mongo_replica_set(
            docker_clients,
            redis_client,
            name
        )
        cluster_url = url_for('get_mongo_cluster', mongo_cluster_id=request_id)
        response = make_response(make_response({'cluster': cluster_url}, 201))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Location'] = cluster_url
        return response

    @route('/mongo_clusters/<mongo_cluster_id>', methods=['GET'])
    def get_mongo_cluster(mongo_cluster_id):
        pass
