import unittest
import urllib
from decimal import Decimal as D

import mock

from simplegeo import Client
from simplegeo.models import Feature
from simplegeo.util import APIError, DecodeError

MY_OAUTH_KEY = 'MY_OAUTH_KEY'
MY_OAUTH_SECRET = 'MY_SECRET_KEY'
TESTING_LAYER = 'TESTING_LAYER'

API_VERSION = '1.0'
API_HOST = 'api.simplegeo.com'
API_PORT = 80

# example: http://api.simplegeo.com/0.1/context/37.797476,-122.424082.json

class ContextTest(unittest.TestCase):

    def setUp(self):
        self.client = Client(MY_OAUTH_KEY, MY_OAUTH_SECRET, host=API_HOST, port=API_PORT)
        self.query_lat = D('37.8016')
        self.query_lon = D('-122.4783')

    def _record(self):
        self.record_id += 1
        self.record_lat = (self.record_lat + 10) % 90
        self.record_lon = (self.record_lon + 10) % 180

        return Feature(
            layer=TESTING_LAYER,
            id=str(self.record_id),
            coordinates=(self.record_lat, self.record_lon)
        )

    def test_wrong_endpoint(self):
        self.assertRaises(Exception, self.client._endpoint, 'wrongwrong')

    def test_missing_argument(self):
        self.assertRaises(Exception, self.client._endpoint, 'context')

    def test_get_context(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        res = self.client.context.get_context(self.query_lat, self.query_lon)
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/%s,%s.json' % (API_VERSION, self.query_lat, self.query_lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')
        # the code under test is required to have json-decoded this before handing it back
        self.failUnless(isinstance(res, dict), (type(res), repr(res)))

    @mock.patch('oauth2.Request.make_timestamp')
    @mock.patch('oauth2.Request.make_nonce')
    def test_oauth(self, mock_make_nonce, mock_make_timestamp):
        mock_make_nonce.return_value = 5
        mock_make_timestamp.return_value = 6

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        self.client.context.get_context(self.query_lat, self.query_lon)

        self.assertEqual(mockhttp.method_calls[0][2]['body'], None)
        self.assertEqual(mockhttp.method_calls[0][2]['headers']['Authorization'], 'OAuth realm="http://api.simplegeo.com", oauth_body_hash="2jmj7l5rSw0yVb%2FvlWAYkK%2FYBwk%3D", oauth_nonce="5", oauth_timestamp="6", oauth_consumer_key="MY_OAUTH_KEY", oauth_signature_method="HMAC-SHA1", oauth_version="1.0", oauth_signature="aCYUTCHSeVlAQiu0CmG2tF71I74%3D"')

    def test_get_context_by_address(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        addr = '41 Decatur St, San Francisco, CA'
        self.client.context.get_context_by_address(addr)
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/address.json?address=%s' % (API_VERSION, urllib.quote_plus(addr)))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_get_context_by_my_ip(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        self.client.context.get_context_by_my_ip()
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/ip.json' % (API_VERSION,))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_get_context_by_ip(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        ipaddr = '192.0.32.10'
        self.client.context.get_context_by_ip(ipaddr=ipaddr)
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/%s.json' % (API_VERSION, ipaddr))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_get_context_by_ip_invalid(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        self.failUnlessRaises(AssertionError, self.client.context.get_context_by_ip, '40.1,127.999')

    def test_get_context_invalid(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.context.http = mockhttp

        self.failUnlessRaises(AssertionError, self.client.context.get_context, -91, 100)
        self.failUnlessRaises(AssertionError, self.client.context.get_context, -11, 361)

    def test_get_context_no_body(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, None)
        self.client.context.http = mockhttp

        self.failUnlessRaises(DecodeError, self.client.context.get_context, self.query_lat, self.query_lon)
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/%s,%s.json' % (API_VERSION, self.query_lat, self.query_lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_get_context_bad_json(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY + 'some crap')
        self.client.context.http = mockhttp

        try:
            self.client.context.get_context(self.query_lat, self.query_lon)
        except DecodeError, e:
            self.failUnlessEqual(e.code,None,repr(e.code))
            self.failUnless("Could not decode" in e.msg, repr(e.msg))
            repr(e)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/%s,%s.json' % (API_VERSION, self.query_lat, self.query_lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_get_context_error(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '500', 'content-type': 'application/json', }, '{"message": "help my web server is confuzzled"}')
        self.client.context.http = mockhttp

        try:
            self.client.context.get_context(self.query_lat, self.query_lon)
        except APIError, e:
            self.failUnlessEqual(e.code, 500, repr(e.code))
            self.failUnlessEqual(e.msg, '{"message": "help my web server is confuzzled"}', (type(e.msg), repr(e.msg)))

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/context/%s,%s.json' % (API_VERSION, self.query_lat, self.query_lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_APIError(self):
        e = APIError(500, 'whee', {'status': "500"})
        self.failUnlessEqual(e.code, 500)
        self.failUnlessEqual(e.msg, 'whee')
        repr(e)
        str(e)


EXAMPLE_BODY="""
{
   "weather": {
    "message" : "'NoneType' object has no attribute 'properties'",
    "code" : 400
    },
   "features": [
    {
     "name" : "06075013000",
     "type" : "Census Tract",
     "bounds": [
      -122.437326,
      37.795016,
      -122.42360099999999,
      37.799485
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Census_Tract%3A06075013000%3A9q8zn0.json"
     },
     {
     "name" : "94123",
     "type" : "Postal",
     "bounds": [
      -122.452966,
      37.792787,
      -122.42360099999999,
      37.810798999999996
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Postal%3A94123%3A9q8zjc.json"
     },
     {
     "name" : "San Francisco",
     "type" : "County",
     "bounds": [
      -123.173825,
      37.639829999999996,
      -122.28178,
      37.929823999999996
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/County%3ASan_Francisco%3A9q8yvv.json"
     },
     {
     "name" : "San Francisco",
     "type" : "City",
     "bounds": [
      -123.173825,
      37.639829999999996,
      -122.28178,
      37.929823999999996
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/City%3ASan_Francisco%3A9q8yvv.json"
     },
     {
     "name" : "Congressional District 8",
     "type" : "Congressional District",
     "bounds": [
      -122.612285,
      37.708131,
      -122.28178,
      37.929823999999996
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Congressional_District%3ACongressional_Di%3A9q8yyn.json"
     },
     {
     "name" : "United States of America",
     "type" : "Country",
     "bounds": [
      -179.14247147726383,
      18.930137634111077,
      179.78114994357418,
      71.41217966730892
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Country%3AUnited_States_of%3A9z12zg.json"
     },
     {
     "name" : "Pacific Heights",
     "type" : "Neighborhood",
     "bounds": [
      -122.446782,
      37.787529,
      -122.422182,
      37.797728
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Neighborhood%3APacific_Heights%3A9q8yvz.json"
     },
     {
     "name" : "San Francisco1",
     "type" : "Urban Area",
     "bounds": [
      -122.51666666668193,
      37.19166666662851,
      -121.73333333334497,
      38.04166666664091
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Urban_Area%3ASan_Francisco1%3A9q9jsg.json"
     },
     {
     "name" : "California",
     "type" : "Province",
     "bounds": [
      -124.48200299999999,
      32.528832,
      -114.131211,
      42.009516999999995
     ],
     "href" : "http://api.simplegeo.com/0.1/boundary/Province%3ACA%3A9qdguu.json"
     }
   ],
   "demographics": {
    "metro_score" : "10"
    }
   }
"""
