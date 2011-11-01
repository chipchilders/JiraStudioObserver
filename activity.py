###
# Copyright (c) 2011, Chip Childers
# All rights reserved.
#
#
###
import feedparser
import urllib

class ActivityFeed():
    """A class to manipulate Jira Studio activity feeds"""
    def __init__(self, url, username, password, last_known_update = None):
        if url is None:
            raise "You must provide a Jira Studio feed URL"
        split_url = url.split("://")
        self.url = split_url[0] + "://" + urllib.quote(username) + ":" + urllib.quote(password) + "@" + split_url[1]
        self.feed = feedparser.parse(self.url)
        if last_known_update is None:
            self.last_updated = self.feed.entries[5]['updated_parsed']
        else:
            self.last_updated = last_known_update

    def find_next_item(self):
        i = 9
        while i > -1:
            if self.feed.entries[i]['updated_parsed'] > self.last_updated:
                self.last_updated = self.feed.entries[i]['updated_parsed']
                return ActivityItem(self.feed.entries[i])
            i = i - 1

        return None

    def update_feed(self):
        self.feed = feedparser.parse(self.url)

class ActivityItem():
    def __init__(self, entry):
        self.entry = entry
        self.updated = self.entry['updated_parsed']
        
        app = self.entry['atlassian_application']
        if app == 'com.atlassian.fisheye':
            self.application = 'Subversion'
            self._fisheye_item()
        elif app == 'com.atlassian.jira':
            self._jira_item()
            self.application = 'Jira'
        elif app == 'com.atlassian.bamboo':
            self.application = 'Bamboo'
            self._bamboo_item()
        else:
            self.application = 'Unknown'

    def get_summary(self):
        updatestring = ''
        if self.entry.application == "Bamboo":
            updatestring = "New build " + self.entry.id + " " + self.entry.status + "! " + self.entry.url
        elif self.entry.application == "Jira":
            updatestring = self.entry.actor + " " + self.entry.action + " " + self.entry.url
        elif self.entry.application == "Subversion":
            updatestring = self.entry.actor + " " + self.entry.status + " " + self.entry.url
        else:
            updatestring = self.entry.actor + " did something interesting, but I don't understand what."

        return updatestring


    def _bamboo_item(self):
        self.action = 'Build'
        self.actor = self.entry['usr_username']
        if self.entry['activity_verb'] == 'http://streams.atlassian.com/syndication/verbs/bamboo/pass':
            self.status = 'Passed'
        elif self.entry['activity_verb'] == 'http://streams.atlassian.com/syndication/verbs/bamboo/fail':
            self.status = 'Failed'
        else:
            self.status = 'Unknown'

        for i in self.entry['links']:
            if i['href'].startswith('https://mountdiablo.jira.com/builds/browse'):
                self.id = i['href'].split('/browse/')[1]
                self.url = i['href']
 

    def _jira_item(self):
        if self.entry['activity_verb'] == 'http://activitystrea.ms/schema/1.0/update':
            self.action = 'Updated'
        elif self.entry['activity_verb'] == 'http://activitystrea.ms/schema/1.0/post':
            self.action = 'Updated'
        elif self.entry['activity_verb'] == 'http://streams.atlassian.com/syndication/verbs/jira/reopen':
            self.action = 'Reopened'
        elif self.entry['activity_verb'] == 'http://streams.atlassian.com/syndication/verbs/jira/resolve':
            self.action = 'Resolved'
        elif self.entry['activity_verb'] == 'http://streams.atlassian.com/syndication/verbs/jira/close':
            self.action = 'Closed'
        else:
            self.action = 'Updated'
        self.actor = self.entry['usr_username']
        self.status = ''

        for i in entry['links']:
            if i['href'].startswith('https://mountdiablo.jira.com/browse/'):
                self.id = i['href'].split('/browse/')[1]
                self.url = i['href']

    def _fisheye_item(self):

        if self.entry['activity_verb'].startswith('http://streams.atlassian.com/syndication/verbs/crucible/') or self.entry['activity_verb'] == 'http://activitystrea.ms/schema/1.0/post':
            self.action = 'Review'
            self.status = self.entry['activity_verb'].split('/crucible/')[1]
            for i in self.entry['links']:
                if i['href'].startswith('https://mountdiablo.jira.com/source/cru/'):
                    self.id = i['href'].split('/cru/')[1]
                    self.url = i['href']

        elif self.entry['activity_verb'] == 'http://streams.atlassian.com/syndication/verbs/fisheye/push':
            self.action = 'Commit'
            self.status = 'Committed'
            for i in self.entry['links']:
                if i['href'].startswith('https://mountdiablo.jira.com/source/changelog/EDISON?cs='):
                    self.id = i['href'].split('cs=')[1]
                    self.url = i['href']

        else:
            self.action = 'Unknown'
            self.status = 'Unknown'
            self.id = 'Unknown'
            self.url = 'Unknown'

        self.actor = self.entry['usr_username']


