import time
import random
import unittest
from simplegeo import Client, Record, APIError

MY_OAUTH_KEY = 'your_oauth_key'
MY_OAUTH_SECRET = 'your_oauth_secret'
TESTING_LAYER = 'your_testing_layer'

API_VERSION = '0.1'
API_HOST = 'api.simplegeo.com'
API_PORT = 80

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
            lon=str(random.uniform(top_left[1], bottom_right[1]))
        )
        return record

    def test_multi_record_post(self):
        post_records = [self._record() for i in range(10)]
        self.client.add_records(TESTING_LAYER, post_records)

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


if __name__ == '__main__':
    unittest.main()
