import urllib

from simplegeo.util import (json_decode, is_valid_lat, is_valid_lon,
                            _assert_valid_lat, _assert_valid_lon,
                            is_valid_ip)
from simplegeo import Client as ParentClient


class Client(ParentClient):

    def __init__(self, key, secret, api_version='1.0', **kwargs):
        self.subclient = True
        ParentClient.__init__(self, key, secret, **kwargs)

        context_endpoints = [
            ['context', '/context/%(lat)s,%(lon)s.json'],
            ['context_by_ip', '/context/%(ip)s.json'],
            ['context_by_my_ip', '/context/ip.json'],
            ['context_by_address', '/context/address.json'],
            ['features_from_bbox', '/context/%(NW_lon)s,%(NW_lat)s,%(SE_lon)s,%(SE_lat)s.json']
        ]

        self.endpoints.update(map(lambda x: (x[0], api_version+x[1]), context_endpoints))

    def get_context(self, lat, lon, filter=None):
        _assert_valid_lat(lat)
        _assert_valid_lon(lon)
        
        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")
        
        kwargs = { }
        if filter:
            kwargs['filter'] = filter
        
        endpoint = self._endpoint('context', lat=lat, lon=lon)
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_by_ip(self, ipaddr, filter=None):
        """ The server uses guesses the latitude and longitude from
        the ipaddr and then does the same thing as get_context(),
        using that guessed latitude and longitude."""

        if not is_valid_ip(ipaddr):
            raise ValueError("Address %s is not a valid IP" % ipaddr)
        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")
        
        kwargs = { }
        if filter:
            kwargs['filter'] = filter

        endpoint = self._endpoint('context_by_ip', ip=ipaddr)
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_by_my_ip(self, filter=None):
        """ The server gets the IP address from the HTTP connection
        (this may be the IP address of your device or of a firewall,
        NAT, or HTTP proxy device between you and the server), and
        then does the same thing as get_context_by_ip(), using that IP
        address."""

        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")
        
        kwargs = { }
        if filter:
            kwargs['filter'] = filter

        endpoint = self._endpoint('context_by_my_ip')
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_context_by_address(self, address, filter=None):
        """
        The server figures out the latitude and longitude from the
        street address and then does the same thing as get_context(),
        using that deduced latitude and longitude.
        """
        
        if not isinstance(address, basestring):
            raise ValueError("Address must be a string.")
        if (filter and not isinstance(filter, basestring)):
            raise ValueError("Query must be a string.")
        
        kwargs = { }
        if filter:
            kwargs['filter'] = filter
        if address:
            kwargs['address'] = address

        endpoint = self._endpoint('context_by_address')
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

    def get_features_from_bbox(self, bbox, **kwargs):

        NW_lon = bbox[1]
        NW_lat = bbox[0]
        SE_lon = bbox[3]
        SE_lat = bbox[2]

        endpoint = self._endpoint('features_from_bbox', NW_lon=NW_lon, NW_lat=NW_lat, SE_lon=SE_lon, SE_lat=SE_lat)
        result = self._request(endpoint, 'GET', data=kwargs)[1]
        return json_decode(result)

