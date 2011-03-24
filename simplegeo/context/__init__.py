import urllib

from pyutil.assertutil import precondition

from simplegeo.util import json_decode, is_valid_lat, is_valid_lon, is_valid_ip
from simplegeo import Client as ParentClient


class Client(ParentClient):

    def __init__(self, key, secret, api_version='1.0', host='api.simplegeo.com', port=80):
        self.subclient = True
        ParentClient.__init__(self, key, secret, host=host, port=port)

        self.endpoints.update([
            # Context
            ('context', '1.0/context/%(lat)s,%(lon)s.json'),
            ('context_by_ip', '1.0/context/%(ip)s.json'),
            ('context_by_my_ip', '1.0/context/ip.json'),
            ('context_by_address', '1.0/context/address.json')])

    def get_context(self, lat, lon):
        precondition(is_valid_lat(lat), lat)
        precondition(is_valid_lon(lon), lon)
        endpoint = self._endpoint('context', lat=lat, lon=lon)
        return json_decode(self._request(endpoint, "GET")[1])

    def get_context_by_ip(self, ipaddr):
        """ The server uses guesses the latitude and longitude from
        the ipaddr and then does the same thing as get_context(),
        using that guessed latitude and longitude."""
        precondition(is_valid_ip(ipaddr), ipaddr)
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
        precondition(isinstance(address, basestring), address)
        endpoint = self._endpoint('context_by_address')
        return json_decode(self._request(endpoint, "GET", data={'address' : address})[1])



