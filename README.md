# getRedditDataset
This repository uses PRAW to create custom datasets from reddit. 

## PRAW/Reddit API Basics ##

This isn't intended as a tutorial for PRAW. If you want that, I recommend visiting their [docs](https://praw.readthedocs.org/en/v2.1.20/ "PRAW documentation"). This section will only go through the fundamentals of PRAW necessary to create a data set from reddit. 

First, let's import praw and the redditDataset module
	
	import praw
	import redditDataset

Next, let's initialize a connection with PRAW as follows: 

    redditObject = praw.Reddit(user_agent='get_reddit_dataset')

We can grab subreddits using `getSubreddits`. Here, we'll grab /r/funny and /r/gaming
	
	subreddits = redditDataset.getSubreddits(redditObject, ['funny', 'gaming'])

PRAW also has a variety of functions to grab subreddits. One of the most useful is the method `get_popular_subreddits`.
	
	popularSubreddits = redditObject.get_popular_subreddits(limit=200)

This will return a generator containing the 200 most popular subreddits. PRAW has many other methods to grab specific submissions, comments, users, etc., but these are the only ones you'll need to know to use the module. 

Now that we have a reddit object and the subreddits to query, let's make a data set. 

## Grabbing a data set from a set of subreddits ##

Once you have a generator or list of subreddit objects and your praw object, call `createDataset` to start downloading comments and posts into a sqlite3 database. The database will be saved in `~\Databases\<dbName>db`.

Let's grab all the posts from the funny subreddit from March 1, 2015: 

	funnySubreddit = redditDataset.getSubreddits(redditObject, ['funny'])
    redditDataset.createDataset(redditObject, funnySubreddit, startDate='150301000000'
								endDate='150301115959', dbName='March_01_2015_funny_posts'
								fineScale=4)

Basically, you give `createDataset` the reddit object, the subreddits (in list or generator form), a start and end date, a base name for the database, and a fine scale (which I'll get to in a moment). 

For the start and end date, provide a string in the format 'yymmddHHMMSS'. So, in the above example, we're pulling posts between March 1, 2015 at 12:00:00 AM and March 1, 2015 at 11:59:59 PM. 

Unfortunately, the reddit API will only provide a list of 1000 posts for any query. What does this mean for us? Well, say we want to get all the posts from 2014. If we request all those posts, we'll only get the 1000 with whatever sort is specified (`createDataset` uses a 'top' sort). To get around this, `createDataset` will make many requests in increments of 'fineScale' hours. So, in the example, above, we'll actually make six separate queries for a theoretical maximum of 6,000 posts. Because of the overhead associated with getting posts, we want to set this parameter to be as large as possible while still getting all the data we want. I've found that 8 works well for all but the most frequented subreddits. 

And that's it! It'll work to retrieve all the posts within the desired range and the top comments from each post (by default, this is set to 100). One thing to note: because of the reddit API limits, this process is slow. We can only make 30 requests per minute. Currently, we only get the data for one post per request. I think this can be improved (potentially up to 25 posts per request), but I haven't gotten around to it yet.   

## Database structure ##

The sql database is pretty simple. It has two tables: `submissions` and `comments`. 

Each row in `submissions` represents a single post. The columns contain the `postID`, `postTitle`, `postBody` (text if a self-post, url if a link), `postScore` (as of when it was downloaded), `subredditName`, and `subredditID`. 

Each row in `comments` represents a single comment in a post. The columns contain the `commentDate`, `user`, `body`, `comScore` (as of when it was downloaded), and the `postID`. 
