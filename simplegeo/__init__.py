from _version import __version__

import pkg_resources
pkg_resources.declare_namespace(__name__)


import urllib
from urlparse import urljoin

from httplib2 import Http
import oauth2 as oauth
from pyutil import jsonutil as json
from pyutil.assertutil import precondition

from simplegeo.models import Feature
from simplegeo.util import json_decode, APIError, is_numeric, is_valid_lat, is_valid_lon, SIMPLEGEOHANDLE_RSTR, is_simplegeohandle, to_unicode, is_valid_ip


class Client(object):

    realm = "http://api.simplegeo.com"
    endpoints = {
        # Shared
        'feature': '1.0/features/%(simplegeohandle)s.json',
        'annotations': '1.0/features/%(simplegeohandle)s/annotations.json',
        # More endpoints are added by mixins.
    }

    def __init__(self, key, secret, host="api.simplegeo.com", port=80):
        self.host = host
        self.port = port
        self.consumer = oauth.Consumer(key, secret)
        self.key = key
        self.secret = secret
        self.signature = oauth.SignatureMethod_HMAC_SHA1()
        self.uri = "http://%s:%s" % (host, port)
        self.http = Http()
        self.headers = None

        self.context = ContextClientMixin(self)
        self.places = PlacesClientMixin(self)
        self.storage = StorageClientMixin(self)

    def get_most_recent_http_headers(self):
        """ Intended for debugging -- return the most recent HTTP
        headers which were received from the server. """
        return self.headers

    def _endpoint(self, name, **kwargs):
        """Not used directly. Finds and formats the endpoints as needed for any type of request."""
        try:
            endpoint = self.endpoints[name]
        except KeyError:
            raise Exception('No endpoint named "%s"' % name)
        try:
            endpoint = endpoint % kwargs
        except KeyError, e:
            raise TypeError('Missing required argument "%s"' % (e.args[0],))
        return urljoin(urljoin(self.uri, '/'), endpoint)

    def get_feature(self, simplegeohandle):
        """Return the GeoJSON representation of a feature."""
        if not is_simplegeohandle(simplegeohandle):
            raise TypeError("simplegeohandle is required to match the regex %s, but it was %s :: %r" % (SIMPLEGEOHANDLE_RSTR, type(simplegeohandle), simplegeohandle))
        endpoint = self._endpoint('feature', simplegeohandle=simplegeohandle)
        return Feature.from_json(self._request(endpoint, 'GET')[1])

    def get_annotations(self, simplegeohandle):
        if not is_simplegeohandle(simplegeohandle):
            raise TypeError("simplegeohandle is required to match the regex %s, but it was %s :: %r" % (SIMPLEGEOHANDLE_RSTR, type(simplegeohandle), simplegeohandle))
        endpoint = self._endpoint('annotations', simplegeohandle=simplegeohandle)
        return json_decode(self._request(endpoint, 'GET')[1])

    def annotate(self, simplegeohandle, annotations, private):
        if not isinstance(annotations, dict):
            raise TypeError('annotations must be of type dict')
        if not len(annotations.keys()):
            raise ValueError('annotations dict is empty')
        for annotation_type in annotations.keys():
            if not len(annotations[annotation_type].keys()):
                raise ValueError('annotation type "%s" is empty' % annotation_type)
        if not isinstance(private, bool):
            raise TypeError('private must be of type bool')

        data = {'annotations': annotations,
                'private': private}

        endpoint = self._endpoint('annotations', simplegeohandle=simplegeohandle)
        return json_decode(self._request(endpoint,
                                        'POST',
                                        data=json.dumps(data))[1])

    def _request(self, endpoint, method, data=None):
        """
        Not used directly by code external to this lib. Performs the
        actual request against the API, including passing the
        credentials with oauth.  Returns a tuple of (headers as dict,
        body as string).
        """
        if data is not None:
            data = to_unicode(data)
        params = {}
        body = data
        request = oauth.Request.from_consumer_and_token(self.consumer,
            http_method=method, http_url=endpoint, parameters=params)

        request.sign_request(self.signature, self.consumer, None)
        headers = request.to_header(self.realm)
        headers['User-Agent'] = 'SimpleGeo Python Client v%s' % __version__

        self.headers, content = self.http.request(endpoint, method, body=body, headers=headers)

        if self.headers['status'][0] not in ('2', '3'):
            raise APIError(int(self.headers['status']), content, self.headers)

        return self.headers, content


class ContextClientMixin(object):

    def __init__(self, client):
        self.client = client

        self.client.endpoints.update([
            # Context
            ('context', '1.0/context/%(lat)s,%(lon)s.json'),
            ('context_by_ip', '1.0/context/%(ip)s.json'),
            ('context_by_my_ip', '1.0/context/ip.json'),
            ('context_by_address', '1.0/context/address.json?address=%(address)s')])

    def get_context(self, lat, lon):
        precondition(is_valid_lat(lat), lat)
        precondition(is_valid_lon(lon), lon)
        endpoint = self.client._endpoint('context', lat=lat, lon=lon)
        return json_decode(self.client._request(endpoint, "GET")[1])

    def get_context_by_ip(self, ipaddr):
        """ The server uses guesses the latitude and longitude from
        the ipaddr and then does the same thing as get_context(),
        using that guessed latitude and longitude."""
        precondition(is_valid_ip(ipaddr), ipaddr)
        endpoint = self.client._endpoint('context_by_ip', ip=ipaddr)
        return json_decode(self.client._request(endpoint, "GET")[1])

    def get_context_by_my_ip(self):
        """ The server gets the IP address from the HTTP connection
        (this may be the IP address of your device or of a firewall,
        NAT, or HTTP proxy device between you and the server), and
        then does the same thing as get_context_by_ip(), using that IP
        address."""
        endpoint = self.client._endpoint('context_by_my_ip')
        print endpoint
        return json_decode(self.client._request(endpoint, "GET")[1])

    def get_context_by_address(self, address):
        """
        The server figures out the latitude and longitude from the
        street address and then does the same thing as get_context(),
        using that deduced latitude and longitude.
        """
        precondition(isinstance(address, basestring), address)
        endpoint = self.client._endpoint('context_by_address', address=urllib.quote_plus(address))
        return json_decode(self.client._request(endpoint, "GET")[1])


class PlacesClientMixin(object):

    def __init__(self, client):
        self.client = client

        self.client.endpoints.update([
            # Places
            ('create', '1.0/places'),
            ('search', '1.0/places/%(lat)s,%(lon)s.json%(quargs)s'),
            ('search_by_ip', '1.0/places/%(ipaddr)s.json%(quargs)s'),
            ('search_by_my_ip', '1.0/places/ip.json%(quargs)s'),
            ('search_by_address', '1.0/places/address.json?%(quargs)s')])

    """PLACES"""

    def add_feature(self, feature):
        """Create a new feature, returns the simplegeohandle. """
        endpoint = self.client._endpoint('create')
        if feature.id:
            # only simplegeohandles or None should be stored in self.id
            assert is_simplegeohandle(feature.id)
            raise ValueError('A feature cannot be added to the Places database when it already has a simplegeohandle: %s' % (feature.id,))
        jsonrec = feature.to_json()
        resp, content = self.client._request(endpoint, "POST", jsonrec)
        if resp['status'] != "202":
            raise APIError(int(resp['status']), content, resp)
        contentobj = json_decode(content)
        if not contentobj.has_key('id'):
            raise APIError(int(resp['status']), content, resp)
        handle = contentobj['id']
        assert is_simplegeohandle(handle)
        return handle

    def update_feature(self, feature):
        """Update a Places feature."""
        endpoint = self.client._endpoint('feature', simplegeohandle=feature.id)
        return self.client._request(endpoint, 'POST', feature.to_json())[1]

    def delete_feature(self, simplegeohandle):
        """Delete a Places feature."""
        precondition(is_simplegeohandle(simplegeohandle), "simplegeohandle is required to match the regex %s" % SIMPLEGEOHANDLE_RSTR, simplegeohandle=simplegeohandle)
        endpoint = self.client._endpoint('feature', simplegeohandle=simplegeohandle)
        return self.client._request(endpoint, 'DELETE')[1]

    def search(self, lat, lon, radius=None, query=None, category=None):
        """Search for places near a lat/lon, within a radius (in kilometers)."""
        precondition(is_valid_lat(lat), lat)
        precondition(is_valid_lon(lon), lon)
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        quargs = urllib.urlencode(kwargs)
        if quargs:
            quargs = '?'+quargs
        endpoint = self.client._endpoint('search', lat=lat, lon=lon, quargs=quargs)

        result = self.client._request(endpoint, 'GET')[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_ip(self, ipaddr, radius=None, query=None, category=None):
        """
        Search for places near an IP address, within a radius (in
        kilometers).

        The server uses guesses the latitude and longitude from the
        ipaddr and then does the same thing as search(), using that
        guessed latitude and longitude.
        """
        precondition(is_valid_ip(ipaddr), ipaddr)
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        quargs = urllib.urlencode(kwargs)
        if quargs:
            quargs = '?'+quargs
        endpoint = self.client._endpoint('search_by_ip', ipaddr=ipaddr, quargs=quargs)

        result = self.client._request(endpoint, 'GET')[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_my_ip(self, radius=None, query=None, category=None):
        """
        Search for places near your IP address, within a radius (in
        kilometers).

        The server gets the IP address from the HTTP connection (this
        may be the IP address of your device or of a firewall, NAT, or
        HTTP proxy device between you and the server), and then does
        the same thing as search_by_ip(), using that IP address.
        """
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        quargs = urllib.urlencode(kwargs)
        if quargs:
            quargs = '?'+quargs
        endpoint = self.client._endpoint('search_by_my_ip', quargs=quargs)

        result = self.client._request(endpoint, 'GET')[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_address(self, address, radius=None, query=None, category=None):
        """
        Search for places near the given address, within a radius (in
        kilometers).

        The server figures out the latitude and longitude from the
        street address and then does the same thing as search(), using
        that deduced latitude and longitude.
        """
        precondition(isinstance(address, basestring), address)
        precondition(address != '', address)
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

        if isinstance(address, unicode):
            address = address.encode('utf-8')
        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { 'address': address }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        quargs = urllib.urlencode(kwargs)
        endpoint = self.client._endpoint('search_by_address', quargs=quargs)

        result = self.client._request(endpoint, 'GET')[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]


class StorageClientMixin(object):

    def __init__(self, client):
        self.client = client

        self.client.endpoints.update([
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

        endpoint = self.client._endpoint('record', layer=record.layer, id=record.id)
        self.client._request(endpoint, "PUT", record.to_json())

    def add_records(self, layer, records):
        features = {
            'type': 'FeatureCollection',
            'features': [record.to_dict() for record in records],
        }
        endpoint = self.client._endpoint('add_records', layer=layer)
        self.client._request(endpoint, "POST", json.dumps(features))

    def delete_record(self, layer, id):
        endpoint = self.client._endpoint('record', layer=layer, id=id)
        self.client._request(endpoint, "DELETE")

    def get_record(self, layer, id):
        endpoint = self.client._endpoint('record', layer=layer, id=id)
        return json_decode(self.client._request(endpoint, "GET")[1])

    def get_records(self, layer, ids):
        endpoint = self.client._endpoint('records', layer=layer, ids=','.join(ids))
        features = json_decode(self.client._request(endpoint, "GET")[1])
        return features.get('features') or []

    def get_history(self, layer, id, **kwargs):
        quargs = urllib.urlencode(kwargs)
        if quargs:
                quargs = '?'+quargs
        endpoint = self.client._endpoint('history', layer=layer, id=id)
        return json_decode(self.client._request(endpoint, "GET", data=quargs)[1])

    def get_nearby(self, layer, lat, lon, **kwargs):
        quargs = urllib.urlencode(kwargs)
        if quargs:
            quargs = '?'+quargs
        endpoint = self.client._endpoint('nearby', layer=layer, arg='%s,%s' % (lat, lon))
        return json_decode(self.client._request(endpoint, "GET", data=quargs)[1])

    def get_layer(self, layer):
        endpoint = self.client._endpoint('layer', layer=layer)
        return json_decode(self.client._request(endpoint, "GET")[1])

    """ Waiting on Gate
    def get_nearby_ip_address(self, layer, ip_address, **kwargs):
        endpoint = self.client._endpoint('nearby', layer=layer, arg=ip_address)
        return self.client._request(endpoint, "GET", data=kwargs)
    """

    """Pre-release layer management methods."""

    def create_layer(self, layer):
        endpoint = self.client._endpoint('layer', layer=layer.name)
        return json_decode(self.client._request(endpoint, "PUT", layer.to_json())[1])

    def update_layer(self, layer):
        return self.create_layer(layer)

    def delete_layer(self, name):
        endpoint = self.client._endpoint('layer', layer=name)
        return json_decode(self.client._request(endpoint, "DELETE")[1])

    def get_layer(self, name):
        endpoint = self.client._endpoint('layer', layer=name)
        return json_decode(self.client._request(endpoint, "GET")[1])

    def get_layers(self):
        endpoint = self.client._endpoint('layers')
        return json_decode(self.client._request(endpoint, "GET")[1])
