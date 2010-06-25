import time
import random
import unittest
import simplejson as json
import geohash
from simplegeo import Client, Record, APIError

MY_OAUTH_KEY = 'MY_OAUTH_KEY'
MY_OAUTH_SECRET = 'MY_OAUTH_SECRET'
TESTING_LAYER = 'testlayer'

API_VERSION = '0.1'
API_HOST = 'api.simplegeo.com'
API_PORT = 80

TESTING_GEOHASH = '9q8zn1'
TESTING_LAT = '37.7481624945'
TESTING_LON = '-122.433287165'
TESTING_LAT_NON_US = '48.8566667'
TESTING_LON_NON_US = '2.3509871'
RECORD_TYPES = ['person', 'place', 'object']

class ClientTest(unittest.TestCase):

    def setUp(self):
        self.client = Client(MY_OAUTH_KEY, MY_OAUTH_SECRET, API_VERSION, API_HOST, API_PORT)

    def _record(self):
        """ Generate a record in San Francisco. """
        top_left = [37.801646236899785, -122.47833251953125]
        bottom_right = [37.747371884118664, -122.3931884765625]

        record = Record(
            layer=TESTING_LAYER,
            id=str(int(time.time() * 1000000)),
            lat=str(random.uniform(top_left[0], bottom_right[0])),
            lon=str(random.uniform(top_left[1], bottom_right[1])),
            type=RECORD_TYPES[random.randint(0, 2)]
        )
        return record

    def test_multi_record_post(self):
        post_records = [self._record() for i in range(10)]
        self.addRecordsAndSleep(TESTING_LAYER, post_records)

        get_records = self.client.get_records(TESTING_LAYER,
                        [record.id for record in post_records])
        self.assertEquals(len(get_records), len(post_records))

        post_record_ids = [post_record.id for post_record in post_records]
        for get_record in get_records:
            self.assertTrue(get_record['id'] in post_record_ids)

    def test_too_many_records(self):
        record_limit = 100
        records = []
        for i in xrange(record_limit + 1):
            records.append(self._record())

        self.assertRaises(APIError, self.client.add_records, TESTING_LAYER,
                          records)

    def test_add_record(self):
        record = self._record()
        self.client.add_record(record)
        result = self.client.get_record(record.layer, record.id)
        self.assertPointIsRecord(result, record)

    def test_add_update_delete_record(self):
        record = self._record()
        self.addRecordAndSleep(record)
        result = self.client.get_record(record.layer, record.id)
        self.assertPointIsRecord(result, record)
        updated_record = self._record()
        updated_record.id = record.id
        self.addRecordAndSleep(updated_record)
        updated_result = self.client.get_record(record.layer, record.id)
        self.assertPointIsRecord(updated_result, updated_record)
        self.client.delete_record(record.layer, record.id)
        self.assertRaises(APIError, self.client.get_record, record.layer, record.id)
        self.assertRaises(APIError, self.client.get_record, updated_record.layer, updated_record.id)

    def test_record_history(self):
        post_records = [self._record() for i in range(10)]
        for record in post_records:
            record.id = post_records[0].id
            record.created = int(time.time())
            self.client.add_record(record)
            time.sleep(1)
        history = self.client.get_history(TESTING_LAYER, post_records[0].id)
        points = history.get('geometries')
        self.assertEquals(len(points), 10)
        post_records.reverse()
        count = 0
        for point in points:
            self.assertEquals(str(point.get('coordinates')[0]), post_records[count].lon)
            self.assertEquals(str(point.get('coordinates')[1]), post_records[count].lat)
            count += 1

    def test_nearby_geohash_search(self):
        limit = 5
        nearby_result = self.client.get_nearby_geohash(TESTING_LAYER, TESTING_GEOHASH, limit=limit)
        features = nearby_result.get('features')
        self.assertTrue(len(features) <= limit)
        bounding_box = geohash.bbox(TESTING_GEOHASH)
        for feature in features:
            self.assertTrue(bounding_box.get('s') <= feature.get('geometry').get('coordinates')[1] <= bounding_box.get('n'))
            self.assertTrue(bounding_box.get('e') >= feature.get('geometry').get('coordinates')[0] >= bounding_box.get('w'))

    def test_nearby_lat_lon_search(self):
        limit = 5
        radius = 1.5
        nearby_result = self.client.get_nearby(TESTING_LAYER, TESTING_LAT, TESTING_LON, limit=limit, radius=radius)
        features = nearby_result.get('features')
        self.assertTrue(len(features) <= limit)
        for feature in features:
            self.assertTrue(float(feature.get('distance')) <= radius*1000)

    def test_nearby_address_search(self):
        self.assertTrue(self.client.get_nearby_address(TESTING_LAT, TESTING_LON))
        self.assertRaises(APIError, self.client.get_nearby_address, TESTING_LAT_NON_US, TESTING_LON_NON_US)

    # Utility functions

    def assertPointIsRecord(self, point, record):
        self.assertEquals(point['type'], 'Feature')
        self.assertEquals(point['id'], record.id)
        self.assertEquals(point['layerLink']['href'],
                          'http://api.simplegeo.com/0.1/layer/%s.json'
                            % record.layer)
        self.assertEquals(point['selfLink']['href'],
                          'http://api.simplegeo.com/0.1/records/%s/%s.json'
                            % (record.layer, record.id))
        self.assertEquals(point['created'], record.created)
        self.assertEquals(point['properties']['type'], record.type)
        self.assertEquals(point['geometry']['type'], 'Point')
        self.assertEquals(point['geometry']['coordinates'][0], float(record.lon))
        self.assertEquals(point['geometry']['coordinates'][1], float(record.lat))

    def addRecordAndSleep(self, record):
        self.client.add_record(record)
        time.sleep(5)

    def addRecordsAndSleep(self, layer, records):
        self.client.add_records(layer, records)
        time.sleep(5)

if __name__ == '__main__':
    unittest.main()
