from pickle import TRUE
from reddit import redditScrapper

app = redditScrapper("askreddit")
app.getRedditPostAsImage(postCount=1, commentCount=3, filter="week", isTesting=False, saveOnCreate=True)