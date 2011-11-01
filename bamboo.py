import urllib2 as URL
import json

class BambooFeed():

    def __init__(self, url, username, password):
        auth = URL.HTTPBasicAuthHandler()
        split_url = url.split('/')
        uri = split_url[0] + '//' + split_url[2] + '/'
        auth.add_password(
            realm='protected-area',
            uri=uri,
            user=username, 
            passwd=password
        )
        opener = URL.build_opener(auth)
        URL.install_opener(opener)
        try:
            feed=URL.urlopen(url)
            feed = json.loads(feed.read())
            self.latest = feed
        except:
            raise "Error opening connection to Bamboo"

