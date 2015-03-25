__author__ = 'Ari Morcos'

import os
import datetime
import sqlite3
import re
import shutil
import time


class RedditDB:
    """
    Class for interfacing with a database for reddit data sets
    """

    def __init__(self, dbName='reddit', dbPath=None):
        self.__dbName = dbName
        self.__dbPath = dbPath
        self.__c = None  # initialized in initialize database
        self.__initializeDatabase()

    def __getDatabasePath(self):
        """
        :return: full absolute database path
        """

        if self.__dbPath is None:
            userPath = os.path.expanduser('~')
            basePath = os.path.abspath(os.path.join(userPath, 'Databases'))
        else:
            basePath = self.__dbPath

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
        self.__dbObj = sqlite3.connect(dbPath)
        self.__c = self.__dbObj.cursor()

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

    def getSubreddits(self):
        """ Extracts a list of distinct subreddits """

        # execute query
        self.__c.execute('select distinct subredditName '
                         'from submissions '
                         'group by subredditName '
                         'order by count(*) desc')

        # grab results
        rawOut = self.__c.fetchall()

        return [item[0] for item in rawOut]

    def getSubredditCommentText(self, subreddit):
        """ Grabs all comment text and concatenates from a given subreddit """

        # execute query
        self.__c.execute("select body "
                         "from comments "
                         "where postID in "
                         "  (select postID "
                         "   from submissions "
                         "   where subredditName = ?)", [subreddit])

        # get comments
        rawComments = self.__c.fetchall()

        return [item[0] for item in rawComments]

    def closeConnection(self):
        self.__dbObj.close()


def mergeDBs(path, dbName='mergedDB'):
    """
    Merges multiple databases into one large database
    :param path: path to folder containing databases. Will merge all of these databases
    :param dbName: Name of the merged database. Default is mergedDB.
    """

    # get list of database objects in path
    allFiles = os.listdir(path)

    # get db files
    dbFiles = [dbFile for dbFile in allFiles if re.match(r'.*\.db', dbFile) is not None]

    # get path of first file and new database object
    source = os.path.abspath(os.path.join(path, dbFiles[0]))
    destination = os.path.abspath(os.path.join(path, dbName + '.db'))

    # check if destination file exists
    if os.path.isfile(destination):
        userInput = raw_input('Destination file already exists. Continue (y/n): ')
        if userInput.lower() == 'n':
            print('Ending merge.')
            return
        elif userInput.lower() != 'y':
            print 'Cannot process input. Ending merge.'
            return

    # copy file
    shutil.copyfile(source, destination)

    # create sql object
    dbObj = sqlite3.connect(destination)
    c = dbObj.cursor()

    # loop through each database, attach, and merge
    for dbFile in dbFiles[1:]:

        # create query
        sqlQuery = "attach '" + os.path.abspath(os.path.join(path, dbFile)) + """' as toMerge;
                    INSERT into comments select * from toMerge.comments;
                    INSERT into submissions select * from toMerge.submissions;
                    detach toMerge;"""

        # execute and commit
        c.executescript(sqlQuery)
        dbObj.commit()

    print 'Merge complete!'


