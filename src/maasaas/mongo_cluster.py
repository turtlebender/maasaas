"""
Wrapper functions for starting up a mongo replica set as docker containers.
"""

import json
import logging
import os.path
import time
import uuid

import redis
import pymongo
import pymongo.errors

import docker

DOCKER_IMAGE = 'mongodb:2.0.8'
DATA_DIR = '/home/trhowe/src/mongo-7-11/data'


def get_mongo_client(host):
    """
    Abstract the mongo client aquisition to make testing easier
    """
    return pymongo.MongoClient(host, slave_okay=True)


def launch_mongo_replica_set(docker_clients, redis_client, name):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    master = None
    others = []
    command = [
        '/usr/bin/mongod',
        '--journal',
        '--dbpath=/var/lib/mongodb',
        '--smallfiles',
        "--replSet={0}".format(name)
    ]
    mongo_hosts = []
    containers = []
    for docker_client in docker_clients:
        volume_id = uuid.uuid4().hex
        volume_path = os.path.join(DATA_DIR, volume_id)
        if not os.path.exists(volume_path):
            os.mkdir(volume_path)

        container = docker_client.create_container(
            DOCKER_IMAGE,
            command,
            ports=["0:27017"]
        )
        docker_client.start(container, binds={volume_path: '/var/lib/mongodb'})
        container_details = docker_client.inspect_container(container['Id'])
        main_port = docker_client.port(container, 27017)
        local_ip = container_details['NetworkSettings']['IPAddress']
        container_details = {
            'docker_url': docker_client.base_url,
            'remote_mongo_host': 'localhost',
            'volume_id': volume_id,
            'container_id': container['Id'],
            'local_mongo_port': main_port,
            'local_ip': local_ip,
            'remote_mongo_port': main_port,
        }
        redis_client.rpush(
            name,
            json.dumps(container_details)
        )
        containers.append(container_details)
        if not master:
            master = "localhost:{0}".format(main_port)
        else:
            others.append("localhost:{0}".format(main_port))
    exception = object()
    c = None
    while True:
        try:
            c = get_mongo_client(master)
            break
        except Exception:
            logging.debug('Waiting for mongo to come to life!!!!')
            time.sleep(5)
    logging.debug('Mongo is ALIVE!!!!!')
    members = []
    for count, container in zip(xrange(len(containers)), containers):
        container = containers[count]
        members.append(
            {
                '_id': count,
                'host': "{0}:{1}".format(
                    container['local_ip'],
                    27017
                )
            }
        )
    repl_set_doc = {
        '_id': name,
        'members': members
    }

    while True:
        try:
            c.admin.command("replSetInitiate", repl_set_doc)
            break
        except pymongo.errors.OperationFailure:
            logging.debug('Waiting for replica set to initialize')
            time.sleep(5)
    return [
        "{0}:{1}".format(
            container['remote_mongo_host'],
            container['remote_mongo_port']
        )
        for container in containers
    ]


def delete_mongo(name, redis_client):
    container = redis_client.lpop(name)
    while container:
        container = json.loads(container)
        logging.debug(
            "Removing Container: {0}".format(container['container_id'])
        )
        docker_client = docker.Client(container['docker_url'])
        docker_client.stop(container['container_id'])
        docker_client.remove_container(container['container_id'])
        os.removedirs(os.path.join(DATA_DIR, container['volume_id']))
        container = redis_client.lpop(name)


def get_mongo(name, redis_client):
    containers = redis_client.lrange(name, 0, -1)
    containers = [json.loads(container) for container in containers]
    return [
        "{0}:{1}".format(
            container['remote_mongo_host'],
            container['remote_mongo_port']
        )
        for container in containers
    ]


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    redis_client = redis.StrictRedis()
    import sys
    if len(sys.argv) < 2 or sys.argv[1] == 'launch':
        launch_mongo_replica_set(
            [
                docker.Client('unix://var/run/docker.sock'),
                docker.Client('unix://var/run/docker.sock'),
                docker.Client('unix://var/run/docker.sock'),
            ],
            redis_client, 'test'
        )
    elif sys.argv[1] == 'delete':
        delete_mongo('test', redis_client)
    elif sys.argv[1] == 'get':
        print json.dumps(get_mongo('test', redis_client), indent=2)
