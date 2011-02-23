import time
import copy
from pyutil import jsonutil as json
from util import json_decode, deep_swap, deep_validate_lat_lon, is_simplegeohandle, SIMPLEGEOHANDLE_RSTR
from pyutil.assertutil import precondition

class Feature:
    def __init__(self, coordinates, geomtype='Point', simplegeohandle=None, properties=None, strict_lon_validation=False):
        """
        The simplegeohandle and the record_id are both optional -- you
        can have one or the other or both or neither.

        A simplegeohandle is globally unique and is assigned by the
        Places service. It is returned from the Places service in the
        response to a request to add a place to the Places database
        (the add_feature method).

        The simplegeohandle is passed in as an argument to the
        constructor, named "simplegeohandle", and is stored in the
        "id" attribute of the Feature instance.

        A record_id is scoped to your particular user account and is
        chosen by you. The only use for the record_id is in case you
        call add_feature and you have already previously added that
        feature to the database -- if there is already a feature from
        your user account with the same record_id then the Places
        service will return that feature to you, along with that
        feature's simplegeohandle, instead of making a second, duplicate
        feature.

        A record_id is passed in as a value in the properties dict
        named "record_id".

        geomtype is a GeoJSON geometry type such as "Point",
        "Polygon", or "Multipolygon". coordinates is a GeoJSON
        coordinates *except* that each lat/lon pair is written in
        order lat, lon instead of the GeoJSON order of lon, at.

        When a Feature is being submitted to the SimpleGeo Places
        database, if there is a key 'private' in the properties dict
        which is set to True, then the Feature is intended to be
        visible only to your user account. If there is no 'private'
        key or if there is a 'private' key which is set to False, then
        the Feature is intended to be merged into the publicly visible
        Places Database.

        Note that even if it is intended to be merged into the public
        Places Database the actual process of merging it into the
        public shared database may take some time, and the newly added
        Feature will be visible to your account right away even if it
        isn't (yet) visible to the public.

        For the meaning of strict_lon_validation, please see the
        function is_valid_lon().
        """
        try:
            deep_validate_lat_lon(coordinates, strict_lon_validation=strict_lon_validation)
        except TypeError, le:
            raise TypeError("The first argument, 'coordinates' is required to be a 2-element sequence of lon, lat for a point (or a more complicated set of coordinates for polygons or multipolygons), but it was %s :: %r. The error that was raised from validating this was: %s" % (type(coordinates), coordinates, le))

        if not (simplegeohandle is None or is_simplegeohandle(simplegeohandle)):
            raise TypeError("The third argument, 'simplegeohandle' is required to be None or to match this regex: %s, but it was %s :: %r" % (SIMPLEGEOHANDLE_RSTR, type(simplegeohandle), simplegeohandle))

        record_id = properties and properties.get('record_id') or None
        if not (record_id is None or isinstance(record_id, basestring)):
            raise TypeError("record_id is required to be None or a string, but it was: %r :: %s." % (type(record_id), record_id))
        self.strict_lon_validation = strict_lon_validation
        precondition(coordinates)
        self.id = simplegeohandle
        self.coordinates = coordinates
        self.geomtype = geomtype
        self.properties = {'private': False}
        if properties:
            self.properties.update(properties)

    @classmethod
    def from_dict(cls, data, strict_lon_validation=False):
        """
        data is a GeoJSON standard data structure, including that the
        coordinates are in GeoJSON order (lon, lat) instead of
        SimpleGeo order (lat, lon)
        """
        assert isinstance(data, dict), (type(data), repr(data))
        coordinates = deep_swap(data['geometry']['coordinates'])
        try:
            deep_validate_lat_lon(coordinates, strict_lon_validation=strict_lon_validation)
        except TypeError, le:
            raise TypeError("The 'coordinates' value is required to be a 2-element sequence of lon, lat for a point (or a more complicated set of coordinates for polygons or multipolygons), but it was %s :: %r. The error that was raised from validating this was: %s" % (type(coordinates), coordinates, le))
        feature = cls(
            simplegeohandle = data.get('id'),
            coordinates = coordinates,
            geomtype = data['geometry']['type'],
            properties = data.get('properties')
            )

        return feature

    def to_dict(self):
        """
        Returns a GeoJSON object, including having its coordinates in
        GeoJSON standad order (lon, lat) instead of SimpleGeo standard
        order (lat, lon).
        """
        return {
            'type': 'Feature',
            'id': self.id,
            'geometry': {
                'type': self.geomtype,
                'coordinates': deep_swap(self.coordinates)
            },
            'properties': copy.deepcopy(self.properties),
        }

    @classmethod
    def from_json(cls, jsonstr):
        return cls.from_dict(json_decode(jsonstr))

    def to_json(self):
        return json.dumps(self.to_dict())


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

class Layer(object):
    def __init__(self, name, title='', description='', public=False,
                 callback_urls=[]):
        self.name = name
        self.title = title
        self.description = description
        self.public = public
        self.callback_urls = callback_urls

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        layer = cls(data.get('name'), data.get('title'),
                    data.get('description'), data.get('public'),
                    data.get('callback_urls'))
        return layer

    def to_dict(self):
        return {
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'public': self.public,
            'callback_urls': self.callback_urls,
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return "Layer(name=%s, public=%s)" % (self.name, self.public)

    def __hash__(self):
        return hash((self.name))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name
