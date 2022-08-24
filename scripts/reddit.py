import praw
import re
import textwrap
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from PIL import ImageDraw, ImageFont, Image, ImageFilter, ImageChops
import numpy as np
from util import human_format
from better_profanity import profanity
import time
import lorem
from dotenv import load_dotenv
import os


class TestSubmission:
    class author:
        def __init__(self):
            self.name = "TestAuthor"
            
    class Comment:
        def __init__(self):
            self.author = TestSubmission.author()
            self.body = self.selftext = " ".join([lorem.paragraph() for i in range(1)])
            self.stickied = False
            self.score = 60000
            
    def __init__(self):
        self.title = " ".join([lorem.paragraph() for i in range(1)])
        self.selftext = " ".join([lorem.paragraph() for i in range(1)])

        # self.title = 10 * "a"
        # self.selftext = 0 * "a"

        self.num_comments = 3600
        self.score = 25000
        self.author = TestSubmission.author()
        self.comments =[TestSubmission.Comment() for i in range(8)]
        self.icon_img = "./assets/reddit.png"
        self.url = "https://www.reddit.com/r/AskReddit/"


class PostSubmission:
    def __init__(self, title, author, img, icon_img, url, id, isPost=True):
        self.title = title
        self.author = author
        self.img = img
        self.icon_img = icon_img
        self.isPost = isPost
        self.url = url
        self.id = id


class redditScrapper:
    def __init__(self, sub, bgres=1000):
        print("Initialized")
        self.sub = sub
        self.gildMinAmount = 80
        self.textWrapLen = 58
        self.pageLength = 1300
        self.imageSize = 1000
        self.textWidth = 1000
        self.textHeight = 38
        self.elementPadding = 10
        self.textLeftPadding = 90
        self.resetBG(bgres)
        self.urlPattern = re.compile('\[(.*?)\]\(.*?\)')

        self.font = ImageFont.truetype("LucidaSansDemiBold.ttf", 25)
        self.mediumFont = ImageFont.truetype("calibrib.ttf", 26)
        self.smallFont = ImageFont.truetype("calibrib.ttf", 21)

        self.reddit = praw.Reddit(
            client_id=os.getenv('client_id'),
            client_secret=os.getenv('client_secret'),
            user_agent=os.getenv('user_agent'),
            check_for_async=False)

    def getPostFromLink(self, link, commentCount=4, saveOnCreate=False):
        listOfPosts = []
        print("Gather Post Started")    
        submission = praw.models.Submission(reddit=self.reddit, url=link)
        subredditHelper = submission.subreddit
        subIconPath = subredditHelper.icon_img

        self.fillArrayFromSubmission(listOfPosts, submission, commentCount, True, saveOnCreate, subIconPath)

        return listOfPosts

    def changeSub(self, sub):
        self.sub = sub

    def resetBG(self, res):
        # response = requests.get('https://picsum.photos/' + str(res))
        # response = requests.get(f"https://picsum.photos/{res}/{res}")
        # self.background = Image.open(BytesIO(response.content))
        self.background = Image.open("./outputs/pic.jpg")
        enhancer = ImageEnhance.Brightness(self.background)
        self.background = enhancer.enhance(0.6)

    def setHeight(self, text, content=None):
        content = content if content else ""
        lineCount = len(textwrap.wrap(text + content, width=self.textWrapLen))
        return max(lineCount + 4, 2) * 29 + self.elementPadding

    def addTitleContent(self, text, image, textColor="#ffffff", content=None, isHeadEmpty=True):
        draw = ImageDraw.Draw(image)

        margin = self.textLeftPadding
        offset = self.imageSize / 2 - self.textHeight / 2 + self.elementPadding + (29 if isHeadEmpty else 0)
        for line in textwrap.wrap(text, width=self.textWrapLen):
            draw.text((margin, offset), line, textColor, font=self.font)
            offset += self.font.getbbox(line)[3]

        if (content):
            for line in textwrap.wrap(content, width=self.textWrapLen):
                draw.text((margin, offset + 29), line, "#CBCBCC", font=self.font)
                offset += self.font.getbbox(line)[3]

    def addCustomText(self, image, text, pos=(0, 0), textColor="#ffffff", textAnchor="ms", storoke_fill=None,
                      stroke_width=0):
        text = profanity.censor(text)
        draw = ImageDraw.Draw(image)
        draw.text(pos, text, textColor, font=self.smallFont, anchor=textAnchor)

    def addMediumCustomText(self, image, text, pos=(0, 0), textColor="#ffffff", textAnchor="ms", storoke_fill=None,
                            stroke_width=0):
        text = profanity.censor(text)
        draw = ImageDraw.Draw(image)
        draw.text(pos, text, textColor, font=self.mediumFont, anchor=textAnchor, stroke_fill=storoke_fill,
                  stroke_width=stroke_width)

    def blurBox(self, image, blurAmount=8):

        draw = ImageDraw.Draw(image, "RGBA")
        draw.rectangle((int(self.imageSize / 2 - self.textWidth / 2),
                        int(self.imageSize / 2 - self.textHeight / 2),
                        int(self.imageSize / 2 + self.textWidth / 2),
                        int(self.imageSize / 2 + self.textHeight / 2)),
                       fill=(0, 0, 0, 80))

        # draw.rectangle((int(self.imageSize/2-self.textWidth/2), 
        #                 int(self.imageSize/2-self.textHeight/2),
        #                 int(self.imageSize/2+self.textWidth/2),
        #                 int(self.imageSize/2+self.textHeight/2)),
        #                 fill =(0, 0, 0, 0), outline ="red")

        box = (
            int(self.imageSize / 2 - self.textWidth / 2),
            int(self.imageSize / 2 - self.textHeight / 2),
            int(self.imageSize / 2 + self.textWidth / 2),
            int(self.imageSize / 2 + self.textHeight / 2)
        )

        ic = image.crop(box)
        for i in range(blurAmount):  # with the BLUR filter, you can blur a few times to get the effect you're seeking
            ic = ic.filter(ImageFilter.BLUR)
        image.paste(ic, box)

    def crop_to_circle(self, im):
        bigsize = (im.size[0] * 3, im.size[1] * 3)
        mask = Image.new('L', bigsize, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + bigsize, fill=255)
        mask = mask.resize(im.size, Image.ANTIALIAS)
        mask = ImageChops.darker(mask, im.split()[-1])
        im.putalpha(mask)

    def addIcon(self, iconPath, image, posY, isIconOnUrl):
        logo = None
        if isIconOnUrl:
            response = requests.get(iconPath)
            logo = Image.open(BytesIO(response.content))
        else:
            logo = Image.open(iconPath)

        logo = logo.resize((60, 60))

        logo = logo.convert('RGBA')
        self.crop_to_circle(logo)

        image.paste(logo, (self.elementPadding, posY), logo)

        return logo

    def createImageWithText(self, title, icon="", isIconOnUrl=True):
        bg = self.background.copy()
        self.textHeight = self.setHeight(title)
        self.blurBox(bg)
        self.addTitleContent(title, bg)

        if icon != "":
            self.addIcon(icon, bg, int(self.imageSize / 2 - self.textHeight / 2 + self.elementPadding),
                         isIconOnUrl=isIconOnUrl)

        bg.show()
        return bg

    def isCommentBadCheck(self, comment):
        isRemoved = (comment.body == "[removed]")
        isBot = False if not comment.author else re.search('moderator', comment.author.name, re.IGNORECASE)
        isSticky = comment.stickied

        return isRemoved or isBot or isSticky

    def getRedditPostAsImage(self, filter="day", postCount=1, commentCount=4, saveOnCreate=False, isTesting=False):
        listOfPosts = []
        print("Gather Post Started")
        subredditHelper = None if isTesting else self.reddit.subreddit(self.sub)
        submissionArray = [TestSubmission() for i in range(postCount)] if isTesting else subredditHelper.top(time_filter=filter, limit=postCount)
        subIconPath = TestSubmission().icon_img if (isTesting or (not subredditHelper.icon_img) or (len(subredditHelper.icon_img) == 0)) else subredditHelper.icon_img
        isIconOnUrl = (not (isTesting or (not subredditHelper.icon_img) or (len(subredditHelper.icon_img) == 0)))

        for submission in submissionArray:
            self.fillArrayFromSubmission(listOfPosts, submission, commentCount, isIconOnUrl, saveOnCreate, subIconPath)

        return listOfPosts

    def gildPhoto(self, im, gradient_magnitude=3.5):
        if im.mode != 'RGBA':
            im = im.convert('RGBA')
        width, height = im.size
        gradient = Image.new('L', (width, 1), color=0xFF)
        for x in range(width):
            # gradient.putpixel((width-x-1, 0), 150-x)
            gradient.putpixel((width-x-1, 0), int(150 * (1 - gradient_magnitude * float(x)/width)))
        alpha = gradient.resize(im.size)
        black_im = Image.new('RGBA', (width, height), color=0x03BAFC) # i.e. black
        black_im.putalpha(alpha)
        return Image.alpha_composite(im, black_im)

    def fillArrayFromSubmission(self, listOfPosts, submission, commentCount, isIconOnUrl, saveOnCreate, subIconPath):
        self.resetBG(self.imageSize)
        title = submission.title
        print(title)
        content = submission.selftext
        name = submission.author.name if submission.author is not None else "Unknown"
        pages = textwrap.wrap(content, width=self.pageLength - len(title))
        title = profanity.censor(title)
        title = self.urlPattern.sub(r'\1', title)
        bg = self.background.copy()
        
        self.textHeight = self.setHeight(title, pages[0] if len(pages) > 0 else "")
        self.blurBox(bg)
        
        if submission.score > self.gildMinAmount:
            bg = self.gildPhoto(bg)
        
        
        self.addTitleContent(title, bg, content=pages[0] if len(pages) > 0 else "")
        self.addIconSubScore(bg, isIconOnUrl, name, subIconPath, submission)
        
        if saveOnCreate:
            bg.save("outputs/" + str(
                int(round(time.time() * 100))) + " - " + submission.author.name + " - MAIN " + ".png")
        else:
            listOfPosts.append(PostSubmission(title, name, bg, subIconPath, submission.url, submission.id))
        
        imageCount = 1
            
        # For content that doesn't fit
        if len(pages) > 0:
            for count, page in enumerate(pages[1:]):
                imageCount += 1
                page = profanity.censor(page)
                page = self.urlPattern.sub(r'\1', page)

                bg = self.background.copy()

                self.textHeight = self.setHeight(" ", page)
                self.blurBox(bg)
                if submission.score > self.gildMinAmount:
                    bg = self.gildPhoto(bg)
                
                self.addTitleContent(f"...{count + 1}/{len(pages)}...", bg, content=page)

                self.addIconSubScore(bg, isIconOnUrl, name, subIconPath, submission)

                if saveOnCreate:
                    bg.save(
                        "outputs/" + str(int(round(time.time() * 1000))) + " - " + submission.author.name + ".jpg")
                else:
                    listOfPosts.append(PostSubmission(title, name, bg, subIconPath, submission.url, submission.id))
                    
        for count, comment in enumerate(submission.comments):
            if imageCount > 10:
                break
            
            if commentCount == count:
                break
            
            if self.isCommentBadCheck(comment):
                continue
            
            commentPages = textwrap.wrap(comment.body, width=self.pageLength)  
            if imageCount + len(commentPages) > 10:
                continue
            

            for page in commentPages:
                imageCount += 1
                commentBody = page
                commentBody = profanity.censor(commentBody)
                commentBody = self.urlPattern.sub(r'\1', commentBody)

                commentAuthorName = comment.author.name if comment.author else "[deleted]"
                commentImage = self.background.copy()

                self.textHeight = self.setHeight(commentBody)
                self.blurBox(commentImage)
                if comment.score > self.gildMinAmount:
                    commentImage = self.gildPhoto(commentImage)
                
                self.addTitleContent(commentBody, commentImage, "#e8e8e8", isHeadEmpty=False)
                self.addScoreAuthor(comment, commentAuthorName, commentImage)
                self.addIcon(subIconPath, commentImage,
                            int(self.imageSize / 2 - self.textHeight / 2 + self.elementPadding), isIconOnUrl)

                if saveOnCreate:
                    commentImage.save(
                        "outputs/" + str(int(round(time.time() * 1000))) + " - " + submission.author.name + ".jpg")
                else:
                    listOfPosts.append(PostSubmission(f"{title} - {str(count)}", commentAuthorName, commentImage, subIconPath, submission.id, False))
                    
        print(submission.author.name + "post is finished!")

    def addIconSubScore(self, bg, isIconOnUrl, name, subIconPath, submission):
        self.addIcon(subIconPath, bg, int(self.imageSize / 2 - self.textHeight / 2 + self.elementPadding),isIconOnUrl)
        self.addMediumCustomText(bg, "r/" + self.sub, (self.elementPadding * 3 + 60, int(self.imageSize / 2 - self.textHeight / 2 + self.elementPadding)),"#FF4500", textAnchor="lt", storoke_fill="#000000", stroke_width=2)
        self.addScoreAuthor(submission, name, bg)
        self.addCustomText(bg, human_format(submission.num_comments), (self.elementPadding + 30, int(self.imageSize / 2 - self.textHeight / 2 + self.elementPadding + 110)),"#39ceff")

    def addScoreAuthor(self, comment, commentAuthorName, commentImage):
        self.addCustomText(commentImage, human_format(comment.score), (self.elementPadding + 30, int(self.imageSize / 2 - self.textHeight / 2 + self.elementPadding + 85)),"#fa6505")
        self.addCustomText(commentImage, "/u/" + commentAuthorName, (self.imageSize - self.elementPadding, int(self.imageSize / 2 + self.textHeight / 2 - self.elementPadding)),"#ffffff", textAnchor="rs")
