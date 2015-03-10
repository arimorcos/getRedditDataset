__author__ = 'arimorcos'

import praw
from redditDataset import *


if __name__ == '__main__':

    r = praw.Reddit(user_agent='test')
    sub = getSubreddits(r, ['funny'])
    sub = sub.next()
    posts = getAllPostsWithinRangeFineScale(sub, '140101', '140104', fineScale=24)
