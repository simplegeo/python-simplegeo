import time
import random
import unittest
import simplejson as json
import geohash
import random
from simplegeo import Client, Record, APIError

MY_OAUTH_KEY = 'MY_OAUTH_KEY'
MY_OAUTH_SECRET = 'MY_SECRET_KEY'
TESTING_LAYER = 'TESTING_LAYER'

if MY_OAUTH_KEY == 'MY_OAUTH_KEY' or \
    MY_OAUTH_SECRET == 'MY_SERCRET_KEY' or \
    TESTING_LAYER == 'TESTING_LAYER':
    raise Exception('Please provide the proper credentials.')

API_VERSION = '0.1'
API_HOST = 'api.simplegeo.com'
API_PORT = 80


TESTING_LAT = '37.7481624945'
TESTING_LON = '-122.433287165'
TESTING_GEOHASH = geohash.encode(float(TESTING_LAT), float(TESTING_LON))

TESTING_LAT_NON_US = '48.8566667'
TESTING_LON_NON_US = '2.3509871'
RECORD_TYPES = ['person', 'place', 'object']
TESTING_BOUNDS = [-122.43409, 37.747296999999996, -122.424768, 37.751841999999996]

class ClientTest(unittest.TestCase):

    def tearDown(self):
        for record in self.created_records:
            try:
                self.client.delete_record(record.layer, record.id)
            except APIError, e:
                # If we get a 404, then our job is done.
                pass

    def setUp(self):
        self.client = Client(MY_OAUTH_KEY, MY_OAUTH_SECRET, API_VERSION, API_HOST, API_PORT)
        self.created_records = []

    def _record(self):
        """ Generate a record in San Francisco. """
        top_left = [37.801646236899785, -122.47833251953125]
        bottom_right = [37.747371884118664, -122.3931884765625]

        record = Record(
            layer=TESTING_LAYER,
            id=str(int(random.random() * 1000000)),
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
        for i in range(record_limit + 1):
            records.append(self._record())

        self.assertRaises(APIError, self.client.add_records, TESTING_LAYER,
                          records)

    def test_add_record(self):
        record = self._record()
        self.addRecordAndSleep(record)
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
        time.sleep(5)
        self.assertRaises(APIError, self.client.get_record, record.layer, record.id)
        self.assertRaises(APIError, self.client.get_record, updated_record.layer, updated_record.id)

    def test_record_history(self):
        post_records = [self._record() for i in range(10)]
        current_time = int(time.time())
        for record in post_records:
            record.id = post_records[0].id
            record.created = current_time
            current_time -= 1

        self.addRecordsAndSleep(TESTING_LAYER, post_records)

        history = self.client.get_history(TESTING_LAYER, post_records[0].id)
        points = history.get('geometries')
        self.assertEquals(len(points), 10)

        count = 0
        for point in points:
            self.assertEquals(str(point.get('coordinates')[0]), post_records[count].lon)
            self.assertEquals(str(point.get('coordinates')[1]), post_records[count].lat)
            count += 1

    def test_nearby_geohash_search(self):
        limit = 5
        records = []
        for i in range(limit):
            record = self._record()
            record.lat = float(TESTING_LAT) + (i / 10000000)
            record.lon = float(TESTING_LON) - (i / 10000000)
            records.append(record)

        self.addRecordsAndSleep(TESTING_LAYER, records)

        nearby_result = self.client.get_nearby_geohash(TESTING_LAYER, TESTING_GEOHASH, limit=limit)
        features = nearby_result.get('features')
        self.assertTrue(len(features) <= limit)
        bounding_box = geohash.bbox(TESTING_GEOHASH)
        for feature in features:
            self.assertTrue(bounding_box.get('s') <= feature.get('geometry').get('coordinates')[1] <= bounding_box.get('n'))
            self.assertTrue(bounding_box.get('e') >= feature.get('geometry').get('coordinates')[0] >= bounding_box.get('w'))

    def test_nearby_lat_lon_search(self):
        limit = 5
        records = []
        for i in range(limit):
            record = self._record()
            record.lat = float(TESTING_LAT) + (i / 10000000)
            record.lon = float(TESTING_LON) - (i / 10000000)
            records.append(record)

        self.addRecordsAndSleep(TESTING_LAYER, records)

        radius = 1.5
        nearby_result = self.client.get_nearby(TESTING_LAYER, TESTING_LAT, TESTING_LON, limit=limit, radius=radius)
        features = nearby_result.get('features')
        self.assertTrue(len(features) <= limit)
        for feature in features:
            self.assertTrue(float(feature.get('distance')) <= radius*1000)

    def test_nearby_address_search(self):
        address_result = self.client.get_nearby_address(TESTING_LAT, TESTING_LON)
        self.assertAddressEquals(address_result)
        self.assertRaises(APIError, self.client.get_nearby_address, TESTING_LAT_NON_US, TESTING_LON_NON_US)

    def test_contains_and_boundary(self):
        contains_result = self.client.get_contains(TESTING_LAT, TESTING_LON)
        for feature in contains_result:
            self.assertTrue(feature.get('bounds')[0] <= float(TESTING_LON) <= feature.get('bounds')[2])
            self.assertTrue(feature.get('bounds')[1] <= float(TESTING_LAT) <= feature.get('bounds')[3])
            boundary_dict = self.client.get_boundary(feature.get('id'))
            self.assertTrue(feature.get('id'), boundary_dict.get('id'))

    def test_overlaps(self):
        limit = 1
        overlaps_result = self.client.get_overlaps(TESTING_BOUNDS[1], TESTING_BOUNDS[0], TESTING_BOUNDS[3], TESTING_BOUNDS[2], limit=limit)
        self.assertOverlapEquals(overlaps_result[0])

    def test_density(self):
        density_results = self.client.get_density(TESTING_LAT, TESTING_LON, 'mon')
        features = density_results.get('features')
        self.assertEquals(len(features), 24)
        for feature in features:
            self.assertEquals(feature.get('properties').get('dayname'), 'mon')
            self.assertCorrectCoordinates(feature.get('geometry').get('coordinates'))

    def test_hour_density(self):
        density_results = self.client.get_density(TESTING_LAT, TESTING_LON, 'mon', 0)
        self.assertEqual(density_results.get('properties').get('dayname'), 'mon')
        self.assertEqual(density_results.get('properties').get('hour'), 0)
        self.assertCorrectCoordinates(density_results.get('geometry').get('coordinates'))

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
        self.created_records.append(record)
        time.sleep(5)

    def addRecordsAndSleep(self, layer, records):
        self.client.add_records(layer, records)
        self.created_records += records
        time.sleep(5)

    def assertAddressEquals(self, record):
        self.assertEquals(record.get('properties').get('state_name'), 'California')
        self.assertEquals(record.get('properties').get('street_number'), '4176')
        self.assertEquals(record.get('properties').get('country'), 'US')
        self.assertEquals(record.get('properties').get('street'), '26th St')
        self.assertEquals(record.get('properties').get('postal_code'), '94131')
        self.assertEquals(record.get('properties').get('county_name'), 'San Francisco')
        self.assertEquals(record.get('properties').get('county_code'), '075')
        self.assertEquals(record.get('properties').get('state_code'), 'CA')
        self.assertEquals(record.get('properties').get('place_name'), 'San Francisco')

    def assertOverlapEquals(self, record):
        self.assertEquals(record.get('name'), '06075021500')
        self.assertEquals(record.get('type'), 'Census Tract')
        self.assertEquals(record.get('bounds')[0], -122.431477)
        self.assertEquals(record.get('bounds')[1], 37.741833)
        self.assertEquals(record.get('bounds')[2], -122.421328)
        self.assertEquals(record.get('bounds')[3], 37.748123999999997)
        self.assertEquals(record.get('abbr'), '')
        self.assertEquals(record.get('id'), 'Census_Tract:06075021500:9q8ywp')

    def assertCorrectCoordinates(self, coordinate_list):
        self.assertEquals(coordinate_list[0][0], 37.748046875)
        self.assertEquals(coordinate_list[0][1], -122.43359375)
        self.assertEquals(coordinate_list[1][0], 37.7490234375)
        self.assertEquals(coordinate_list[1][1], -122.43359375)
        self.assertEquals(coordinate_list[2][0], 37.7490234375)
        self.assertEquals(coordinate_list[2][1], -122.4326171875)
        self.assertEquals(coordinate_list[3][0], 37.748046875)
        self.assertEquals(coordinate_list[3][1], -122.4326171875)
        self.assertEquals(coordinate_list[4][0], 37.748046875)
        self.assertEquals(coordinate_list[4][1], -122.43359375)

if __name__ == '__main__':
    unittest.main()
