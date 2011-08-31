
import urllib

from simplegeo.util import (json_decode, APIError, SIMPLEGEOHANDLE_RSTR,
                            is_valid_lat, is_valid_lon,
                            _assert_valid_lat, _assert_valid_lon,
                            is_valid_ip, is_numeric, is_simplegeohandle)
from simplegeo import Client as ParentClient


class Client(ParentClient):

    def __init__(self, key, secret, api_version='1.0', **kwargs):
        ParentClient.__init__(self, key, secret, **kwargs)

        places_endpoints = [
            ['create', '/places'],
            ['search', '/places/%(lat)s,%(lon)s.json'],
            ['search_by_ip', '/places/%(ipaddr)s.json'],
            ['search_by_my_ip', '/places/ip.json'],
            ['search_by_address', '/places/address.json']
        ]

        self.endpoints.update(map(lambda x: (x[0], api_version+x[1]), places_endpoints))

    def add_feature(self, feature):
        """Create a new feature, returns the simplegeohandle. """
        endpoint = self._endpoint('create')
        if hasattr(feature, 'id'):
            # only simplegeohandles or None should be stored in self.id
            assert is_simplegeohandle(feature.id)
            raise ValueError('A feature cannot be added to the Places database when it already has a simplegeohandle: %s' % (feature.id,))
        jsonrec = feature.to_json()
        resp, content = self._request(endpoint, "POST", jsonrec)
        if resp['status'] != "202":
            raise APIError(int(resp['status']), content, resp)
        contentobj = json_decode(content)
        if not contentobj.has_key('id'):
            raise APIError(int(resp['status']), content, resp)
        handle = contentobj['id']
        assert is_simplegeohandle(handle)
        return handle

    def update_feature(self, feature):
        """Update a Places feature."""
        endpoint = self._endpoint('feature', simplegeohandle=feature.id)
        return self._request(endpoint, 'POST', feature.to_json())[1]

    def delete_feature(self, simplegeohandle):
        """Delete a Places feature."""
        if not is_simplegeohandle(simplegeohandle):
            raise ValueError("simplegeohandle is required to match "
                             "the regex %s" % SIMPLEGEOHANDLE_RSTR)
        endpoint = self._endpoint('feature', simplegeohandle=simplegeohandle)
        return self._request(endpoint, 'DELETE')[1]

    def search(self, lat, lon, radius=None, query=None, category=None, num=None):
        """Search for places near a lat/lon, within a radius (in kilometers)."""
        _assert_valid_lat(lat)
        _assert_valid_lon(lon)
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        endpoint = self._endpoint('search', lat=lat, lon=lon)

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_ip(self, ipaddr, radius=None, query=None, category=None, num=None):
        """
        Search for places near an IP address, within a radius (in
        kilometers).

        The server uses guesses the latitude and longitude from the
        ipaddr and then does the same thing as search(), using that
        guessed latitude and longitude.
        """
        if not is_valid_ip(ipaddr):
            raise ValueError("Address %s is not a valid IP" % ipaddr)
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        endpoint = self._endpoint('search_by_ip', ipaddr=ipaddr)

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_my_ip(self, radius=None, query=None, category=None, num=None):
        """
        Search for places near your IP address, within a radius (in
        kilometers).

        The server gets the IP address from the HTTP connection (this
        may be the IP address of your device or of a firewall, NAT, or
        HTTP proxy device between you and the server), and then does
        the same thing as search_by_ip(), using that IP address.
        """
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        endpoint = self._endpoint('search_by_my_ip')

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_address(self, address, radius=None, query=None, category=None, num=None):
        """
        Search for places near the given address, within a radius (in
        kilometers).

        The server figures out the latitude and longitude from the
        street address and then does the same thing as search(), using
        that deduced latitude and longitude.
        """
        if not isinstance(address, basestring) or not address.strip():
            raise ValueError("Address must be a non-empty string.")
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(address, unicode):
            address = address.encode('utf-8')
        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { 'address': address }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num
 
        endpoint = self._endpoint('search_by_address')

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]


class Client12(ParentClient):

    def __init__(self, key, secret, **kwargs):
        ParentClient.__init__(self, key, secret, **kwargs)

        self.endpoints.update(
            feature='1.2/features/%(place_id)s.json',
            search='1.2/places/%(lat)s,%(lon)s.json',
            search_text='1.2/places/search.json',
            search_bbox='1.2/places/%(lat_sw)s,%(lon_sw)s,%(lat_ne)s,%(lon_ne)s.json',
            search_by_ip='1.2/places/%(ipaddr)s.json',
            search_by_my_ip='1.2/places/ip.json',
            search_by_address='1.2/places/address.json')

    def _respond(self, headers, response):
        """Return the correct structure for this response."""
        status = int(headers['status'])
        if status >= 200 and status < 300:
            return json_decode(response)

        if (status >= 300 and status < 400 or
            status < 200):
            return {'headers': headers, 'body': response}

        raise APIError(status, response, headers)

    def get_feature(self, place_id):
        """Return the GeoJSON representation of a feature."""
        (headers, response) = self._request(
            self._endpoint('feature', place_id=place_id), 'GET')
        return self._respond(headers, response)

    def search(self, lat, lon, radius=None, query=None, category=None,
               num=None):
        """Search for places near a lat/lon, within a radius (in kilometers)."""
        _assert_valid_lat(lat)
        _assert_valid_lon(lon)
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        return self._respond(*self._request(self._endpoint(
                    'search', lat=lat, lon=lon),
                              'GET', data=kwargs))

    def search_text(self, query=None, category=None, num=None):
        """Fulltext search for places."""
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        return self._respond(*self._request(self._endpoint('search_text'),
                                            'GET', data=kwargs))

    def search_bbox(self, lat_sw, lon_sw, lat_ne, lon_ne, query=None,
                    category=None, num=None):
        """Return places inside a box of (lat_sw, lon_sw), (lat_ne, lon_ne)."""
        _assert_valid_lat(lat_sw)
        _assert_valid_lat(lat_ne)
        _assert_valid_lon(lon_sw)
        _assert_valid_lon(lon_ne)
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        return self._respond(*self._request(self._endpoint(
                    'search_bbox', lat_sw=lat_sw, lon_sw=lon_sw,
                    lat_ne=lat_ne, lon_ne=lon_ne), 'GET', data=kwargs))

    def search_by_ip(self, ipaddr, radius=None, query=None,
                     category=None, num=None):
        """
        Search for places near an IP address, within a radius (in
        kilometers).

        The server uses guesses the latitude and longitude from the
        ipaddr and then does the same thing as search(), using that
        guessed latitude and longitude.
        """
        if not is_valid_ip(ipaddr):
            raise ValueError("Address %s is not a valid IP" % ipaddr)
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        return self._respond(*self._request(self._endpoint(
                    'search_by_ip', ipaddr=ipaddr), 'GET', data=kwargs))

    def search_by_my_ip(self, radius=None, query=None, category=None, num=None):
        """
        Search for places near your IP address, within a radius (in
        kilometers).

        The server gets the IP address from the HTTP connection (this
        may be the IP address of your device or of a firewall, NAT, or
        HTTP proxy device between you and the server), and then does
        the same thing as search_by_ip(), using that IP address.
        """
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        return self._respond(*self._request(self._endpoint(
                    'search_by_my_ip'), 'GET', data=kwargs))

    def search_by_address(self, address, radius=None, query=None,
                          category=None, num=None):
        """
        Search for places near the given address, within a radius (in
        kilometers).

        The server figures out the latitude and longitude from the
        street address and then does the same thing as search(), using
        that deduced latitude and longitude.
        """
        if not isinstance(address, basestring) or not address.strip():
            raise ValueError("Address must be a non-empty string.")
        if (radius and not is_numeric(radius)):
            raise ValueError("Radius must be numeric.")
        if (query and not isinstance(query, basestring)):
            raise ValueError("Query must be a string.")
        if (category and not isinstance(category, basestring)):
            raise ValueError("Category must be a string.")
        if (num and not is_numeric(num)):
            raise ValueError("Num parameter must be numeric.")

        if isinstance(address, unicode):
            address = address.encode('utf-8')
        if isinstance(query, unicode):
            query = query.encode('utf-8')
        if isinstance(category, unicode):
            category = category.encode('utf-8')

        kwargs = { 'address': address }
        if radius:
            kwargs['radius'] = radius
        if query:
            kwargs['q'] = query
        if category:
            kwargs['category'] = category
        if num:
            kwargs['num'] = num

        return self._respond(*self._request(self._endpoint(
                    'search_by_address'), 'GET', data=kwargs))
