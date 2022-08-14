from reddit import redditScrapper

app = redditScrapper("askreddit")
for i, k in enumerate(app.getRedditPostAsImage(postCount=3, commentCount=3, filter="month")):
    k.save("outputs/" + str(i) + ".jpg")

