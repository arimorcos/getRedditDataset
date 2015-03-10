__author__ = 'Ari Morcos'

from requests import HTTPError
import praw
import sqlite3
import os
import datetime
import time
import itertools


def createDataset(r, subreddits, dateRange='month', nCommentsPerSubmission=100, dbName='reddit'):
    """
    :param r: reddit object
    :param subreddits: list of subreddits to grab
    :param dateRange: range of posts to get. Default is one month.
    :param nCommentsPerSubmission: number of comments to grab per submission. Default is 100.
    :return:
    """

    # initialize database
    c = initializeDatabase(dbName=dbName)

    # loop through each subreddit
    for sub in subreddits:

        print 'Processing subreddit: ' + sub.title

        # get submissions within the date range
        recentPosts = getRecentSubmissions(sub, dateRange)

        # loop through each post and get top comments
        for post in recentPosts:

            print 'Processing post: ' + post.title

            # save post
            saveSubmission(c, post)

            # get comments
            comments = getCommentsFromSubmission(post, nCommentsPerSubmission)

            # save comment data for comments which have not been deleted
            # print [com.author.name for com in comments if isinstance(com, praw.objects.Comment)]
            [saveCommentData(c, com) for com in comments if isinstance(com, praw.objects.Comment)
             and com.author is not None]


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
    startDateObject = datetime.datetime.strptime(startDate, "%y%m%d")
    endDateObject = datetime.datetime.strptime(endDate, "%y%m%d")

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


def getDatabasePath(baseName):
    """
    :param baseName: base name for database
    :return: full absolute database path
    """
    userPath = os.path.expanduser('~')
    basePath = os.path.abspath(os.path.join(userPath, 'Databases'))
    databasePath = os.path.abspath(os.path.join(basePath, baseName + '.db'))

    # make directory if it doesn't exist
    if not os.path.exists(basePath):
        os.makedirs(basePath)
    return databasePath


def initializeDatabase(dbName='reddit'):
    """
    Initializes a database connection called 'reddit.db'
    :return: cursor object
    """

    dbPath = getDatabasePath(dbName)
    dbObj = sqlite3.connect(dbPath)
    c = dbObj.cursor()

    # get list of tables
    tableList = c.execute("Select name from sqlite_master where type = 'table' ")

    # check if comments exist in tableList
    commentsPresent = any(['comments' == item[0] for item in [row for row in list(tableList)]])

    if not commentsPresent:
        # create comments table
        c.execute('Create TABLE comments (date, user, body, comScore, postID)')

        # create submissions table
        c.execute('Create TABLE submissions (postID, postTitle, postBody, postScore, subredditName, subredditID)')

    return c


def saveCommentData(c, comment):
    """
    :param c: cursor object output by initialize database
    :param comment: comment object
    :return: void
    """

    # extract relevant fields
    commentDate = datetime.date.fromtimestamp(comment.created_utc)
    commentDateStr = commentDate.strftime('%Y%m%d%H%M%S')
    userName = comment.author.name
    body = comment.body
    submissionID = comment._submission.name
    score = comment.score

    # save data
    c.execute('Insert into comments VALUES (?, ?, ?, ?, ?)', [commentDateStr, userName, body, score, submissionID])
    c.connection.commit()


def saveSubmission(c, post):
    """
    :param c: cursor object output by initialize database
    :param post: post object
    :return: void
    """

    # extract relevant fields
    submissionID = post.name
    submissionTitle = post.title
    subredditID = post.subreddit.name
    subredditName = post.subreddit.display_name
    score = post.score
    if post.is_self:
        body = post.selftext
    else:
        body = post.url

    # save data
    c.execute('Insert into submissions VALUES (?, ?, ?, ?, ?, ?)', [submissionID, submissionTitle, body, score,
                                                                    subredditName, subredditID])
    c.connection.commit()


if __name__ == "__main__":


    # handle argument

    # initialize reddit object
    r = praw.Reddit(user_agent='get_dataset')