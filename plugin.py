###
# Copyright (c) 2011, Chip Childers
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import time
import supybot.ircmsgs as ircmsgs
import supybot.schedule as schedule
from activity import ActivityFeed
from bamboo import BambooFeed

class JiraStudioObserver(callbacks.Plugin):
    """Add the help for "@plugin help JiraStudioObserver" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(JiraStudioObserver, self)
        self.__parent.__init__(irc)
        self.bambooChannel = self.registryValue('channel', value=True)
        self.bambooTime = 30
        streams = self.registryValue('streams')
        self.activityFeeds = []
        for stream in streams:
            self.activityFeeds.append(ActivityFeed(stream, self.registryValue('username'), self.registryValue('password')))

        try:
            schedule.removeEvent('myJiraStudioObserverEvent')
        except KeyError:
            pass
        def myEventCaller():
            self.bambooEvent(irc)
        schedule.addPeriodicEvent(myEventCaller, self.bambooTime, 'myJiraStudioObserverEvent')
        self.irc = irc

    def bambooEvent(self, irc):
        self.getFeedUpdates(irc)


    def start(self, irc, msg, args):
        """takes no arguments

        A command to start the bamboo watcher."""
        # don't forget to redefine the event wrapper
        def myEventCaller():
            self.bambooEvent(irc)
        try:
            schedule.addPeriodicEvent(myEventCaller, self.bambooTime, 'myJiraStudioObserverEvent', False)
        except AssertionError:
            irc.reply('Error: JiraStudioObserver was already running!')
        else:
            irc.reply('JiraStudioObserver started!')
    start = wrap(start)


    def stop(self, irc, msg, args):
        """takes no arguments

        A command to stop the JiraStudioObserver."""
        try:
            schedule.removeEvent('myJiraStudioObserverEvent')
        except KeyError:
            irc.reply('Error: the build watcher wasn\'t running!')
        else:
            irc.reply('JiraStudioObserver stopped.')
    stop = wrap(stop)


    def reset(self, irc, msg, args):
        """takes no arguments

        Resets the bamboo build watcher.  Can be useful if something changes and you want the
        updates to reflect that.  For example, if you defined the bambooChannel as a
        supybot config, and changed it while the bamboo build watcher was running, it would still
        keep going on the same channel until you reset it."""
        def myEventCaller():
            self.bambooEvent(irc)
        try:
            schedule.removeEvent('myJiraStudioObserverEvent')
        except KeyError:
            irc.reply('Build watcher wasn\'t running')
        schedule.addPeriodicEvent(myEventCaller, self.bambooTime, 'myJiraStudioObserverEvent', False)
        irc.reply('Build watcher reset sucessfully!')
    reset = wrap(reset)

    def anyupdates(self, irc, msg, args):
        """takes no arguments

        Checks the observed activity feeds for new updates, and reports any new items
        back to the channel."""
        if not self.getFeedUpdates(irc, force_latest = True):
            irc.queueMsg(ircmsgs.privmsg(self.bambooChannel, "Nothing to update you about."))
    anyupdates = wrap(anyupdates)

    def getFeedUpdates(self, irc, force_latest=False):
        updated = False
        for feed in self.activityFeeds:
            feed.update_feed()
            while 1 == 1:
                item = feed.find_next_item()
                if item is None:
                    break
                else:
                    updated = True
                    irc.queueMsg(ircmsgs.privmsg(self.bambooChannel, item.get_summary()))

        return updated


    def latestbuild(self, irc, msg, args):
        """takes no arguments

        Returns the next random number from the random number generator.
        """
        #irc.reply('test' + str(self.bambooChannel))
        self.getLatest(irc, True)
    latestbuild = wrap(latestbuild)

    def getLatest(self, irc, force=False):
        bb = BambooFeed(self.registryValue('bambooapiurl'), self.registryValue('username'), self.registryValue('password'))
        latest = bb.latest
        if force or self.lastBuild != latest["results"]["result"][0]["key"]:
            irc.queueMsg(ircmsgs.privmsg(self.bambooChannel, "Latest build reported as: " +
                                     str(latest["results"]['result'][0]["lifeCycleState"]) +
                                     " - " +
                                     str(latest["results"]['result'][0]["state"])))
            irc.queueMsg(ircmsgs.privmsg(self.bambooChannel, "URL to latest build: " + 
                  "https://mountdiablo.jira.com/builds/browse/" +
                  str(latest["results"]['result'][0]["key"])))
            if str(latest["results"]['result'][0]["lifeCycleState"]) == "Finished":
                self.lastBuild = latest["results"]["result"][0]["key"]

Class = JiraStudioObserver
