import time
from pyutil import jsonutil as json

class Record(object):
    def __init__(self, layer, id, lat, lon, created=None, **kwargs):
        self.layer = layer
        self.id = id
        self.lon = lon
        self.lat = lat
        if created is None:
            self.created = int(time.time())
        else:
            self.created = created
        self.__dict__.update(kwargs)

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        coord = data['geometry']['coordinates']
        record = cls(data['properties']['layer'], data['id'], lat=coord[1], lon=coord[0])
        record.created = data.get('created', record.created)
        record.__dict__.update(dict((k, v) for k, v in data['properties'].iteritems()
                                    if k not in ('layer', 'created')))
        return record

    def to_dict(self):
        return {
            'type': 'Feature',
            'id': self.id,
            'created': self.created,
            'geometry': {
                'type': 'Point',
                'coordinates': [self.lon, self.lat],
            },
            'properties': dict((k, v) for k, v in self.__dict__.iteritems()
                                        if k not in ('lon', 'lat', 'id', 'created')),
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return "Record(layer=%s, id=%s, lat=%s, lon=%s)" % (self.layer, self.id, self.lat, self.lon)

    def __hash__(self):
        return hash((self.layer, self.id))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id
