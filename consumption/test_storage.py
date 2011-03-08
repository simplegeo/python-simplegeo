import time
import random
import unittest
from decimal import Decimal as D

from pyutil import jsonutil as json

from simplegeo import Client
from simplegeo.models import Record, Layer
from simplegeo.util import APIError

import config

if config.MY_OAUTH_KEY == 'MY_OAUTH_KEY' or \
    config.MY_OAUTH_SECRET == 'MY_SECRET_KEY':
    raise Exception('Please provide the proper credentials in config.py.')

API_VERSION = '0.1'

TESTING_LAT = '37.7481624945'
TESTING_LON = '-122.433287165'
TESTING_IP_ADDRESS = '173.164.32.246'

TESTING_LAT_NON_US = '48.8566667'
TESTING_LON_NON_US = '2.3509871'
RECORD_TYPES = ['person', 'place', 'object']
TESTING_BOUNDS = [-122.43409, 37.747296999999996, -122.424768, 37.751841999999996]


class ClientTest(unittest.TestCase):

    def tearDown(self):
        for record in self.created_records:
            try:
                self.client.storage.delete_record(record.layer, record.id)
            except APIError, e:
                # If we get a 404, then our job is done.
                pass
        self._delete_test_layer()

    def setUp(self):
        self.client = Client(config.MY_OAUTH_KEY, config.MY_OAUTH_SECRET, host=config.API_HOST, port=config.API_PORT)
        self.created_records = []
        self._create_test_layer()

    def _create_test_layer(self):
        self.layer = Layer('test.layer.' + config.MY_OAUTH_KEY,
                           'Layer for Tests', 'Layer for \
                            Tests', False, ['http://simplegeo.com',
                            'http://example.com'])
        response = self.client.storage.create_layer(self.layer)
        self.assertEquals(response, {'status': 'OK'})
        response = self.client.storage.get_layer(self.layer.name)
        self.assertEquals(response['name'], self.layer.name)
        self.assertEquals(response['title'], self.layer.title)
        self.assertEquals(response['description'], self.layer.description)
        self.assertEquals(response['callback_urls'], self.layer.callback_urls)
        self.assertEquals(response['public'], self.layer.public)
        self.assert_(response['created'])
        self.assert_(response['updated'])

    def _delete_test_layer(self):
        response = self.client.storage.delete_layer(self.layer.name)
        self.assertEquals(response, {'status': 'Deleted'})
        self.assertRaises(APIError, self.client.storage.get_layer, self.layer.name)

    def _record(self):
        """ Generate a record in San Francisco. """
        top_left = [37.801646236899785, -122.47833251953125]
        bottom_right = [37.747371884118664, -122.3931884765625]

        record = Record(
            layer=self.layer.name,
            id=str(int(random.random() * 1000000)),
            lat=str(random.uniform(top_left[0], bottom_right[0])),
            lon=str(random.uniform(top_left[1], bottom_right[1])),
            type=RECORD_TYPES[random.randint(0, 2)]
        )
        return record

    def test_multi_record_post(self):
        post_records = [self._record() for i in range(10)]
        self.addRecordsAndSleep(self.layer.name, post_records)

        get_records = self.client.storage.get_records(self.layer.name,
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

        self.assertRaises(APIError, self.client.storage.add_records, self.layer.name,
                          records)

    def test_add_record(self):
        record = self._record()
        self.addRecordAndSleep(record)
        result = self.client.storage.get_record(record.layer, record.id)
        self.assertPointIsRecord(result, record)

    def test_add_update_delete_record(self):
        record = self._record()
        self.addRecordAndSleep(record)
        result = self.client.storage.get_record(record.layer, record.id)
        self.assertPointIsRecord(result, record)
        updated_record = self._record()
        updated_record.id = record.id
        self.addRecordAndSleep(updated_record)
        updated_result = self.client.storage.get_record(record.layer, record.id)
        self.assertPointIsRecord(updated_result, updated_record)
        self.client.storage.delete_record(record.layer, record.id)
        time.sleep(5)
        self.assertRaises(APIError, self.client.storage.get_record, record.layer, record.id)
        self.assertRaises(APIError, self.client.storage.get_record, updated_record.layer, updated_record.id)

    def test_record_history(self):
        post_records = [self._record() for i in range(10)]
        current_time = int(time.time())
        for record in post_records:
            record.id = post_records[0].id
            record.created = current_time
            current_time -= 1

        self.addRecordsAndSleep(self.layer.name, post_records)

        history = self.client.storage.get_history(self.layer.name, post_records[0].id)
        points = history.get('geometries')
        self.assertEquals(len(points), 10)

        count = 0
        for point in points:
            self.assertEquals(str(point.get('coordinates')[0]), post_records[count].lon)
            self.assertEquals(str(point.get('coordinates')[1]), post_records[count].lat)
            count += 1

    """ Waiting on Gate
    def test_nearby_ip_address_search(self):
        limit = 5
        records = []
        for i in range(limit):
            record = self._record()
            record.lat = float(39.7437) + (i / 10000000)
            record.lon = float(-104.9793) - (i / 10000000)
            records.append(record)

        self.addRecordsAndSleep(self.layer.name, records)

        nearby_result = self.client.get_nearby_ip_address(self.layer.name, TESTING_IP_ADDRESS, limit=limit, radius=10)

        features = nearby_result.get('features')
        self.assertEquals(len(features), limit)
    """


    # Layer Management

    def test_update_layer(self):
        self.layer.public = True
        response = self.client.storage.update_layer(self.layer)
        self.assertEquals(response, {'status': 'OK'})
        response = self.client.storage.get_layer(self.layer.name)
        self.assertEquals(response['name'], self.layer.name)
        self.assertEquals(response['title'], self.layer.title)
        self.assertEquals(response['description'], self.layer.description)
        self.assertEquals(response['callback_urls'], self.layer.callback_urls)
        self.assertEquals(response['public'], self.layer.public)
        self.assert_(response['created'])
        self.assert_(response['updated'])

    def test_get_layers(self):
        response = self.client.storage.get_layers()
        self.assert_(len(response.get('layers')) >= 1)


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
        self.assertEquals(point['geometry']['type'], 'Point')
        self.assertEquals(point['geometry']['coordinates'][0], D(record.lon))
        self.assertEquals(point['geometry']['coordinates'][1], D(record.lat))

    def addRecordAndSleep(self, record):
        self.client.storage.add_record(record)
        self.created_records.append(record)
        time.sleep(5)

    def addRecordsAndSleep(self, layer, records):
        self.client.storage.add_records(layer, records)
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
