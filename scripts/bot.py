from reddit import redditScrapper

app = redditScrapper("askreddit")
app.getRedditPostAsImage(postCount=1, commentCount=8, filter="week", isTesting=True, saveOnCreate=True)
# app.getPostFromLink("https://www.reddit.com/r/askscience/comments/wtjdsq/what_would_happen_if_you_poured_a_sunsized_bucket/", saveOnCreate=True)
