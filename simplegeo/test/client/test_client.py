import unittest
from decimal import Decimal as D

from pyutil import jsonutil as json
import mock

from simplegeo import Client
from simplegeo.models import Feature
from simplegeo.util import APIError, DecodeError, is_valid_lat, is_valid_lon, is_valid_ip, to_unicode

MY_OAUTH_KEY = 'MY_OAUTH_KEY'
MY_OAUTH_SECRET = 'MY_SECRET_KEY'
TESTING_LAYER = 'TESTING_LAYER'

API_VERSION = '1.0'
API_HOST = 'api.simplegeo.com'
API_PORT = 80

class ReallyEqualMixin:
    def failUnlessReallyEqual(self, a, b, msg='', *args, **kwargs):
        self.failUnlessEqual(a, b, msg, *args, **kwargs)
        self.failUnlessEqual(type(a), type(b), msg="a :: %r, b :: %r, %r" % (a, b, msg), *args, **kwargs)

class ToUnicodeTest(unittest.TestCase, ReallyEqualMixin):
    def test_to_unicode(self):
        self.failUnlessReallyEqual(to_unicode('x'), u'x')
        self.failUnlessReallyEqual(to_unicode(u'x'), u'x')
        self.failUnlessReallyEqual(to_unicode('\xe2\x9d\xa4'), u'\u2764')

class LatLonValidationTest(unittest.TestCase):

    def test_is_valid_lon(self):
        self.failUnless(is_valid_lon(180, strict=True))
        self.failUnless(is_valid_lon(180.0, strict=True))
        self.failUnless(is_valid_lon(D('180.0'), strict=True))
        self.failUnless(is_valid_lon(-180, strict=True))
        self.failUnless(is_valid_lon(-180.0, strict=True))
        self.failUnless(is_valid_lon(D('-180.0'), strict=True))

        self.failIf(is_valid_lon(180.0002, strict=True))
        self.failIf(is_valid_lon(D('180.0002'), strict=True))
        self.failIf(is_valid_lon(-180.0002, strict=True))
        self.failIf(is_valid_lon(D('-180.0002'), strict=True))

        self.failUnless(is_valid_lon(180.0002, strict=False))
        self.failUnless(is_valid_lon(D('180.0002'), strict=False))
        self.failUnless(is_valid_lon(-180.0002, strict=False))
        self.failUnless(is_valid_lon(D('-180.0002'), strict=False))

        self.failIf(is_valid_lon(360.0002, strict=False))
        self.failIf(is_valid_lon(D('360.0002'), strict=False))
        self.failIf(is_valid_lon(-360.0002, strict=False))
        self.failIf(is_valid_lon(D('-360.0002'), strict=False))

    def test_is_valid_lat(self):
        self.failUnless(is_valid_lat(90))
        self.failUnless(is_valid_lat(90.0))
        self.failUnless(is_valid_lat(D('90.0')))
        self.failUnless(is_valid_lat(-90))
        self.failUnless(is_valid_lat(-90.0))
        self.failUnless(is_valid_lat(D('-90.0')))

        self.failIf(is_valid_lat(90.0002))
        self.failIf(is_valid_lat(D('90.0002')))
        self.failIf(is_valid_lat(-90.0002))
        self.failIf(is_valid_lat(D('-90.0002')))

class DecodeErrorTest(unittest.TestCase):
    def test_repr(self):
        body = 'this is not json'
        try:
            json.loads('this is not json')
        except ValueError, le:
            e = DecodeError(body, le)
        else:
            self.fail("We were supposed to get an exception from json.loads().")

        self.failUnless("Could not decode JSON" in e.msg, repr(e.msg))
        self.failUnless('JSONDecodeError' in repr(e), repr(e))

class ClientTest(unittest.TestCase):
    def setUp(self):
        self.client = Client(MY_OAUTH_KEY, MY_OAUTH_SECRET, host=API_HOST, port=API_PORT)
        self.query_lat = D('37.8016')
        self.query_lon = D('-122.4783')

    def test_is_valid_ip(self):
        self.failUnless(is_valid_ip('192.0.32.10'))
        self.failIf(is_valid_ip('i am not an ip address at all'))

    def test_wrong_endpoint(self):
        self.assertRaises(Exception, self.client._endpoint, 'wrongwrong')

    def test_missing_argument(self):
        self.assertRaises(Exception, self.client._endpoint, 'feature')

    def test_get_feature_useful_validation_error_message(self):
        c = Client('whatever', 'whatever')
        try:
            c.get_feature('wrong thing')
        except TypeError, e:
            self.failUnless(str(e).startswith('simplegeohandle is required to match '), str(e))
        else:
            self.fail('Should have raised exception.')

    def test_get_most_recent_http_headers(self):
        h = self.client.get_most_recent_http_headers()
        self.failUnlessEqual(h, None)

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', 'thingie': "just to see if you're listening"}, EXAMPLE_POINT_BODY)
        self.client.http = mockhttp

        self.client.get_feature("SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970")
        h = self.client.get_most_recent_http_headers()
        self.failUnlessEqual(h, {'status': '200', 'content-type': 'application/json', 'thingie': "just to see if you're listening"})

    def test_get_point_feature(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', 'thingie': "just to see if you're listening"}, EXAMPLE_POINT_BODY)
        self.client.http = mockhttp

        res = self.client.get_feature("SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970")
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, "SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970"))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')
        # the code under test is required to have json-decoded this before handing it back
        self.failUnless(isinstance(res, Feature), (repr(res), type(res)))

    def test_get_polygon_feature(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY)
        self.client.http = mockhttp

        res = self.client.get_feature("SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970")
        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, "SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970"))

        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')
        # the code under test is required to have json-decoded this before handing it back
        self.failUnless(isinstance(res, Feature), (repr(res), type(res)))

    def test_get_feature_bad_json(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_BODY + 'some crap')
        self.client.http = mockhttp

        try:
            self.client.get_feature("SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970")
        except DecodeError, e:
            self.failUnlessEqual(e.code, None, repr(e.code))

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, "SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970"))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_dont_json_decode_results(self):
        """ _request() is required to return the exact string that the HTTP
        server sent to it -- no transforming it, such as by json-decoding. """

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, '{ "Hello": "I am a string. \xe2\x9d\xa4" }'.decode('utf-8'))
        self.client.http = mockhttp
        res = self.client._request("http://thing", 'POST')[1]
        self.failUnlessEqual(res, '{ "Hello": "I am a string. \xe2\x9d\xa4" }'.decode('utf-8'))

    def test_dont_Recordify_results(self):
        """ _request() is required to return the exact string that the HTTP
        server sent to it -- no transforming it, such as by json-decoding and
        then constructing a Record. """

        EXAMPLE_RECORD_JSONSTR=json.dumps({ 'geometry' : { 'type' : 'Point', 'coordinates' : [D('10.0'), D('11.0')] }, 'id' : 'my_id', 'type' : 'Feature', 'properties' : { 'key' : 'value'  , 'type' : 'object' } })

        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '200', 'content-type': 'application/json', }, EXAMPLE_RECORD_JSONSTR)
        self.client.http = mockhttp
        res = self.client._request("http://thing", 'POST')[1]
        self.failUnlessEqual(res, EXAMPLE_RECORD_JSONSTR)

    def test_get_feature_error(self):
        mockhttp = mock.Mock()
        mockhttp.request.return_value = ({'status': '500', 'content-type': 'application/json', }, '{"message": "help my web server is confuzzled"}')
        self.client.http = mockhttp

        try:
            self.client.get_feature("SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970")
        except APIError, e:
            self.failUnlessEqual(e.code, 500, repr(e.code))
            self.failUnlessEqual(e.msg, '{"message": "help my web server is confuzzled"}', (type(e.msg), repr(e.msg)))

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s.json' % (API_VERSION, "SG_4bgzicKFmP89tQFGLGZYy0_34.714646_-86.584970"))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

    def test_APIError(self):
        e = APIError(500, 'whee', {'status': "500"})
        self.failUnlessEqual(e.code, 500)
        self.failUnlessEqual(e.msg, 'whee')
        repr(e)
        str(e)

EXAMPLE_POINT_BODY="""
{"geometry":{"type":"Point","coordinates":[-105.048054,40.005274]},"type":"Feature","id":"SG_6sRJczWZHdzNj4qSeRzpzz_40.005274_-105.048054@1291669259","properties":{"province":"CO","city":"Erie","name":"CMD Colorado Inc","tags":["sandwich"],"country":"US","phone":"+1 303 664 9448","address":"305 Baron Ct","owner":"simplegeo","classifiers":[{"category":"Restaurants","type":"Food & Drink","subcategory":""}],"postcode":"80516"}}
"""

EXAMPLE_BODY="""
{"geometry":{"type":"Polygon","coordinates":[[[-86.3672637,33.4041157],[-86.3676356,33.4039745],[-86.3681259,33.40365],[-86.3685992,33.4034242],[-86.3690556,33.4031137],[-86.3695121,33.4027609],[-86.3700361,33.4024363],[-86.3705601,33.4021258],[-86.3710166,33.4018012],[-86.3715575,33.4014061],[-86.3720647,33.4008557],[-86.3724366,33.4005311],[-86.3730621,33.3998395],[-86.3733156,33.3992891],[-86.3735523,33.3987811],[-86.3737383,33.3983153],[-86.3739073,33.3978355],[-86.374144,33.3971016],[-86.3741609,33.3968758],[-86.3733494,33.3976943],[-86.3729606,33.3980189],[-86.3725211,33.3984141],[-86.3718111,33.3990069],[-86.3713378,33.399402],[-86.370949,33.3997266],[-86.3705094,33.3999948],[-86.3701206,33.4003899],[-86.3697487,33.4007287],[-86.369157,33.4012791],[-86.3687682,33.401646],[-86.3684132,33.4019847],[-86.368092,33.4023798],[-86.3676694,33.4028738],[-86.3674835,33.4033113],[-86.3672975,33.4037487],[-86.3672637,33.4041157],[-86.3672637,33.4041157]]]},"type":"Feature","properties":{"category":"Island","license":"http://creativecommons.org/licenses/by-sa/2.0/","handle":"SG_4b10i9vCyPnKAYiYBLKZN7_33.400800_-86.370802","subcategory":"","name":"Elliott Island","attribution":"(c) OpenStreetMap (http://openstreetmap.org/) and contributors CC-BY-SA (http://creativecommons.org/licenses/by-sa/2.0/)","type":"Physical Feature","abbr":""},"id":"SG_4b10i9vCyPnKAYiYBLKZN7"}
"""

class TestAnnotations(unittest.TestCase):

    def setUp(self):
        self.client = Client(MY_OAUTH_KEY, MY_OAUTH_SECRET, host=API_HOST, port=API_PORT)
        self.handle = 'SG_4H2GqJDZrc0ZAjKGR8qM4D'

    def test_get_annotations(self):
        mockhttp = mock.Mock()
        headers = {'status': '200', 'content-type': 'application/json'}
        mockhttp.request.return_value = (headers, json.dumps(EXAMPLE_ANNOTATIONS_RESPONSE))
        self.client.http = mockhttp

        res = self.client.get_annotations(self.handle)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s/annotations.json' % (API_VERSION, self.handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'GET')

        # Make sure client returns a dict.
        self.failUnless(isinstance(res, dict))

    def test_get_annotations_bad_handle(self):
        try:
            self.client.get_annotations('bad_handle')
        except TypeError, e:
            self.failUnless(str(e).startswith('simplegeohandle is required to match the regex'))
        else:
            self.fail('Should have raised exception.')

    def test_annotate(self):
        mockhttp = mock.Mock()
        headers = {'status': '200', 'content-type': 'application/json'}
        mockhttp.request.return_value = (headers, json.dumps(EXAMPLE_ANNOTATE_RESPONSE))
        self.client.http = mockhttp

        res = self.client.annotate(self.handle, EXAMPLE_ANNOTATIONS, True)

        self.assertEqual(mockhttp.method_calls[0][0], 'request')
        self.assertEqual(mockhttp.method_calls[0][1][0], 'http://api.simplegeo.com:80/%s/features/%s/annotations.json' % (API_VERSION, self.handle))
        self.assertEqual(mockhttp.method_calls[0][1][1], 'POST')

        # Make sure client returns a dict.
        self.failUnless(isinstance(res, dict))

    def test_annotate_bad_annotations_type(self):
        annotations = 'not_a_dict'
        try:
            self.client.annotate(self.handle, annotations, True)
        except TypeError, e:
            self.failUnless(str(e) == 'annotations must be of type dict')
        else:
            self.fail('Should have raised exception.')

    def test_annotate_empty_annotations_dict(self):
        annotations = {}
        try:
            self.client.annotate(self.handle, annotations, True)
        except ValueError, e:
            self.failUnless(str(e) == 'annotations dict is empty')
        else:
            self.fail('Should have raised exception.')

    def test_annotate_empty_annotation_type_dict(self):
        annotations = {
            'annotation_type_1': {
                'foo': 'bar'},
            'annotation_type_2': {
                }
            }
        try:
            self.client.annotate(self.handle, annotations, True)
        except ValueError, e:
            self.failUnless(str(e) == 'annotation type "annotation_type_2" is empty')
        else:
            self.fail('Should have raised exception.')

    def test_annotate_private_type(self):
        try:
            self.client.annotate(self.handle, EXAMPLE_ANNOTATIONS, 'not_a_bool')
        except TypeError, e:
            self.failUnless(str(e) == 'private must be of type bool')
        else:
            self.fail('Should have raised exception.')


EXAMPLE_ANNOTATIONS_RESPONSE = {
    'private': {
        'venue': {
            'profitable': 'yes',
            'owner': 'John Doe'},
        'building': {
            'condition': 'poor'}
        },
    'public': {
        'venue': {
            'capacity': '28,037',
            'activity': 'sports'},
        'building': {
            'size': 'extra small',
            'material': 'wood',
            'ground': 'grass'}
        }
    }

EXAMPLE_ANNOTATIONS = {
    'venue': {
        'profitable': 'yes',
        'owner': 'John Doe'},
    'building': {
        'condition': 'poor'}
    }

EXAMPLE_ANNOTATE_RESPONSE = {'status': 'success'}
