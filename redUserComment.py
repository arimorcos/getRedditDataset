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
    file_object.write(str(lastCommentTime))

    # close
    file_object.close()


def checkComment(userToCheck, userToNotify):
    # initialize reddit object
    redditObject = praw.Reddit(user_agent="findUserComments")

    # get most recent user comment
    lastComment = getMostRecentComment(userToCheck, redditObject)

    # get home directory
    homePath = os.path.expanduser('~')

    # construct file name
    fileName = os.path.join(homePath, userToCheck) + '.txt'

    if os.path.isfile(fileName):
        # load last saved comment date
        lastCommentDate = loadLastComment(fileName)

        # compare to current last comment date
        if lastCommentDate != lastComment.created:
            # send reddit message
            redditObject.set_oauth_app_info(client_id='6z02joDBya9uHA',
                                            client_secret='VW_eorxVV9QBuxjeQmYxdRU0tC8',
                                            redirect_uri='http://127.0.0.1:65010/authorize_callback')
            access_information = redditObject.get_access_information('pOg4o0YTvTcnwsFXEowb10NZM40')
            redditObject.set_access_credentials(**access_information)
            redditObject.send_message(userToNotify, 'New comment found for ' + userToCheck,
                                      'The following comment has been found for user: ' + userToCheck + '\n\n' +
                                      lastComment.body)

            print('sending message')

            # save new date
            saveLastComment(fileName, lastComment.created)

    else:
        # save new date
        saveLastComment(fileName, lastComment.created)

        # send reddit message
        redditObject.set_oauth_app_info(client_id='6z02joDBya9uHA',
                                        client_secret='VW_eorxVV9QBuxjeQmYxdRU0tC8',
                                        redirect_uri='http://127.0.0.1:65010/authorize_callback')
        access_information = redditObject.get_access_information('pOg4o0YTvTcnwsFXEowb10NZM40')
        redditObject.set_access_credentials(**access_information)
        redditObject.send_message(userToNotify, 'New comment found for ' + userToCheck,
                                  'The following comment has been found for user: ' + userToCheck + '\n\n' +
                                  lastComment.body)

        print('sending message')


if __name__ == "__main__":

    # handle argument
    userToCheck = sys.argv[1]

    checkComment(userToCheck)