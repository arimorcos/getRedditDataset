__author__ = 'arimorcos'

import praw
from redditDataset import *


if __name__ == '__main__':

    r = praw.Reddit(user_agent='test')
    sub = getSubreddits(r, ['funny'])
    createDataset(r, sub, startDate='140101000000', endDate='140102000000', dbName='test')
