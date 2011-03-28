import ssl
import socket
from httplib2 import has_timeout
import httplib2
from simplegeo.contrib import socks


class CertificateValidationError(httplib2.HttpLib2Error):
    pass


def validating_sever_factory():
    # we need to define a closure here because we don't control
    # the arguments this class is instantiated with
    class ValidatingHTTPSConnection(httplib2.HTTPSConnectionWithTimeout):

        def connect(self):
            # begin copypasta from HTTPSConnectionWithTimeout
            "Connect to a host on a given (SSL) port."

            if self.proxy_info and self.proxy_info.isgood():
                sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setproxy(*self.proxy_info.astuple())
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            if has_timeout(self.timeout):
                sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            # end copypasta


            try:
                self.sock = ssl.wrap_socket(sock,
                            self.key_file,
                            self.cert_file,
                            cert_reqs=ssl.CERT_REQUIRED
                            )
            except ssl.SSLError:
                # we have to capture the exception here and raise later because
                # httplib2 tries to ignore exceptions on connect
                import sys
                self._exc_info = sys.exc_info()
                raise
            else:
                self._exc_info = None

                # this might be redundant
                server_cert = self.sock.getpeercert()
                if not server_cert:
                    raise CertificateValidationError(repr(server_cert))

        def getresponse(self):
            if not self._exc_info:
                return httplib2.HTTPSConnectionWithTimeout.getresponse(self)
            else:
                raise self._exc_info[1], None, self._exc_info[2]
    return ValidatingHTTPSConnection


def request(url,
        method='GET',
        body=None,
        headers=None,
        keyfile=None,
        certfile=None,
        ca_certs=None,
        proxy_info=None,
        timeout=30):
    """
    makes an http/https request, with optional client certificate and server
    certificate verification.
    returns response, content
    """
    kwargs = {}
    h = httplib2.Http(proxy_info=proxy_info, timeout=timeout)
    is_ssl = url.startswith('https')
    if is_ssl and ca_certs:
        kwargs['connection_type'] = validating_sever_factory()

    if is_ssl and keyfile and certfile:
        h.add_certificate(keyfile, certfile, '')
    return h.request(url, method=method, body=body, headers=headers, **kwargs)
