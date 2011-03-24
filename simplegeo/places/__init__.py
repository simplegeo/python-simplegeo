import urllib

from pyutil.assertutil import precondition

from simplegeo.util import json_decode, APIError, SIMPLEGEOHANDLE_RSTR, is_valid_lat, is_valid_lon, is_valid_ip, is_numeric, is_simplegeohandle
from simplegeo.models import Feature
from simplegeo import Client as ParentClient


class Client(ParentClient):

    def __init__(self, key, secret, api_version='1.0', host='api.simplegeo.com', port=80):
        self.subclient = True
        ParentClient.__init__(self, key, secret, host=host, port=port)

        self.endpoints.update([
            # Places
            ('create', '1.0/places'),
            ('search', '1.0/places/%(lat)s,%(lon)s.json'),
            ('search_by_ip', '1.0/places/%(ipaddr)s.json'),
            ('search_by_my_ip', '1.0/places/ip.json'),
            ('search_by_address', '1.0/places/address.json')])

    def add_feature(self, feature):
        """Create a new feature, returns the simplegeohandle. """
        endpoint = self._endpoint('create')
        if feature.id:
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
        precondition(is_simplegeohandle(simplegeohandle), "simplegeohandle is required to match the regex %s" % SIMPLEGEOHANDLE_RSTR, simplegeohandle=simplegeohandle)
        endpoint = self._endpoint('feature', simplegeohandle=simplegeohandle)
        return self._request(endpoint, 'DELETE')[1]

    def search(self, lat, lon, radius=None, query=None, category=None):
        """Search for places near a lat/lon, within a radius (in kilometers)."""
        precondition(is_valid_lat(lat), lat)
        precondition(is_valid_lon(lon), lon)
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

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

        endpoint = self._endpoint('search', lat=lat, lon=lon)

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_ip(self, ipaddr, radius=None, query=None, category=None):
        """
        Search for places near an IP address, within a radius (in
        kilometers).

        The server uses guesses the latitude and longitude from the
        ipaddr and then does the same thing as search(), using that
        guessed latitude and longitude.
        """
        precondition(is_valid_ip(ipaddr), ipaddr)
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

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

        endpoint = self._endpoint('search_by_ip', ipaddr=ipaddr)

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_my_ip(self, radius=None, query=None, category=None):
        """
        Search for places near your IP address, within a radius (in
        kilometers).

        The server gets the IP address from the HTTP connection (this
        may be the IP address of your device or of a firewall, NAT, or
        HTTP proxy device between you and the server), and then does
        the same thing as search_by_ip(), using that IP address.
        """
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

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

        endpoint = self._endpoint('search_by_my_ip')

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]

    def search_by_address(self, address, radius=None, query=None, category=None):
        """
        Search for places near the given address, within a radius (in
        kilometers).

        The server figures out the latitude and longitude from the
        street address and then does the same thing as search(), using
        that deduced latitude and longitude.
        """
        precondition(isinstance(address, basestring), address)
        precondition(address != '', address)
        precondition(radius is None or is_numeric(radius), radius)
        precondition(query is None or isinstance(query, basestring), query)
        precondition(category is None or isinstance(category, basestring), category)

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
 
        endpoint = self._endpoint('search_by_address')

        result = self._request(endpoint, 'GET', data=kwargs)[1]

        fc = json_decode(result)
        return [Feature.from_dict(f) for f in fc['features']]



