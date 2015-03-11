__author__ = 'Ari Morcos'

import os
import datetime
import sqlite3


class RedditDB:
    """
    Class for interfacing with a database for reddit data sets
    """

    def __init__(self, dbName='reddit'):
        self.__dbName = dbName
        self.__c = None  # initialized in initialize database
        self.__initializeDatabase()

    def __getDatabasePath(self):
        """
        :return: full absolute database path
        """
        userPath = os.path.expanduser('~')
        basePath = os.path.abspath(os.path.join(userPath, 'Databases'))
        databasePath = os.path.abspath(os.path.join(basePath, self.__dbName + '.db'))

        # make directory if it doesn't exist
        if not os.path.exists(basePath):
            os.makedirs(basePath)
        return databasePath

    def __initializeDatabase(self):
        """
        Initializes a database connection called 'reddit.db'
        :return: cursor object
        """

        dbPath = self.__getDatabasePath()
        dbObj = sqlite3.connect(dbPath)
        self.__c = dbObj.cursor()

        # get list of tables
        tableList = self.__c.execute("Select name from sqlite_master where type = 'table' ")

        # check if comments exist in tableList
        commentsPresent = any(['comments' == item[0] for item in [row for row in list(tableList)]])

        if not commentsPresent:
            self.__createTables()

    def __createTables(self):
        # create comments table
        self.__c.execute('Create TABLE comments (date, user, body, comScore, postID)')

        # create submissions table
        self.__c.execute('Create TABLE submissions (postID, postTitle, postBody, postScore, postDate, '
                         'subredditName, subredditID)')

    def saveCommentData(self, comment):
        """
        :param comment: comment object
        :return: void
        """

        # extract relevant fields
        commentDate = datetime.datetime.fromtimestamp(comment.created_utc)
        commentDateStr = commentDate.strftime('%Y%m%d%H%M%S')
        userName = comment.author.name
        body = comment.body
        submissionID = comment._submission.name
        score = comment.score

        # save data
        self.__c.execute('Insert into comments VALUES (?, ?, ?, ?, ?)', [commentDateStr, userName, body, score, submissionID])
        self.__c.connection.commit()

    def saveSubmission(self, post):
        """
        :param post: post object
        :return: void
        """

        # extract relevant fields
        submissionID = post.name
        submissionTitle = post.title
        submissionDate = datetime.datetime.fromtimestamp(post.created_utc)
        submissionDateStr = submissionDate.strftime('%Y%m%d%H%M%S')
        subredditID = post.subreddit.name
        subredditName = post.subreddit.display_name
        score = post.score
        if post.is_self:
            body = post.selftext
        else:
            body = post.url

        # save data
        self.__c.execute('Insert into submissions VALUES (?, ?, ?, ?, ?, ?, ?)', [submissionID, submissionTitle, body,
                                                                                  score, submissionDateStr,
                                                                                  subredditName, subredditID])
        self.__c.connection.commit()