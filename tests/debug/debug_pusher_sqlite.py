import os
import gzip
import json
import base64
import threading
import asyncio
import sqlite3
from google.cloud import pubsub_v1
from xialib_gcp import PubsubSubscriber
import google.auth
from xialib import SQLiteAdaptor, BasicStorer
from pyagent import Pusher

project_id = google.auth.default()[1]
if os.path.exists(os.path.join('.', 'debug.db')):
    os.remove(os.path.join('.', 'debug.db'))
conn = sqlite3.connect(os.path.join('.', 'debug.db'), check_same_thread=False)
adaptor = SQLiteAdaptor(connection=conn)
adaptor.create_table(SQLiteAdaptor._ctrl_table_id, '', dict(), SQLiteAdaptor._ctrl_table)
adaptor.create_table(SQLiteAdaptor._ctrl_log_id, '', dict(), SQLiteAdaptor._ctrl_log_table)
storer = BasicStorer()
adaptor_dict = {'.': adaptor, 'NPL.': adaptor}

locks = {None: threading.Lock()}

def callback(s: PubsubSubscriber, message: dict, source, subscription_id):
    global project_id
    global storer
    global adaptor_dict
    global locks

    pusher = Pusher(storers=[storer], adaptor_dict=adaptor_dict)
    header, data, id = s.unpack_message(message)
    s.ack(project_id, subscription_id, id)
    if subscription_id == 'agent-001-debug':
        if locks.get(header['table_id'], None) is None:
            locks[None].acquire(True)
            if locks.get(header['table_id'], None) is None:
                locks[header['table_id']] = threading.Lock()
            locks[None].release()
        locks[header['table_id']].acquire(True)
        print("{}: {}".format(subscription_id, header))
        pusher.push_data(dict(header), data)
        locks[header['table_id']].release()

if __name__=='__main__':
    loop = asyncio.get_event_loop()
    task_pusher = PubsubSubscriber(sub_client=pubsub_v1.SubscriberClient()).stream('x-i-a-test', 'agent-001', callback=callback)
    loop.run_until_complete(asyncio.wait([task_pusher]))
    loop.close()