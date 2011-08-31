# -*- coding: utf-8 -*-
#
# © 2011 SimplegGeo, Inc. All rights reserved.
# Author: Ian Eure <ian@simplegeo.com>
#

"""Places 1.0 client."""

from simplegeo.util import (json_decode, APIError, SIMPLEGEOHANDLE_RSTR,
                            is_valid_lat, is_valid_lon,
                            _assert_valid_lat, _assert_valid_lon,
                            is_valid_ip, is_numeric, is_simplegeohandle)
from simplegeo import Client as ParentClient
from simplegeo.models import Feature

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
