__author__ = 'Ari Morcos'

from requests import HTTPError
import praw
import sqlite3
import os
import datetime
import time


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
        getRecentSubmissions(subreddit, dateRange)

    # return search result
    return searchResult


def getCommentsFromSubmission(submission, nCommentsPerSubmission):

    # get comment list
    flatComments = praw.helpers.flatten_tree(submission.comments)

    # filter list and return
    return flatComments[:nCommentsPerSubmission]


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