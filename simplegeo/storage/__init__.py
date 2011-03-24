import urllib

from pyutil import jsonutil as json

from simplegeo.util import json_decode
from simplegeo import Client as ParentClient


class Client(ParentClient):

    def __init__(self, key, secret, api_version='0.1', host='api.simplegeo.com', port=80):
        self.subclient = True
        ParentClient.__init__(self, key, secret, host=host, port=port)

        self.endpoints.update([
            ('record', '0.1/records/%(layer)s/%(id)s.json'),
            ('records', '0.1/records/%(layer)s/%(ids)s.json'),
            ('add_records', '0.1/records/%(layer)s.json'),
            ('history', '0.1/records/%(layer)s/%(id)s/history.json'),
            ('nearby', '0.1/records/%(layer)s/nearby/%(arg)s.json'),
            ('layer', '0.1/layers/%(layer)s.json'),
            ('layers', '0.1/layers.json')])

    def add_record(self, record):
        if not hasattr(record, 'layer'):
            raise Exception("Record has no layer.")

        endpoint = self._endpoint('record', layer=record.layer, id=record.id)
        self._request(endpoint, "PUT", record.to_json())

    def add_records(self, layer, records):
        features = {
            'type': 'FeatureCollection',
            'features': [record.to_dict() for record in records],
        }
        endpoint = self._endpoint('add_records', layer=layer)
        self._request(endpoint, "POST", json.dumps(features))

    def delete_record(self, layer, id):
        endpoint = self._endpoint('record', layer=layer, id=id)
        self._request(endpoint, "DELETE")

    def get_record(self, layer, id):
        endpoint = self._endpoint('record', layer=layer, id=id)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_records(self, layer, ids):
        endpoint = self._endpoint('records', layer=layer, ids=','.join(ids))
        features = json_decode(self._request(endpoint, "GET")[1])
        return features.get('features') or []

    def get_history(self, layer, id, **kwargs):
        endpoint = self._endpoint('history', layer=layer, id=id)
        return json_decode(self._request(endpoint, "GET", data=kwargs)[1])

    def get_nearby(self, layer, lat, lon, **kwargs):
        endpoint = self._endpoint('nearby', layer=layer, arg='%s,%s' % (lat, lon))
        return json_decode(self._request(endpoint, "GET", data=kwargs)[1])

    """ Waiting on Gate
    def get_nearby_ip_address(self, layer, ip_address, **kwargs):
        endpoint = self._endpoint('nearby', layer=layer, arg=ip_address)
        return self._request(endpoint, "GET", data=kwargs)
    """

    """Layer management methods."""

    def create_layer(self, layer):
        endpoint = self._endpoint('layer', layer=layer.name)
        return json_decode(self._request(endpoint, "PUT", layer.to_json())[1])

    def update_layer(self, layer):
        return self.create_layer(layer)

    def delete_layer(self, name):
        endpoint = self._endpoint('layer', layer=name)
        return json_decode(self._request(endpoint, "DELETE")[1])

    def get_layer(self, name):
        endpoint = self._endpoint('layer', layer=name)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_layers(self):
        endpoint = self._endpoint('layers')
        return json_decode(self._request(endpoint, "GET")[1])
