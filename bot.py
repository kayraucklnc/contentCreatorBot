from reddit import redditScrapper
import lorem

app = redditScrapper("askreddit")
app.getRedditPostAsImage(postCount=4, commentCount=1, filter="all", saveOnCreate = True)