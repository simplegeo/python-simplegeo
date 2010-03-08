import codecs
from cStringIO import StringIO

from zope.interface import implements
from twisted.internet.defer import succeed, Deferred
from twisted.internet.protocol import Protocol
from twisted.web.iweb import IBodyProducer

from twisted.web.client import ResponseDone
from twisted.web.http import PotentialDataLoss

def deferred_callback(d):
    def decorator(function):
        d.addCallback(function)
    return decorator

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

def receive_body(response):
    string_receiver = StringReceiver()
    response.deliverBody(string_receiver)
    return string_receiver.deferred

class StringReceiver(Protocol):
    def __init__(self):
        self.string_io = codecs.getwriter('utf_8')(StringIO())
        self.deferred = Deferred()

    def dataReceived(self, bytes):
        self.string_io.write(bytes)

    def connectionLost(self, reason):
        if reason.check(ResponseDone) or reason.check(PotentialDataLoss):
            self.deferred.callback(self.string_io.getvalue())
        else:
            self.deferred.errback(reason)
