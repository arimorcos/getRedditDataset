__author__ = 'Ari Morcos'

import praw
import datetime


def createDataset(subreddits, startDate=( datetime.datetime.now() - datetime.timedelta( weeks=1 ) ),
                  endDate=datetime.datetime.now(), nSubReddits=500):

    # create reddit object
    r = praw.Reddit(user_agent='get_dataset')






if __name__ == "__main__":

    # handle argument