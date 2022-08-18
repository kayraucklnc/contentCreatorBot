from reddit import redditScrapper

app = redditScrapper("unethicallifeprotips")
app.getRedditPostAsImage(postCount=1, commentCount=0, filter="week", isTesting=True)[0].img.show()