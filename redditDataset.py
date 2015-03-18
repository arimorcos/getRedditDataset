__author__ = 'Ari Morcos'

from requests import HTTPError
import praw
from redditDB import RedditDB
import datetime
import time
import itertools
import sys
import os


def createDataset(r, subreddits, startDate=(datetime.datetime.now()-datetime.timedelta(days=7)).strftime('%y%m%d%H%M%S'),
                  endDate=datetime.datetime.now().strftime('%y%m%d%H%M%S'), nCommentsPerSubmission=100, dbName='reddit',
                  fineScale=12, nPostsPerFineScale=200):
    """
    :param r: reddit object
    :param subreddits: list of subreddits to grab
    :param startDate: start date in format yymmddHHMMSS
    :param endDate: end date in format yymmddHHMMSS
    :param nCommentsPerSubmission: number of comments to grab per submission. Default is 100.
    :param dbName: base of database name
    :param fineScale: scale of database in hours
    :param nPostsPerFineScale: number of posts per fine scale
    :return:
    """

    # initialize database
    dbObj = RedditDB(dbName=dbName)

    # loop through each subreddit
    for sub in subreddits:

        print 'Processing subreddit: ' + sub.title.encode('utf-8')

        # get submissions within the date range
        matchingPosts = getAllPostsWithinRangeFineScale(sub, startDate=startDate, endDate=endDate, fineScale=fineScale,
                                                        nPostsPer=nPostsPerFineScale)

        # loop through each post and get top comments
        for post in matchingPosts:

            print 'Processing post: ' + post.title.encode('utf-8')

            # save post
            dbObj.saveSubmission(post)

            # get comments
            numTries = 0
            gotComments = False
            while not gotComments and numTries < 10:
                try:
                    comments = getCommentsFromSubmission(post, nCommentsPerSubmission)
                    gotComments = True
                except HTTPError:
                    time.sleep(2)
                    numTries += 1

            # save comment data for comments which have not been deleted
            # print [com.author.name for com in comments if isinstance(com, praw.objects.Comment)]
            [dbObj.saveCommentData(com) for com in comments if isinstance(com, praw.objects.Comment)
             and com.author is not None]

    dbObj.closeConnection()
    print ('\nData collection complete!')


def getSubreddits(r, subredditNames):
    """
    :param r: reddit object
    :param subredditNames: list of subreddit names to retrieve
    :return: generator object of subreddit objects
    """

    for sub in subredditNames:
        yield r.get_subreddit(sub.lower())


def getRecentSubmissions(subreddit, dateRange):

    try:
        # perform an empty search to get all submissions within date range
        searchResult = subreddit.search('', period=dateRange, limit=None)
    except HTTPError:
        time.sleep(2)
        searchResult = getRecentSubmissions(subreddit, dateRange)

    # return search result
    return searchResult


def getCommentsFromSubmission(submission, nCommentsPerSubmission):

    # get comment list
    flatComments = praw.helpers.flatten_tree(submission.comments)

    # filter list and return
    return flatComments[:nCommentsPerSubmission]


def getAllPostsWithinRangeFineScale(subreddit, startDate, endDate, fineScale=12, nPostsPer=1000):
    """
    Grabs posts using fine scale to grab maximum number
    :param fineScale: scale in hours. Default is 12.
    :param subreddit: subreddit object
    :param startDate: start date in format yymmdd
    :param endDate: end date in format yymmdd
    :param nPostsPer: number of posts per unit
    :return:
    """

    # create datetime object for each date
    startDateObject = datetime.datetime.strptime(startDate, "%y%m%d%H%M%S")
    endDateObject = datetime.datetime.strptime(endDate, "%y%m%d%H%M%S")

    # get posts
    posts = []
    tempStart = startDateObject
    while True:

        # get temporary end date
        tempEnd = tempStart + datetime.timedelta(hours=fineScale)

        # check if tempEnd is after than endDateObject
        if (tempEnd - endDateObject) > datetime.timedelta(0, 0, 0):
            # set tempEnd to be endDateObject
            tempEnd = endDateObject

        # break if start is after end
        if (tempStart - tempEnd) > datetime.timedelta(0, 0, 0):
            break

        # convert to strings
        tempStartStr = tempStart.strftime('%y%m%d%H%M%S')
        tempEndStr = tempEnd.strftime('%y%m%d%H%M%S')

        # get posts within range
        tempPosts = getPostsWithinRange(subreddit, tempStartStr, tempEndStr, nPosts=nPostsPer)

        # combine with posts
        posts = itertools.chain(posts, tempPosts)

        # iterate on start date
        tempStart = tempEnd + datetime.timedelta(seconds=1)

    # return
    return posts


def getPostsWithinRange(subreddit, startDate, endDate, nPosts=1000):
    """
    :param subreddit: subreddit object
    :param startDate: start date in format yymmddHHMMSS
    :param endDate: end date in format yymmddHHMMSS
    :return: generator object of posts
    """
    # convert dates to unix time format
    startDate = time.mktime(datetime.datetime.strptime(startDate, "%y%m%d%H%M%S").timetuple())
    endDate = time.mktime(datetime.datetime.strptime(endDate, "%y%m%d%H%M%S").timetuple())

    # generate timestamp search term
    searchTerm = 'timestamp:' + str(startDate)[:-2] + '..' + str(endDate)[:-2]

    # get posts
    try:
        posts = subreddit.search(searchTerm, sort='top', syntax='cloudsearch', limit=nPosts)
    except HTTPError:
        time.sleep(2)
        posts = getPostsWithinRange(subreddit, startDate, endDate, nPosts=nPosts)

    return posts


if __name__ == "__main__":

    # handle arguments
    startDate = sys.argv[1]
    endDate = sys.argv[2]
    dbName = sys.argv[3]
    fineScale = int(sys.argv[4])


    # initialize reddit object
    r = praw.Reddit(user_agent='get_dataset')
    subreddits = r.get_popular_subreddits(limit=200)
    createDataset(r, subreddits, startDate=startDate, endDate=endDate, dbName=dbName, fineScale=fineScale)
