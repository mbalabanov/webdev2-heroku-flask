import os

if os.environ.get("REDIS_URL"):  # if Redis exists
    from redis import Redis
    from redis import from_url
else:  # else use TinyDB
    from tinydb import TinyDB, Query
    from tinydb.storages import MemoryStorage

    class Redis:
        def __init__(self, host='localhost', port=6379,
                     db=0, password=None, socket_timeout=None,
                     socket_connect_timeout=None,
                     socket_keepalive=None, socket_keepalive_options=None,
                     connection_pool=None, unix_socket_path=None,
                     encoding='utf-8', encoding_errors='strict',
                     charset=None, errors=None,
                     decode_responses=False, retry_on_timeout=False,
                     ssl=False, ssl_keyfile=None, ssl_certfile=None,
                     ssl_cert_reqs='required', ssl_ca_certs=None,
                     max_connections=None):
            self.tinydb = TinyDB(storage=MemoryStorage)

        def get(self, name):
            result_dict = self.tinydb.get(Query()["name"] == name)

            if result_dict and result_dict["value"]:
                return result_dict["value"].encode()
            else:
                return None

        def delete(self, *names):
            for name in names:
                self.tinydb.remove(Query()["name"] == name)
            return True


        def set(self, name, value):
            self.tinydb.upsert({"name": name, "value": value}, Query()["name"] == name)
            return True

    def from_url(url, db=None, **kwargs):
        return Redis()
