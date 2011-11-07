###
# Copyright (c) 2011, Chip Childers
# All rights reserved.
#
#
###
"""
The activity module holds the ActivityFeed and ActivityItem class
structures for reading and interpreting a Jira Studio activity
stream RSS feed.
"""
import feedparser
import urllib

class ActivityFeed():
    """A class to manipulate Jira Studio activity feeds"""
    def __init__(self, url, username, password, last_known_update = None):
        if url is None:
            raise Exception, "You must provide a Jira Studio feed URL"
        split_url = url.split("://")
        self.url = ''.join([split_url[0],
            "://", 
            urllib.quote(username),
            ":",
            urllib.quote(password),
            "@", 
            split_url[1]])
        self.feed = feedparser.parse(self.url)
        if last_known_update is None:
            self.last_updated = self.feed.entries[5]['updated_parsed']
        else:
            self.last_updated = last_known_update

    def find_next_item(self, force_latest = False):
        """
        Queries the feed, and returns the next ActivityItem
        """

        i = 9
        while i > -1:
            if self.feed.entries[i]['updated_parsed'] > self.last_updated:
                self.last_updated = self.feed.entries[i]['updated_parsed']
                return ActivityItem(self.feed.entries[i])
            i = i - 1

        if force_latest:
            return (ActivityItem(self.feed.entries[0]))

        return None

    def update_feed(self):
        """Forces an update of the feed content from the server"""
        self.feed = feedparser.parse(self.url)

class ActivityItem():
    """
    ActivityItem is a class responsible for understanding
    Jira Studio activity item syntax.
    """

    streams_base = "http://streams.atlassian.com/"
    bamboo_pass = ''.join([streams_base, 
                           "syndication/verbs/bamboo/pass"])
    bamboo_fail = ''.join([streams_base, 
                           "syndication/verbs/bamboo/fail"])
    bamboo_browse = 'https://mountdiablo.jira.com/builds/browse'
    jira_update = 'http://activitystrea.ms/schema/1.0/update'
    jira_post = 'http://activitystrea.ms/schema/1.0/post'
    jira_reopen = ''.join([streams_base,
                           'syndication/verbs/jira/reopen'])
    jira_resolve = ''.join([streams_base,
                           'syndication/verbs/jira/resolve'])
    jira_close = ''.join([streams_base,
                           'syndication/verbs/jira/close'])
    jira_browse = 'https://mountdiablo.jira.com/browse/'
    crucible_verb = ''.join([streams_base,
                             'syndication/verbs/crucible/'])
    general_post = 'http://activitystrea.ms/schema/1.0/post'
    crucible_link = 'https://mountdiablo.jira.com/source/cru/'
    fisheye_push = ''.join([streams_base,
                            'syndication/verbs/fisheye/push'])
    fisheye_browse = 'https://mountdiablo.jira.com/source/changelog/EDISON?cs='

    def __init__(self, entry):
        self.entry = entry
        self.updated = self.entry['updated_parsed']
        self.action = None
        self.status = None
        self.id = None
        self.url = None
        self.actor = None
        
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
        """Provides a simple string summary of an activity item"""
        updatestring = ''
        if self.application == "Bamboo":
            updatestring = ''.join([
                "New build ",
                self.id, 
                " ",
                self.status, 
                "! ",
                self.url])
        elif self.application == "Jira":
            updatestring = ''.join([
                self.actor,
                " ",
                self.action, 
                " ",
                self.url])
        elif self.application == "Subversion":
            updatestring = ''.join([self.actor,
                                    " ",
                                    self.status,
                                    " ",
                                    self.url])
        else:
            updatestring = ''.join([self.actor,
                " did something interesting, but I ",
                "don't understand what."])

        return updatestring


    def _bamboo_item(self):
        """Interprets a bamboo activity item"""
        self.action = 'Build'
        self.actor = self.entry['usr_username']
        if self.entry['activity_verb'] == ActivityItem.bamboo_pass:
            self.status = 'Passed'
        elif self.entry['activity_verb'] == ActivityItem.bamboo_fail:
            self.status = 'Failed'
        else:
            self.status = 'Unknown'

        for i in self.entry['links']:
            if i['href'].startswith(ActivityItem.bamboo_browse):
                self.id = i['href'].split('/browse/')[1]
                self.url = i['href']
 

    def _jira_item(self):
        """Interprets a Jira activity item"""
        if self.entry['activity_verb'] == ActivityItem.jira_update:
            self.action = 'Updated'
        elif self.entry['activity_verb'] == ActivityItem.jira_post:
            self.action = 'Updated'
        elif self.entry['activity_verb'] == ActivityItem.jira_reopen:
            self.action = 'Reopened'
        elif self.entry['activity_verb'] == ActivityItem.jira_resolve:
            self.action = 'Resolved'
        elif self.entry['activity_verb'] == ActivityItem.jira_close:
            self.action = 'Closed'
        else:
            self.action = 'Updated'
        self.actor = self.entry['usr_username']
        self.status = ''

        for i in self.entry['links']:
            if i['href'].startswith(ActivityItem.jira_browse):
                self.id = i['href'].split('/browse/')[1]
                self.url = i['href']

    def _fisheye_item(self):
        """Interprets Fisheye and Crucible activity items"""
        if self.entry['activity_verb'].startswith(
           ActivityItem.crucible_verb) or \
           self.entry['activity_verb'] == ActivityItem.general_post:
            self.action = 'Review'
            self.status = self.entry['activity_verb'].split('/crucible/')[1]
            for i in self.entry['links']:
                if i['href'].startswith(ActivityItem.crucible_link):
                    self.id = i['href'].split('/cru/')[1]
                    self.url = i['href']

        elif self.entry['activity_verb'] == ActivityItem.fisheye_push:
            self.action = 'Commit'
            self.status = 'Committed'
            for i in self.entry['links']:
                if i['href'].startswith(ActivityItem.fisheye_browse):
                    self.id = i['href'].split('cs=')[1]
                    self.url = i['href']

        else:
            self.action = 'Unknown'
            self.status = 'Unknown'
            self.id = 'Unknown'
            self.url = 'Unknown'

        self.actor = self.entry['usr_username']


