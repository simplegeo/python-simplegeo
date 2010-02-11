import time
import urllib
import oauth2 as oauth
import simplejson as json
from httplib2 import Http
from urlparse import urljoin


try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5


API_VERSION = '0.1'


def sgid(layer, id):
    return md5('.'.join((id, layer))).hexdigest()


class Record(object):
    def __init__(self, layer, id, lat, lon, type='object', 
        created=None, **kwargs):
        self.layer = layer
        self.id = id
        self.lon = lon
        self.lat = lat
        self.type = type
        if created is None:
            self.created = int(time.time())
        else:
            self.created = created
        self.__dict__.update(kwargs)

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None

        record = cls(data['properties']['layer'], data['id'], 
            data['geometry']['coordinates'][0], 
            data['geometry']['coordinates'][1])

        record.type = data['properties']['type']
        record.created = data.get('created', record.created)
        record.__dict__.update(dict((k, v) for k, v in data['properties'].iteritems()
                                    if k not in ('layer', 'type', 'created')))
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

    def __hash__(self):
        return hash(self.sgid)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    @property
    def sgid(self):
        return sgid(self.layer, self.id)


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(self, code, message, headers):
        self._code = code
        self._message = message
        self._headers = headers

    def __getitem__(self, key):
        if key == 'code':
            return self._code

        try:
            return self._headers[key]
        except KeyError:
            return None

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s (#%s)" % (self._message, self._code)


class DecodeError(APIError):
    """There was a problem decoding the API's JSON response."""

    def __init__(self, headers, body):
        APIError.__init__(self, 0, "Could not decode JSON.", headers)
        self._body = body

    def __repr__(self):
        return "%s - %s" % (self._headers, self._body)


class Client(object):
    realm = "http://api.simplegeo.com"
    debug = False
    endpoints = {
        'record': 'records/%(layer)s/%(id)s.json',
        'records': 'records/%(layer)s/%(ids)s.json',
        'add_records': 'records/%(layer)s.json',
        'history': 'records/%(layer)s/%(id)s/history.json',
        'nearby': 'nearby/%(arg)s.json',
        'nearby_address': 'nearby/address/%(lat)s,%(lon)s.json',
        'user_stats': 'stats.json',
        'user_stats_bytime': 'stats/%(start)d,%(end)d.json',
        'layer': 'layer/%(layer)s.json',
        'layer_stats': 'stats/%(layer)s.json',
        'layer_stats_bytime': 'stats/%(layer)s/%(start)d,%(end)d.json',
    }

    def __init__(self, key, secret, api_version=API_VERSION,
        host="api.simplegeo.com", port=80):
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
        return "%s (%s, %s)" % (self.uri, self.secret, self.key)

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

    def get_nearby(self, arg, **kwargs):
        endpoint = self.endpoint('nearby', arg=arg)
        return self._request(endpoint, "GET", data=kwargs)

    def get_nearby_address(self, lat, lon):
        endpoint = self.endpoint('nearby_address', lat=lat, lon=lon)
        return self._request(endpoint, "GET")

    def get_user_stats(self, start=None, end=None):
        if start is not None:
            if end is None:
                end = time.time()
            endpoint = self.endpoint('user_stats_bytime', start=start, end=end)
        else:
            endpoint = self.endpoint('user_stats')
        return self._request(endpoint, "GET")

    def get_layer(self, layer):
        endpoint = self.endpoint('layer', layer=layer)
        return self._request(endpoint, "GET")

    def get_layer_stats(self, layer, start=None, end=None):
        if start is not None:
            if not end is None:
                end = time.time()
            endpoint = self.endpoint('layer_stats_bytime', layer=layer, start=start, end=end)
        else:
            endpoint = self.endpoint('layer_stats', layer=layer)
        return self._request(endpoint, "GET")

    def _request(self, endpoint, method, data=None):
        body = None
        params = {}
        if method == "GET" and isinstance(data, dict):
            params = data
            endpoint = endpoint + '?' + urllib.urlencode(data)
        else:
            if isinstance(data, dict):
                body = urllib.urlencode(data)
            else:
                body = data

        request = oauth.Request.from_consumer_and_token(self.consumer, 
            http_method=method, http_url=endpoint, parameters=params)

        request.sign_request(self.signature, self.consumer, None)
        headers = request.to_header(self.realm)
        headers['User-Agent'] = 'SimpleGeo Python Client v%s' % API_VERSION

        resp, content = self.http.request(endpoint, method, body=body,
            headers=headers)

        if self.debug:
            print resp
            print content
        
	try:
            content = json.loads(content)
        except:
            pass
        
	if resp['status'][0] != '2':
            
            code = resp['status']
            message = content
            if isinstance(content, dict):
                code = content['code']
                message = content['message']
            
            raise APIError(code, message, resp)
        
	return content
