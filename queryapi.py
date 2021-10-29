import requests
import time
import json

apiroot = 'http://127.0.0.1:2'

def getprofile(viewer_id: int, interval: int = 1, full: bool = False) -> dict:
    reqid = json.loads(requests.get(f'{apiroot}/enqueue?full={full}&target_viewer_id={viewer_id}').content.decode('utf8'))['reqeust_id']

    if reqid is None:
        return "id err"

    while True:
        query = json.loads(requests.get(f'{apiroot}/query?request_id={reqid}').content.decode('utf8'))
        status = query['status']
        if status == 'done':
            return query['data']
        elif status == 'queue':
            time.sleep(interval)
        else: # notfound or else
            return "queue"
