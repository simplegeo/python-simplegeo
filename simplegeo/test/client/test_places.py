# -*- coding: utf-8 -*-

import unittest
import urllib
from decimal import Decimal as D

from pyutil import jsonutil as json
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

class PlacesTest(unittest.TestCase):

    def setUp(self):
        self.client = Client(MY_OAUTH_KEY, MY_OAUTH_SECRET, host=API_HOST, port=API_PORT)

    def test_wrong_endpoint(self):
        self.assertRaises(Exception, self.client._endpoint, 'featuret')

    def test_missing_argument(self):
        self.assertRaises(Exception, self.client._endpoint, 'features')

    def test_add_feature_norecord_id_nonascii_nonutf8_bytes(self):
        mockhttp = mock.Mock()
        handle = 'SG_abcdefghijklmnopqrstuv'
        newloc = 'http://api.simplegeo.com:80/%s/places/%s.json' % (API_VERSION, handle)
        properties = {
            'name': "B\x92b's H\x92use of M\x92nkeys"
            }
        resultfeature = Feature((D('11.03'), D('10.03')), simplegeohandle=handle, properties=properties)
        methods_called = []
        def mockrequest2(*args, **kwargs):
            methods_called.append(('request', args, kwargs))
            return ({'status': '200', 'content-type': 'application/json', }, resultfeature.to_json())

        def mockrequest(*args, **kwargs):
            self.assertEqual(args[0], 'http://api.simplegeo.com:80/%s/places' % (API_VERSION,))
            self.assertEqual(args[1], 'POST')

            bodyobj = json.loads(kwargs['body'])
            self.failUnlessEqual(bodyobj['id'], None)
            methods_called.append(('request', args, kwargs))
            mockhttp.request = mockrequest2
            return ({'status': '202', 'content-type': 'application/json', 'location': newloc}, json.dumps({'id': handle}))

        mockhttp.request = mockrequest
        self.client.places.http = mockhttp

        feature = Feature(
            coordinates=(D('37.8016'), D('-122.4783'))
        )

        res = self.client.places.add_feature(feature)
        self.failUnlessEqual(res, handle)

    def test_add_feature_norecord_id_nonascii(self):
        mockhttp = mock.Mock()
        handle = 'SG_abcdefghijklmnopqrstuv'
        newloc = 'http://api.simplegeo.com:80/%s/places/%s.json' % (API_VERSION, handle)
        properties = {
            'name': u"B❦b's H❤use of M❥nkeys"
            }
        resultfeature = Feature((D('11.03'), D('10.03')), simplegeohandle=handle, properties=properties)
        methods_called = []
        def mockrequest2(*args, **kwargs):
            methods_called.append(('request', args, kwargs))
            return ({'status': '200', 'content-type': 'application/json', }, resultfeature.to_json())

        def mockrequest(*args, **kwargs):
            self.assertEqual(args[0], 'http://api.simplegeo.com:80/%s/places' % (API_VERSION,))
            self.assertEqual(args[1], 'POST')

            bodyobj = json.loads(kwargs['body'])
            self.failUnlessEqual(bodyobj['id'], None)
            methods_called.append(('request', args, kwargs))
            mockhttp.request = mockrequest2
            return ({'status': '202', 'content-type': 'application/json', 'location': newloc}, json.dumps({'id': handle}))

        mockhttp.request = mockrequest
        self.client.places.http = mockhttp

        feature = Feature(
            coordinates=(D('37.8016'), D('-122.4783'))
        )

        res = self.client.places.add_feature(feature)
        self.failUnlessEqual(res, handle)

    def test_add_feature_norecord_id(self):
        mockhttp = mock.Mock()
        handle = 'SG_abcdefghijklmnopqrstuv'
        newloc = 'http://api.simplegeo.com:80/%s/places/%s.json' % (API_VERSION, handle)
        resultfeature = Feature((D('11.03'), D('10.03')), simplegeohandle=handle)
        methods_called = []
        def mockrequest2(*args, **kwargs):
            methods_called.append(('request', args, kwargs))
            return ({'status': '200', 'content-type': 'application/json', }, resultfeature.to_json())

        def mockrequest(*args, **kwargs):
            self.assertEqual(args[0], 'http://api.simplegeo.com:80/%s/places' % (API_VERSION,))
            self.assertEqual(args[1], 'POST')

            bodyobj = json.loads(kwargs['body'])
            self.failUnlessEqual(bodyobj['id'], None)
            methods_called.append(('request', args, kwargs))
            mockhttp.request = mockrequest2
            return ({'status': '202', 'content-type': 'application/json', 'location': newloc}, json.dumps({'id': handle}))

        mockhttp.request = mockrequest
        self.client.places.http = mockhttp

        feature = Feature(
            coordinates=(D('37.8016'), D('-122.4783'))
        )

        res = self.client.places.add_feature(feature)
        self.failUnlessEqual(res, handle)

    def test_add_feature_simplegeohandle(self):
        handle = 'SG_abcdefghijklmnopqrstuv'
        feature = Feature(
            simplegeohandle=handle,
            coordinates=(D('37.8016'), D('-122.4783'))
        )

        # You can't add-feature on a feature that already has a simplegeo handle. Don't do that.
        self.failUnlessRaises(ValueError, self.client.places.add_feature, feature)

    def test_add_feature_simplegeohandle_and_record_id(self):
        handle = 'SG_abcdefghijklmnopqrstuv'
        record_id = 'this is my record #1. my first record. and it is mine'
        feature = Feature(
            simplegeohandle=handle,
            properties={'record_id': record_id},
            coordinates = (D('37.8016'), D('-122.4783'))
        )

        # You can't add-feature on a feature that already has a simplegeo handle. Don't do that.
        self.failUnlessRaises(ValueError, self.client.places.add_feature, feature)

    def test_add_feature_record_id(self):
        mockhttp = mock.Mock()
        handle = 'SG_abcdefghijklmnopqrstuv'
        record_id = 'this is my record #1. my first record. and it is mine'
        newloc = 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, handle)
        resultfeature = Feature((D('11.03'), D('10.03')), simplegeohandle=handle)
        methods_called = []
        def mockrequest2(*args, **kwargs):
            methods_called.append(('request', args, kwargs))
            return ({'status': '200', 'content-type': 'application/json', }, resultfeature.to_json())

        def mockrequest(*args, **kwargs):
            self.failUnlessEqual(args[0], 'http://api.simplegeo.com:80/%s/places' % (API_VERSION,))
            self.failUnlessEqual(args[1], 'POST')
            bodyobj = json.loads(kwargs['body'])
            self.failUnlessEqual(bodyobj['properties'].get('record_id'), record_id)
            methods_called.append(('request', args, kwargs))
            mockhttp.request = mockrequest2
            return ({'status': '202', 'content-type': 'application/json', 'location': newloc}, json.dumps({'id': handle}))

        mockhttp.request = mockrequest
        self.client.places.http = mockhttp

        feature = Feature(
            properties={'record_id': record_id},
            coordinates = (D('37.8016'), D('-122.4783'))
        )

        res = self.client.places.add_feature(feature)
        self.failUnlessEqual(res, handle)

    def test_get_feature(self):
        handle = 'SG_abcdefghijklmnopqrstuv'
        resultfeature = Feature((D('11.03'), D('10.03')), simplegeohandle=handle)

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, resultfeature.to_json())
        self.client.places.http = mockhttp

        res = self.client.places.get_feature(handle)
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')
        self.failUnless(isinstance(res, Feature), res)
        self.assertEqual(res.to_json(), resultfeature.to_json())

    def test_empty_body(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, None)
        self.client.places.http = mockhttp

        self.client.places._request("http://anyrandomendpoint", 'POST')

        self.failUnless(mockhttp.method_calls[0][2]['body'] is None, (repr(mockhttp.method_calls[0][2]['body']), type(mockhttp.method_calls[0][2]['body'])))

    def test_dont_json_decode_results(self):
        """ _request() is required to return the exact string that the HTTP
        server sent to it -- no transforming it, such as by json-decoding. """

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, '{ "Hello": "I am a string. \xe2\x9d\xa4" }'.decode('utf-8'))
        self.client.places.http = mockhttp
        res = self.client.places._request("http://thing", 'POST')[1]
        self.failUnlessEqual(res, '{ "Hello": "I am a string. \xe2\x9d\xa4" }'.decode('utf-8'))

    def test_dont_Featureify_results(self):
        """ _request() is required to return the exact string that the HTTP
        server sent to it -- no transforming it, such as by json-decoding and
        then constructing a Feature. """

        EXAMPLE_RECORD_JSONSTR=json.dumps({ 'geometry' : { 'type' : 'Point', 'coordinates' : [D('10.0'), D('11.0')] }, 'id' : 'my_id', 'type' : 'Feature', 'properties' : { 'key' : 'value'  , 'type' : 'object' } })

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_RECORD_JSONSTR)
        self.client.places.http = mockhttp
        res = self.client.places._request("http://thing", 'POST')[1]
        self.failUnlessEqual(res, EXAMPLE_RECORD_JSONSTR)

    def test_update_feature(self):
        handle = 'SG_abcdefghijklmnopqrstuv'
        rec = Feature((D('11.03'), D('10.04')), simplegeohandle=handle)

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, {'token': "this is your polling token"})
        self.client.places.http = mockhttp

        res = self.client.places.update_feature(rec)
        self.failUnless(isinstance(res, dict), res)
        self.failUnless(res.has_key('token'), res)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'POST')
        bodyjson = mockhttp.method_calls[0][2]['body']
        self.failUnless(isinstance(bodyjson, basestring), (repr(bodyjson), type(bodyjson)))
        # If it decoded as valid json then check for some expected fields
        bodyobj = json.loads(bodyjson)
        self.failUnless(bodyobj.get('geometry').has_key('coordinates'), bodyobj)
        self.failUnless(bodyobj.get('geometry').has_key('type'), bodyobj)
        self.failUnlessEqual(bodyobj.get('geometry')['type'], 'Point')

    def test_delete_feature(self):
        handle = 'SG_abcdefghijklmnopqrstuv'

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, "whatever the response body is")
        self.client.places.http = mockhttp

        res = self.client.places.delete_feature(handle)
        self.failUnlessEqual(res, "whatever the response body is")

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'DELETE')

    def test_search_nonascii(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': u"B❤b's House Of Monkeys", 'category': u"m❤nkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': u"M❤nkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        self.failUnlessRaises(AssertionError, self.client.places.search, -91, 100)
        self.failUnlessRaises(AssertionError, self.client.places.search, -81, 361)

        lat = D('11.03')
        lon = D('10.04')
        res = self.client.places.search(lat, lon, query=u'm❤nkey', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        urlused = mockhttp.method_calls[0][1][0]
        urlused = urllib.unquote(urlused).decode('utf-8')
        self.assertEqual(urlused, u'http://api.simplegeo.com:80/%s/places/%s,%s.json?q=m❤nkey&category=animal' % (API_VERSION, lat, lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_search(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        self.failUnlessRaises(AssertionError, self.client.places.search, -91, 100)
        self.failUnlessRaises(AssertionError, self.client.places.search, -81, 361)

        lat = D('11.03')
        lon = D('10.04')
        res = self.client.places.search(lat, lon, query='monkeys', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/%s,%s.json?q=monkeys&category=animal' % (API_VERSION, lat, lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_search_by_ip_nonascii(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': u"Bob's House Of M❤nkeys", 'category': u"m❤nkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': u"M❤nkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        self.failUnlessRaises(AssertionError, self.client.places.search_by_ip, 'this is not an IP address at all, silly')
        self.failUnlessRaises(AssertionError, self.client.places.search_by_ip, -81, 181) # Someone accidentally passed lat, lon to search_by_ip().

        ipaddr = '192.0.32.10'

        res = self.client.places.search_by_ip(ipaddr, query=u'm❤nkey', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        urlused = mockhttp.method_calls[0][1][0]
        urlused = urllib.unquote(urlused).decode('utf-8')
        self.assertEqual(urlused, u'http://api.simplegeo.com:80/%s/places/%s.json?q=m❤nkey&category=animal' % (API_VERSION, ipaddr))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

        res = self.client.places.search_by_ip(ipaddr, query=u'm❤nkey', category=u'❤nimal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[-1][0], 'request')
        urlused = mockhttp.method_calls[-1][1][0]
        urlused = urllib.unquote(urlused).decode('utf-8')
        self.assertEqual(urlused, u'http://api.simplegeo.com:80/%s/places/%s.json?q=m❤nkey&category=❤nimal' % (API_VERSION, ipaddr))
        self.assertEqual(mockhttp.method_calls[-1][1][1], 'GET')

    def test_search_by_ip(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        self.failUnlessRaises(AssertionError, self.client.places.search_by_ip, 'this is not an IP address at all, silly')
        self.failUnlessRaises(AssertionError, self.client.places.search_by_ip, -81, 181) # Someone accidentally passed lat, lon to search_by_ip().

        ipaddr = '192.0.32.10'

        res = self.client.places.search_by_ip(ipaddr, query='monkeys', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/%s.json?q=monkeys&category=animal' % (API_VERSION, ipaddr))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_search_by_my_ip_nonascii(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        ipaddr = '192.0.32.10'
        self.failUnlessRaises(AssertionError, self.client.places.search_by_my_ip, ipaddr) # Someone accidentally passed an ip addr to search_by_my_ip().

        res = self.client.places.search_by_my_ip(query='monk❥y', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[-1][0], 'request')
        urlused = mockhttp.method_calls[-1][1][0]
        urlused = urllib.unquote(urlused).decode('utf-8')
        self.assertEqual(urlused, u'http://api.simplegeo.com:80/%s/places/ip.json?q=monk❥y&category=animal' % (API_VERSION,))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

        res = self.client.places.search_by_my_ip(query='monk❥y', category='anim❥l')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[-1][0], 'request')
        urlused = mockhttp.method_calls[-1][1][0]
        urlused = urllib.unquote(urlused).decode('utf-8')
        self.assertEqual(urlused, u'http://api.simplegeo.com:80/%s/places/ip.json?q=monk❥y&category=anim❥l' % (API_VERSION,))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_search_by_my_ip(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        ipaddr = '192.0.32.10'
        self.failUnlessRaises(AssertionError, self.client.places.search_by_my_ip, ipaddr) # Someone accidentally passed an ip addr to search_by_my_ip().

        res = self.client.places.search_by_my_ip(query='monkeys', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/ip.json?q=monkeys&category=animal' % (API_VERSION,))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_search_by_address_nonascii(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        lat = D('11.03')
        lon = D('10.04')
        self.failUnlessRaises(AssertionError, self.client.places.search_by_address, lat, lon) # Someone accidentally passed a lat,lon to search_by_address().

        addr = u'41 Decatur St, San Francisc❦, CA'
        res = self.client.places.search_by_address(addr, query='monkeys', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[-1][0], 'request')
        urlused = mockhttp.method_calls[-1][1][0]
        cod = urllib.quote_plus(addr.encode('utf-8'))
        self.assertEqual(urlused, 'http://api.simplegeo.com:80/%s/places/address.json?q=monkeys&category=animal&address=%s' % (API_VERSION, cod,))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

        res = self.client.places.search_by_address(addr, query=u'monke❦s', category=u'ani❦al')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[-1][0], 'request')
        urlused = mockhttp.method_calls[-1][1][0]

        quargs = {'q': u'monke❦s', 'category': u'ani❦al', 'address': addr}
        equargs = dict( (k, v.encode('utf-8')) for k, v in quargs.iteritems() )
        s2quargs = urllib.urlencode(equargs)
        self.assertEqual(urlused, 'http://api.simplegeo.com:80/%s/places/address.json?%s' % (API_VERSION, s2quargs))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_search_by_address(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        lat = D('11.03')
        lon = D('10.04')
        self.failUnlessRaises(AssertionError, self.client.places.search_by_address, lat, lon) # Someone accidentally passed a lat,lon to search_by_address().

        addr = '41 Decatur St, San Francisco, CA'
        res = self.client.places.search_by_address(addr, query='monkeys', category='animal')
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/address.json?q=monkeys&category=animal&address=%s' % (API_VERSION, urllib.quote_plus(addr)))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_radius_search(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': []}))
        self.client.places.http = mockhttp

        lat = D('11.03')
        lon = D('10.04')
        radius = D('0.01')
        res = self.client.places.search(lat, lon, radius=radius)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 0)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/%s,%s.json?radius=%s' % (API_VERSION, lat, lon, radius))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_radius_search_by_ip(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': []}))
        self.client.places.http = mockhttp

        ipaddr = '192.0.32.10'
        radius = D('0.01')
        res = self.client.places.search_by_ip(ipaddr, radius=radius)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 0)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/%s.json?radius=%s' % (API_VERSION, ipaddr, radius))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_radius_search_by_my_ip(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': []}))
        self.client.places.http = mockhttp

        ipaddr = '192.0.32.10'
        radius = D('0.01')
        self.failUnlessRaises((AssertionError, TypeError), self.client.places.search_by_my_ip, ipaddr, radius=radius) # Someone accidentally passed an ip addr to search_by_my_ip().

        res = self.client.places.search_by_my_ip(radius=radius)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 0)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/ip.json?radius=%s' % (API_VERSION, radius))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_radius_search_by_address(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': []}))
        self.client.places.http = mockhttp

        lat = D('11.03')
        lon = D('10.04')
        radius = D('0.01')
        self.failUnlessRaises((AssertionError, TypeError), self.client.places.search_by_address, lat, lon, radius=radius) # Someone accidentally passed a lat,lon to search_by_address().

        addr = '41 Decatur St, San Francisco, CA'
        res = self.client.places.search_by_address(addr, radius=radius)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 0)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/address.json?radius=%s&address=%s' % (API_VERSION, radius, urllib.quote_plus(addr)))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_no_terms_search(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        lat = D('11.03')
        lon = D('10.04')
        res = self.client.places.search(lat, lon)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/%s,%s.json' % (API_VERSION, lat, lon))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_no_terms_search_by_ip(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        ipaddr = '192.0.32.10'
        res = self.client.places.search_by_ip(ipaddr)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/%s.json' % (API_VERSION, ipaddr))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_no_terms_search_by_my_ip(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        ipaddr = '192.0.32.10'
        self.failUnlessRaises(AssertionError, self.client.places.search_by_my_ip, ipaddr) # Someone accidentally passed an ip addr to search_by_my_ip().
        res = self.client.places.search_by_my_ip()
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/ip.json' % (API_VERSION,))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_no_terms_search_by_address(self):
        rec1 = Feature((D('11.03'), D('10.04')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Bob's House Of Monkeys", 'category': "monkey dealership"})
        rec2 = Feature((D('11.03'), D('10.05')), simplegeohandle='SG_abcdefghijkmlnopqrstuv', properties={'name': "Monkey Food 'R' Us", 'category': "pet food store"})

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, json.dumps({'type': "FeatureColllection", 'features': [rec1.to_dict(), rec2.to_dict()]}))
        self.client.places.http = mockhttp

        lat = D('11.03')
        lon = D('10.04')
        self.failUnlessRaises(AssertionError, self.client.places.search_by_address, lat, lon) # Someone accidentally passed a lat,lon search_by_address().

        addr = '41 Decatur St, San Francisco, CA'
        res = self.client.places.search_by_address(addr)
        self.failUnless(isinstance(res, (list, tuple)), (repr(res), type(res)))
        self.failUnlessEqual(len(res), 2)
        self.failUnless(all(isinstance(f, Feature) for f in res))
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/places/address.json?address=%s' % (API_VERSION, urllib.quote_plus(addr)))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_get_feature_bad_json(self):
        handle = 'SG_abcdefghijklmnopqrstuv'

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, 'some crap')
        self.client.places.http = mockhttp

        try:
            self.client.places.get_feature(handle)
        except DecodeError, e:
            self.failUnlessEqual(e.code,None,repr(e.code))
            self.failUnless("Could not decode JSON" in e.msg, repr(e.msg))
            repr(e)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_APIError(self):
        e = APIError(500, 'whee', {'status': "500"})
        self.failUnlessEqual(e.code, 500)
        self.failUnlessEqual(e.msg, 'whee')
        repr(e)
        str(e)

    def test_get_places_error(self):
        handle = 'SG_abcdefghijklmnopqrstuv'

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '500', 'content-type': 'application/json', }, '{"message": "help my web server is confuzzled"}')
        self.client.places.http = mockhttp

        try:
            self.client.places.get_feature(handle)
        except APIError, e:
            self.failUnlessEqual(e.code, 500, repr(e.code))
            self.failUnlessEqual(e.msg, '{"message": "help my web server is confuzzled"}', (type(e.msg), repr(e.msg)))

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')
