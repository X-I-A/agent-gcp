import os
import json
import base64
import gzip
import hashlib
from flask import Flask, request, Response, render_template
import google.auth
from google.cloud import bigquery
from xialib_gcp import BigQueryAdaptor, GCSStorer
from pyagent import Pusher


app = Flask(__name__)

project_id = google.auth.default()[1]
bigquery_db = bigquery.Client()
gcs_storer = GCSStorer()


@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template("index.html"), 200
    envelope = request.get_json()
    if not envelope:
        return "no Pub/Sub message received", 204
    if not isinstance(envelope, dict) or 'message' not in envelope:
        return "invalid Pub/Sub message format", 204
    data_header = envelope['message']['attributes']
    data_body = json.loads(gzip.decompress(base64.b64decode(envelope['message']['data'])).decode())

    global bigquery_db
    global gcs_storer
    global project_id

    storers = [gcs_storer]
    adapter = BigQueryAdaptor(connection=bigquery_db, project_id=project_id)
    adapter_dict = {'.': adapter, 'SLTNPL.': adapter}
    pusher = Pusher(storers=storers, adaptor_dict=adapter_dict)

    if pusher.push_data(data_header, data_body):
        return "message received", 200
    else:  # pragma: no cover
        return "message to be resent", 400  # pragma: no cover

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))  # pragma: no cover