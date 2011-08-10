import urllib

from simplegeo.util import (json_decode, is_valid_lat, is_valid_lon,
                            _assert_valid_lat, _assert_valid_lon,
                            is_valid_ip)
from simplegeo import Client as ParentClient


class Client(ParentClient):

    def __init__(self, key, secret, api_version='1.0', **kwargs):
        ParentClient.__init__(self, key, secret, **kwargs)

        context_endpoints = [
            ['context', '/context/%(lat)s,%(lon)s.json'],
            ['context_by_ip', '/context/%(ip)s.json'],
            ['context_by_my_ip', '/context/ip.json'],
            ['context_by_address', '/context/address.json'],
            ['context_from_bbox', '/context/%(sw_lat)s,%(sw_lon)s,%(ne_lat)s,%(ne_lon)s.json']
        ]

        self.endpoints.update(map(lambda x: (x[0], api_version+x[1]), context_endpoints))

    def _prepare_kwargs(self, **kwargs):
        if 'context_args' in kwargs and kwargs['context_args']:
            context_args = kwargs['context_args']
            del kwargs['context_args']
            kwargs.update(context_args)
        # Filter out entries with empty values.
        kwargs = dict((k, v) for k, v in kwargs.iteritems() if v)
        return kwargs

    def get_context(self, lat, lon, filter=None, context_args=None):
        _assert_valid_lat(lat)
        _assert_valid_lon(lon)

        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")

        kwargs = self._prepare_kwargs(
            filter=filter,
            context_args=context_args)

        endpoint = self._endpoint('context', lat=lat, lon=lon)
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_by_ip(self, ipaddr, filter=None, context_args=None):
        """ The server uses guesses the latitude and longitude from
        the ipaddr and then does the same thing as get_context(),
        using that guessed latitude and longitude."""

        if not is_valid_ip(ipaddr):
            raise ValueError("Address %s is not a valid IP" % ipaddr)
        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")

        kwargs = self._prepare_kwargs(
            filter=filter,
            context_args=context_args)

        endpoint = self._endpoint('context_by_ip', ip=ipaddr)
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_by_my_ip(self, filter=None, context_args=None):
        """ The server gets the IP address from the HTTP connection
        (this may be the IP address of your device or of a firewall,
        NAT, or HTTP proxy device between you and the server), and
        then does the same thing as get_context_by_ip(), using that IP
        address."""

        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")

        kwargs = self._prepare_kwargs(
            filter=filter,
            context_args=context_args)

        endpoint = self._endpoint('context_by_my_ip')
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_by_address(self, address, filter=None, context_args=None):
        """
        The server figures out the latitude and longitude from the
        street address and then does the same thing as get_context(),
        using that deduced latitude and longitude.
        """

        if not isinstance(address, basestring):
            raise ValueError("Address must be a string.")
        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")

        kwargs = self._prepare_kwargs(
            address=address,
            filter=filter,
            context_args=context_args)

        endpoint = self._endpoint('context_by_address')
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_from_bbox(self, sw_lat, sw_lon, ne_lat, ne_lon, **kwargs):
        """
        This function takes a bbox and returns all
        features that overlap that bounding box. Category
        uses the format: categorytype__Name. Note the
        double underscore. Ex: category__Neighborhood or
        type__Public%20Place

        Note that we do NOT use the GeoJSON ordering in our API URLs, just
        responses, so the order here is (minlat, minlon, maxlat, maxlon).
        """

        kwargs = self._prepare_kwargs(
            context_args=kwargs)

        endpoint = self._endpoint('context_from_bbox',
                                  sw_lat=sw_lat, sw_lon=sw_lon,
                                  ne_lat=ne_lat, ne_lon=ne_lon)
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)
