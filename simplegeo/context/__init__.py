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
            ['context_by_address', '/context/address.json']
        ]

        self.endpoints.update(map(lambda x: (x[0], api_version+x[1]), context_endpoints))

    def get_context(self, lat, lon):
        _assert_valid_lat(lat)
        _assert_valid_lon(lon)
        endpoint = self._endpoint('context', lat=lat, lon=lon)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_ip(self, ipaddr):
        """ The server uses guesses the latitude and longitude from
        the ipaddr and then does the same thing as get_context(),
        using that guessed latitude and longitude."""
        if not is_valid_ip(ipaddr):
            raise ValueError("Address %s is not a valid IP" % ipaddr)
        endpoint = self._endpoint('context_by_ip', ip=ipaddr)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_my_ip(self):
        """ The server gets the IP address from the HTTP connection
        (this may be the IP address of your device or of a firewall,
        NAT, or HTTP proxy device between you and the server), and
        then does the same thing as get_context_by_ip(), using that IP
        address."""
        endpoint = self._endpoint('context_by_my_ip')
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_address(self, address):
        """
        The server figures out the latitude and longitude from the
        street address and then does the same thing as get_context(),
        using that deduced latitude and longitude.
        """
        if not isinstance(address, basestring):
            raise ValueError("Address must be a string.")
        endpoint = self._endpoint('context_by_address')
        return json_decode(self._request(endpoint, "GET", data={'address' : address})[1])



