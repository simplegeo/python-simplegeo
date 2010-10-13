import time
import urllib
import oauth2 as oauth
import simplejson as json
from httplib2 import Http
from urlparse import urljoin

__version__ = "unknown"
try:
    from _version import __version__
except ImportError:
    # We're running in a tree that doesn't have a version number in _version.py.
    pass

API_VERSION = '0.1'


class Record(object):
    def __init__(self, layer, id, lat, lon, created=None, **kwargs):
        self.layer = layer
        self.id = id
        self.lon = lon
        self.lat = lat
        if created is None:
            self.created = int(time.time())
        else:
            self.created = created
        self.__dict__.update(kwargs)

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        coord = data['geometry']['coordinates']
        record = cls(data['properties']['layer'], data['id'], lat=coord[1], lon=coord[0])
        record.created = data.get('created', record.created)
        record.__dict__.update(dict((k, v) for k, v in data['properties'].iteritems()
                                    if k not in ('layer', 'created')))
        return record

    def to_dict(self):
        return {
            'type': 'Feature',
            'id': self.id,
            'created': self.created,
            'geometry': {
                'type': 'Point',
                'coordinates': [self.lon, self.lat],
            },
            'properties': dict((k, v) for k, v in self.__dict__.iteritems() 
                                        if k not in ('lon', 'lat', 'id', 'created')),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return "Record(layer=%s, id=%s, lat=%s, lon=%s)" % (self.layer, self.id, self.lat, self.lon)

    def __hash__(self):
        return hash((self.layer, self.id))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(self, code, msg, headers):
        self.code = code
        self.msg = msg
        self.headers = headers

    def __getitem__(self, key):
        if key == 'code':
            return self.code

        try:
            return self.headers[key]
        except KeyError:
            raise AttributeError(key)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s (#%s)" % (self.msg, self.code)


class DecodeError(APIError):
    """There was a problem decoding the API's JSON response."""

    def __init__(self, headers, body):
        super(DecodeError, self).__init__(None, "Could not decode JSON", headers)
        self.body = body

    def __repr__(self):
        return "headers: %s, content: <%s>" % (self.headers, self.body)


class Client(object):
    realm = "http://api.simplegeo.com"
    debug = False
    endpoints = {
        'record': 'records/%(layer)s/%(id)s.json',
        'records': 'records/%(layer)s/%(ids)s.json',
        'add_records': 'records/%(layer)s.json',
        'history': 'records/%(layer)s/%(id)s/history.json',
        'nearby': 'records/%(layer)s/nearby/%(arg)s.json',
        'nearby_address': 'nearby/address/%(lat)s,%(lon)s.json',
        'density_day': 'density/%(day)s/%(lat)s,%(lon)s.json',
        'density_hour': 'density/%(day)s/%(hour)s/%(lat)s,%(lon)s.json',
        'layer': 'layer/%(layer)s.json',
        'contains' : 'contains/%(lat)s,%(lon)s.json',
        'overlaps' : 'overlaps/%(south)s,%(west)s,%(north)s,%(east)s.json',
        'boundary' : 'boundary/%(id)s.json',    
        'locate' : 'locate/%(ip_address)s.json',
        'contains_ip_address' : 'contains/%(ip_address)s.json'
    }

    def __init__(self, key, secret, api_version=API_VERSION, host="api.simplegeo.com", port=80):
        self.host = host
        self.port = port
        self.consumer = oauth.Consumer(key, secret)
        self.key = key
        self.secret = secret
        self.api_version = api_version
        self.signature = oauth.SignatureMethod_HMAC_SHA1()
        self.uri = "http://%s:%s" % (host, port)
        self.http = Http()

    def __unicode__(self):
        return "%s (key=%s, secret=%s)" % (self.uri, self.key, self.secret)

    def __repr__(self):
        return self.__unicode__()

    def endpoint(self, name, **kwargs):
        try:
            endpoint = self.endpoints[name]
        except KeyError:
            raise Exception('No endpoint named "%s"' % name)
        try:
            endpoint = endpoint % kwargs
        except KeyError, e:
            raise TypeError('Missing required argument "%s"' % (e.args[0],))
        return urljoin(urljoin(self.uri, self.api_version + '/'), endpoint)

    def add_record(self, record):
        if not hasattr(record, 'layer'):
            raise Exception("Record has no layer.")

        endpoint = self.endpoint('record', layer=record.layer, id=record.id)
        self._request(endpoint, "PUT", record.to_json())

    def add_records(self, layer, records):
        features = {
            'type': 'FeatureCollection',
            'features': [record.to_dict() for record in records],
        }
        endpoint = self.endpoint('add_records', layer=layer)
        self._request(endpoint, "POST", json.dumps(features))

    def delete_record(self, layer, id):
        endpoint = self.endpoint('record', layer=layer, id=id)
        self._request(endpoint, "DELETE")

    def get_record(self, layer, id):
        endpoint = self.endpoint('record', layer=layer, id=id)
        return self._request(endpoint, "GET")

    def get_records(self, layer, ids):
        endpoint = self.endpoint('records', layer=layer, ids=','.join(ids))
        features = self._request(endpoint, "GET")
        return features.get('features') or []

    def get_history(self, layer, id, **kwargs):
        endpoint = self.endpoint('history', layer=layer, id=id)
        return self._request(endpoint, "GET", data=kwargs)

    def get_nearby(self, layer, lat, lon, **kwargs):
        endpoint = self.endpoint('nearby', layer=layer, arg='%s,%s' % (lat, lon))
        return self._request(endpoint, "GET", data=kwargs)

    def get_nearby_geohash(self, layer, geohash, **kwargs):
        endpoint = self.endpoint('nearby', layer=layer, arg=geohash)
        return self._request(endpoint, "GET", data=kwargs)
        
    def get_nearby_address(self, lat, lon):
        endpoint = self.endpoint('nearby_address', lat=lat, lon=lon)
        return self._request(endpoint, "GET")

    def get_nearby_ip_address(self, layer, ip_address, **kwargs):
        endpoint = self.endpoint('nearby', layer=layer, arg=ip_address)
        return self._request(endpoint, "GET", data=kwargs)

    def get_layer(self, layer):
        endpoint = self.endpoint('layer', layer=layer)
        return self._request(endpoint, "GET")

    def get_density(self, lat, lon, day, hour=None):
        if hour is not None:
            endpoint = self.endpoint('density_hour', lat=lat, lon=lon, day=day, hour=hour)
        else:
            endpoint = self.endpoint('density_day', lat=lat, lon=lon, day=day)
        return self._request(endpoint, "GET")

    def get_overlaps(self, south, west, north, east, **kwargs):
        endpoint = self.endpoint('overlaps', south=south, west=west, north=north, east=east)
        return self._request(endpoint, "GET", data=kwargs)

    def get_boundary(self, id):
        endpoint = self.endpoint('boundary', id=id)
        return self._request(endpoint, "GET")

    def get_contains(self, lat, lon):
        endpoint = self.endpoint('contains', lat=lat, lon=lon)
        return self._request(endpoint, "GET")

    def get_locate(self, ip_address):
        endpoint = self.endpoint('locate', ip_address=ip_address)
        return self._request(endpoint, "GET")

    def get_contains_ip_address(self, ip_address):
        endpoint = self.endpoint('contains_ip_address', ip_address=ip_address)
        return self._request(endpoint, "GET")

    def _request(self, endpoint, method, data=None):
        body = None
        params = {}
        if method == "GET" and isinstance(data, dict):
            endpoint = endpoint + '?' + urllib.urlencode(data)
        else:
            if isinstance(data, dict):
                body = urllib.urlencode(data)
            else:
                body = data
        if self.debug:
            print endpoint
        request = oauth.Request.from_consumer_and_token(self.consumer, 
            http_method=method, http_url=endpoint, parameters=params)

        request.sign_request(self.signature, self.consumer, None)
        headers = request.to_header(self.realm)
        headers['User-Agent'] = 'SimpleGeo Client v%s' % __version__

        resp, content = self.http.request(endpoint, method, body=body, headers=headers)

        if self.debug:
            print resp
            print content

        if content: # Empty body is allowed.
            try:
                content = json.loads(content)
            except ValueError:
                raise DecodeError(resp, content)

        if resp['status'][0] != '2':
            code = resp['status']
            message = content
            if isinstance(content, dict):
                code = content['code']
                message = content['message']
            raise APIError(code, message, resp)

        return content

