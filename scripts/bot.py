from pickle import TRUE
from reddit import redditScrapper

app = redditScrapper("yraam")
app.getRedditPostAsImage(postCount=1, commentCount=0, filter="week", isTesting=True)[0].img.show()