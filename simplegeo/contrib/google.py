import urllib
from urllib2 import urlopen

def get_translated_address_from_feature(feature, translate_to='ru'):
    """Return a translated address using Google Translate API.
    See http://goo.gl/HXJvu for list of language codes."""
    feature = feature.to_dict()
    address = feature['properties']['address']
    langpair = '%s|%s'%('en',translate_to)
    base_url = 'http://ajax.googleapis.com/ajax/services/language/translate?'
    params = urllib.urlencode( (('v',1.0),
                                ('q',address),
                                ('langpair',langpair),) )
    url = base_url+params
    content = urlopen(url).read()
    start_idx = content.find('"translatedText":"')+18
    translation = content[start_idx:]
    end_idx = translation.find('"}, "')
    translation = translation[:end_idx]
    return translation
