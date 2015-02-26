__author__ = 'arimorcos'
import praw
import sys
import os


def getMostRecentComment(userName, redditObject):

    userObject = redditObject.get_redditor(userName)

    userComments = userObject.get_comments()

    comment = None
    for comment in userComments:
        pass

    return comment


def loadLastComment(saveFile):

    # open file
    file_object = open(saveFile, 'r')

    # read in whole file and return
    lastCommentDate = file_object.read()

    # close file
    file_object.close()

    # return
    return lastCommentDate


def saveLastComment(saveFile, lastCommentTime):

    # open file
    file_object = open(saveFile, 'w')

    # read in whole file and return
    file_object.write(lastCommentTime)

    # close
    file_object.close()


if __name__ == "__main__":

    # handle argument
    userName = sys.argv[1]

    # initialize reddit object
    redditObject = praw.Reddit(user_agent="findUserComments")

    # get most recent user comment
    lastComment = getMostRecentComment(userName, redditObject)

    # get home directory
    homePath = os.path.expanduser('~')

    # construct file name
    fileName = os.path.join(homePath, userName) + '.txt'

    if os.path.isfile(fileName):
        # load last saved comment date
        lastCommentDate = loadLastComment(fileName)

        # compare to current last comment date
        if lastCommentDate == lastComment.created:
            # email

            # save new date
            saveLastComment(fileName, lastComment.created)

    else:
        # save new date
        saveLastComment(fileName, lastComment.created)