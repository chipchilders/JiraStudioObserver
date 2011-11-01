import urllib2 as URL
import json

class BambooFeed():

    def __init__(self):
        auth = URL.HTTPBasicAuthHandler()
        auth.add_password(
            realm='protected-area',
            uri='urihere',
            user='username', 
            passwd='password'
        )
        opener = URL.build_opener(auth)
        URL.install_opener(opener)
        try:
            feed=URL.urlopen('urlgoeshere')
            feed = json.loads(feed.read())
            self.latest = feed
        except:
            raise "Error opening connection to Bamboo"

