import os
import gzip
import json
import base64
import threading
import asyncio
import sqlite3
from google.cloud import pubsub_v1
from google.cloud import bigquery
from xialib_gcp import PubsubSubscriber, BigQueryAdaptor, GCSStorer
import google.auth
from xialib import SQLiteAdaptor, BasicStorer
from pyagent import Pusher

project_id = google.auth.default()[1]
bigquery_db = bigquery.Client()
gcs_storer = GCSStorer()

locks = {None: threading.Lock()}

def callback(s: PubsubSubscriber, message: dict, source, subscription_id):
    global bigquery_db
    global gcs_storer
    global project_id

    storers = [gcs_storer]
    adapter = BigQueryAdaptor(connection=bigquery_db, project_id=project_id)
    adapter_dict = {'.': adapter, 'NPL.': adapter}
    pusher = Pusher(storers=storers, adaptor_dict=adapter_dict)
    header, data, id = s.unpack_message(message)
    print("size:{}-{}".format(len(data), header))
    s.ack(project_id, subscription_id, id)

    if subscription_id == 'agent-001-debug':
        if locks.get(header['table_id'], None) is None:
            locks[None].acquire(True)
            if locks.get(header['table_id'], None) is None:
                locks[header['table_id']] = threading.Lock()
            locks[None].release()
        locks[header['table_id']].acquire(True)
        print("{}: {}".format(subscription_id, header))
        pusher.push_data(header, data)
        locks[header['table_id']].release()

if __name__=='__main__':
    loop = asyncio.get_event_loop()
    task_pusher = PubsubSubscriber(sub_client=pubsub_v1.SubscriberClient()).stream('x-i-a-test', 'agent-001-debug', callback=callback)
    loop.run_until_complete(asyncio.wait([task_pusher]))
    loop.close()