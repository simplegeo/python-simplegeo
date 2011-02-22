import re
import ipaddr
from pyutil import jsonutil as json
from decimal import Decimal as D
from pyutil.assertutil import _assert

def json_decode(jsonstr):
    try:
        return json.loads(jsonstr)
    except (ValueError, TypeError), le:
        raise DecodeError(jsonstr, le)

def is_numeric(x):
    return isinstance(x, (int, long, float, D))

def swap(tupleab):
    return (tupleab[1], tupleab[0])

def deep_swap(struc):
    if is_numeric(struc[0]):
        _assert (len(struc) == 2, (type(struc), repr(struc)))
        _assert (is_numeric(struc[1]), (type(struc), repr(struc)))
        return swap(struc)
    return [deep_swap(sub) for sub in struc]

def _assert_valid_lat(x):
    if not is_valid_lat(x):
        raise TypeError("not a valid lat: %s" % (x,))

def _assert_valid_lon(x, strict=False):
    if not is_valid_lon(x, strict=strict):
        raise TypeError("not a valid lon (strict=%s): %s" % (strict, x,))

def is_valid_lat(x):
    return is_numeric(x) and (x <= 90) and (x >= -90)

def is_valid_lon(x, strict=False):
    """
    Longitude is technically defined as extending from -180 to
    180. However in practice people sometimes prefer to use longitudes
    which have "wrapped around" past 180. For example, if you are
    drawing a polygon around modern-day Russia almost all of it is in
    the Eastern Hemisphere, which means its longitudes are almost all
    positive numbers, but the easternmost part of it (Big Diomede
    Island) lies a few degrees east of the International Date Line,
    and it is sometimes more convenient to describe it as having
    longitude 190.9 instead of having longitude -169.1.

    If strict=True then is_valid_lon() requires a number to be in
    [-180..180] to be considered a valid longitude. If strict=False
    (the default) then it requires the number to be in [-360..360].
    """
    if strict:
        return is_numeric(x) and (x <= 180) and (x >= -180)
    else:
        return is_numeric(x) and (x <= 360) and (x >= -360)

def deep_validate_lat_lon(struc, strict_lon_validation=False):
    """
    For the meaning of strict_lon_validation, please see the function
    is_valid_lon().
    """
    if not isinstance(struc, (list, tuple, set)):
        raise TypeError('argument is required to be a sequence (of sequences of...) numbers, not: %s :: %s' % (struc, type(struc)))
    if is_numeric(struc[0]):
        if not len(struc) == 2:
            raise TypeError("The leaf element of this structure is required to be a tuple of length 2 (to hold a lat and lon).")

        _assert_valid_lat(struc[0])
        _assert_valid_lon(struc[1], strict=strict_lon_validation)
    else:
        for sub in struc:
            deep_validate_lat_lon(sub, strict_lon_validation=strict_lon_validation)
    return True

def is_valid_ip(ip):
    try:
        ipaddr.IPAddress(ip)
    except ValueError:
        return False
    else:
        return True

SIMPLEGEOHANDLE_RSTR=r"""SG_[A-Za-z0-9]{22}(?:_-?[0-9]{1,3}(?:\.[0-9]+)?_-?[0-9]{1,3}(?:\.[0-9]+)?)?(?:@[0-9]+)?$"""
SIMPLEGEOHANDLE_R= re.compile(SIMPLEGEOHANDLE_RSTR)
def is_simplegeohandle(s):
    return isinstance(s, basestring) and SIMPLEGEOHANDLE_R.match(s)

def to_unicode(s):
    """ Convert to unicode, raise exception with instructive error
    message if s is not unicode, ascii, or utf-8. """
    if not isinstance(s, unicode):
        if not isinstance(s, str):
            raise TypeError('You are required to pass either unicode or string here, not: %r (%s)' % (type(s), s))
        try:
            s = s.decode('utf-8')
        except UnicodeDecodeError, le:
            raise TypeError('You are required to pass either a unicode object or a utf-8 string here. You passed a Python string object which contained non-utf-8: %r. The UnicodeDecodeError that resulted from attempting to interpret it as utf-8 was: %s' % (s, le,))
    return s


"""Exceptions."""

class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(self, code, msg, headers, description=''):
        self.code = code
        self.msg = msg
        self.headers = headers
        self.description = description

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "%s (#%s) %s" % (self.msg, self.code, self.description)


class DecodeError(APIError):
    """There was a problem decoding the API's response, which was
    supposed to be encoded in JSON, but which apparently wasn't."""

    def __init__(self, body, le):
        super(DecodeError, self).__init__(None, "Could not decode JSON from server.", None, repr(le))
        self.body = body

    def __repr__(self):
        return "%s content: %s" % (self.description, self.body)


