import praw
from re import sub
from tkinter.messagebox import NO
import praw
import textwrap
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from PIL import ImageDraw, ImageFont, Image, ImageFilter
import numpy as np
from util import human_format
from better_profanity import profanity
import time



class redditScrapper:
    def __init__(self, sub, bgres = 1000):
        print("Initialized")
        self.sub = sub
        self.textWrapLen = 60
        self.imageSize = 1000
        self.textWidth = 1000
        self.textHeight = 38
        self.elementPadding = 10
        self.textLeftPadding = 90
        self.resetBG(bgres)

        self.font = ImageFont.truetype("LucidaSansDemiBold.ttf", 25)
        self.smallFont = ImageFont.truetype("calibrib.ttf", 21)
        
        self.reddit = praw.Reddit(
            client_id="CY6H6O3ng77h5rjiQNpXeg",
            client_secret="n-cxPtR1QezeZGAu8GruZudbAGU4BQ",
            user_agent="com.personalApp:0.0.1 by /u/enguzelharf",
            )


    def resetBG(self, res):
        response = requests.get('https://picsum.photos/' + str(res))
        self.background = Image.open(BytesIO(response.content))
        enhancer = ImageEnhance.Brightness(self.background)
        self.background = enhancer.enhance(0.6)
        
        
    def setHeight(self, text):
        lineCount = len(textwrap.wrap(text, width=self.textWrapLen))
        return max(lineCount, 2)*29 + self.elementPadding*2 + 50

    def addText(self, text, image, textColor = "#ffffff"):
        text = profanity.censor(text)
        draw = ImageDraw.Draw(image)
        
        
        margin = self.textLeftPadding
        offset = self.imageSize/2 - self.textHeight/2 + self.elementPadding
        for line in textwrap.wrap(text, width=self.textWrapLen):
            draw.text((margin, offset), line, textColor, font=self.font)
            offset += self.font.getbbox(line)[3]

    def addCustomText(self, image, text, pos = (0, 0), textColor = "#ffffff", textAnchor = "ms"):
        text = profanity.censor(text)
        draw = ImageDraw.Draw(image)
        draw.text(pos, text, textColor, font=self.smallFont, anchor = textAnchor)

    def blurBox(self, image):

        draw = ImageDraw.Draw(image, "RGBA")
        draw.rectangle((int(self.imageSize/2-self.textWidth/2), 
                        int(self.imageSize/2-self.textHeight/2),
                        int(self.imageSize/2+self.textWidth/2),
                        int(self.imageSize/2+self.textHeight/2)),
                        fill=(0, 0, 0, 80))
        
        # draw.rectangle((int(self.imageSize/2-self.textWidth/2), 
        #                 int(self.imageSize/2-self.textHeight/2),
        #                 int(self.imageSize/2+self.textWidth/2),
        #                 int(self.imageSize/2+self.textHeight/2)),
        #                 fill =(0, 0, 0, 0), outline ="red")

        box =  (
                int(self.imageSize/2-self.textWidth/2), 
                int(self.imageSize/2-self.textHeight/2),
                int(self.imageSize/2+self.textWidth/2),
                int(self.imageSize/2+self.textHeight/2)
                )
        
        ic = image.crop(box)
        for i in range(10):  # with the BLUR filter, you can blur a few times to get the effect you're seeking
            ic = ic.filter(ImageFilter.BLUR)
        image.paste(ic, box)

    def addIcon(self, sub, image, posY, foundImage = None):
        logo = None
        if(foundImage == None):
            response = requests.get(self.reddit.subreddit(sub).icon_img)
            logo = Image.open(BytesIO(response.content))
        else:
            logo = foundImage
            
        logo = logo.resize((60,60))
        
        # Create same size alpha layer with circle
        alpha = Image.new('L', logo.size,0)
        draw2 = ImageDraw.Draw(alpha)
        draw2.pieslice([0,0,logo.height,logo.width],0,360,fill=255)

        # Convert alpha Image to numpy array
        npAlpha=np.array(alpha)

        # Add alpha layer to RGB
        npImage=np.array(logo)
        npImage=np.dstack((npImage,npAlpha))

        image.paste(Image.fromarray(npImage), (self.elementPadding, posY), Image.fromarray(npImage))
        
        return logo

    def createImageWithText(self, title, icon = ""):
        bg = self.background.copy()
        self.textHeight = self.setHeight(title)
        self.blurBox(bg)
        self.addText(title, bg)
        
        if(icon != ""):
            self.addIcon(icon, bg, int(self.imageSize/2-self.textHeight/2+self.elementPadding))
            
        bg.show()
        return bg
        
    def getRedditPostAsImage(self, filter = "day", postCount = 1, commentCount = 4, saveOnCreate = False):
        listOfImages = []  
        for submission in self.reddit.subreddit(self.sub).top(time_filter=filter, limit=postCount):
            self.resetBG(self.imageSize)
            title = submission.title
            bg = self.background.copy()
            self.textHeight = self.setHeight(title)
            self.blurBox(bg)
            self.addText(title, bg)
            icon = self.addIcon(self.sub, bg, int(self.imageSize/2-self.textHeight/2+self.elementPadding))
            self.addCustomText(bg, human_format(submission.score), (self.elementPadding + 30, int(self.imageSize/2-self.textHeight/2+self.elementPadding + 85)), "#fa6505")
            self.addCustomText(bg, "/u/" + submission.author.name, (self.imageSize - self.elementPadding, int(self.imageSize/2+self.textHeight/2-self.elementPadding)), "#ffffff", textAnchor = "rs")
            self.addCustomText(bg, human_format(submission.num_comments), (self.elementPadding + 30, int(self.imageSize/2-self.textHeight/2+self.elementPadding + 110)), "#39ceff")
            
            
            if(saveOnCreate):
                bg.save("outputs/" + str(int(round(time.time() * 1000))) + " - " +  submission.author.name + ".jpg")
            else:
                listOfImages.append(bg)
            print(submission.author.name + " is finished!")
            
            for count, comment in enumerate(submission.comments):
                if(commentCount == count):
                    break
                
                print(comment.body)
                commentBody = comment.body
                commentImage = self.background.copy()                
                
                self.textHeight = self.setHeight(commentBody)
                self.blurBox(commentImage)
                self.addText(commentBody, commentImage, "#ffffff")
                self.addCustomText(commentImage, human_format(comment.score), (self.elementPadding + 30, int(self.imageSize/2-self.textHeight/2+self.elementPadding + 85)), "#fa6505")
                self.addCustomText(commentImage, "/u/" + comment.author.name if comment.author else "[deleted]", (self.imageSize - self.elementPadding, int(self.imageSize/2+self.textHeight/2-self.elementPadding)), "#ffffff", textAnchor = "rs")
                self.addIcon(self.sub, commentImage, int(self.imageSize/2-self.textHeight/2+self.elementPadding), icon)
                
                if(saveOnCreate):
                    commentImage.save("outputs/" + str(int(round(time.time() * 1000))) + " - " +  submission.author.name + ".jpg")
                else:
                    listOfImages.append(commentImage)
            
        return listOfImages