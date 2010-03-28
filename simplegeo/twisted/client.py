import urllib
import oauth2 as oauth

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor
from twisted.web import client
from twisted.web.http_headers import Headers

import simplegeo
from simplegeo.twisted.util import StringProducer, receive_body

try:
    import simplejson as json
except ImportError:
    import json

class Client(simplegeo.Client):
    @inlineCallbacks
    def get_records(self, layer, ids):
        endpoint = self.endpoint('records', layer=layer, ids=','.join(ids))
        features = yield self._request(endpoint, "GET")
        returnValue(features.get('features') or [])
    
    @inlineCallbacks
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
        
        request = oauth.Request.from_consumer_and_token(self.consumer, 
            http_method=method, http_url=endpoint, parameters=params)
        request.sign_request(self.signature, self.consumer, None)

        headers = request.to_header(self.realm)
        headers['User-Agent'] = 'SimpleGeo Twisted Client v%s' % simplegeo.API_VERSION
        headers = Headers(dict([(k, [v]) for k, v in headers.items()]))
        
        agent = client.Agent(reactor)
                
        response = yield agent.request(method, endpoint, headers, (body and StringProducer(body)))
        
        body = yield receive_body(response)
        
        if body: # Empty body is allowed.
            try:
                body = json.loads(body)
            except ValueError:
                raise DecodeError(resp, body)

        if str(response.code)[0] != '2':
            code = str(response.code)
            message = body
            if isinstance(body, dict):
                code = body['code']
                message = body['message']

            raise simplegeo.Client.APIError(code, message, response.headers)

        returnValue(body)