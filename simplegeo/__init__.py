from _version import __version__

from urlparse import urljoin
import urllib
from httplib2 import Http
import oauth2 as oauth
from pyutil import jsonutil as json

from simplegeo.models import Feature
from simplegeo.util import json_decode, APIError, SIMPLEGEOHANDLE_RSTR, is_simplegeohandle, to_unicode

# For backwards compatibility with other codebases.
from simplegeo.util import APIError, DecodeError
from simplegeo.models import Record


# This is arbitrary for now.  Storage URLs are still /0.1/.  Left this in the constructors for future use.
API_VERSION = '1.0'


class Client(object):

    realm = "http://api.simplegeo.com"
    endpoints = {
        # Shared
        'feature': '1.0/features/%(simplegeohandle)s.json',
        'annotations': '1.0/features/%(simplegeohandle)s/annotations.json',
        # More endpoints are added by mixins.
    }

    def __init__(self, key, secret, api_version=API_VERSION, host="api.simplegeo.com", port=80):
        self.host = host
        self.port = port
        self.consumer = oauth.Consumer(key, secret)
        self.key = key
        self.secret = secret
        self.signature = oauth.SignatureMethod_HMAC_SHA1()
        self.uri = "http://%s:%s" % (host, port)
        self.http = Http()
        self.headers = None

        self.subclient = getattr(self, 'subclient', False)

        # Do not create recursive subclients.
        # Only create subclients if we are running __init__() from Client.
        if not self.subclient:
            self.context = ContextClient(key, secret, host=host, port=port)
            self.places = PlacesClient(key, secret, host=host, port=port)
            self.storage = StorageClient(key, secret, host=host, port=port)

    # For backwards compatibility with the old Storage client.
    def __getattr__(self, name):
        if name not in ['storage']:
            return getattr(self.storage, name)

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
        body = None
        params = {}
        if method == 'GET' and isinstance(data, dict) and len(data) > 0:
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
        headers['User-Agent'] = 'SimpleGeo Python Client v%s' % __version__

        self.headers, content = self.http.request(endpoint, method, body=body, headers=headers)

        if self.headers['status'][0] not in ('2', '3'):
            raise APIError(int(self.headers['status']), content, self.headers)

        return self.headers, content


from simplegeo.context import Client as ContextClient
from simplegeo.places import Client as PlacesClient
from simplegeo.storage import Client as StorageClient
