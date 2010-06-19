import unittest
from simplegeo import Record

class RecordTest(unittest.TestCase):

    def test_record_from_dict(self):
        record_dict = {'created': 10,
                     'geometry' : {
                                   'type' : 'Point',
                                   'coordinates' : [10.0, 11.0]
                                   },
                     'id' : 'my_id',
                     'type' : 'Feature',
                     'properties' : {
                                     'layer' : 'my_layer',
                                     'key' : 'value'  ,
                                     'type' : 'object'
                                     }
                     }

        record = Record.from_dict(record_dict)
        self.assertEquals(record.created, record_dict['created'])
        self.assertEquals(record.lat, 11.0)
        self.assertEquals(record.lon, 10.0)
        self.assertEquals(record.id, 'my_id')
        self.assertEquals(record.layer, 'my_layer')
        self.assertEquals(record.key, 'value')
        self.assertEquals(record.type, 'object')
                     