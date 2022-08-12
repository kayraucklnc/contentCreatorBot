import praw
import textwrap
from PIL import Image, ImageEnhance
import requests
from io import BytesIO
from PIL import ImageDraw, ImageFont, Image, ImageFilter
import numpy as np


class redditScrapper:
    def __init__(self):
        print("Initialized")
        self.sub = "UnethicalLifeProTips"
        self.textWrapLen = 65
        self.imageSize = 1000
        self.textWidth = 1000
        self.textHeight = 38
        self.elementPadding = 10
        self.textLeftPadding = 90

        self.font = ImageFont.truetype("LucidaSansDemiBold.ttf", 25)
        self.reddit = praw.Reddit(
            client_id="CY6H6O3ng77h5rjiQNpXeg",
            client_secret="n-cxPtR1QezeZGAu8GruZudbAGU4BQ",
            user_agent="com.personalApp:0.0.1 by /u/enguzelharf",
            )

    def setHeight(self, text):
        lineCount = len(textwrap.wrap(text, width=self.textWrapLen))
        return max(lineCount, 2)*29 + self.elementPadding*2

    def addText(self, text, image):
        draw = ImageDraw.Draw(image)
        
        
        margin = self.textLeftPadding
        offset = self.imageSize/2 - self.textHeight/2 + self.elementPadding
        for line in textwrap.wrap(text, width=self.textWrapLen):
            draw.text((margin, offset), line, (255,255,255), font=self.font)
            offset += self.font.getbbox(line)[3]

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

        box = (int(self.imageSize/2-self.textWidth/2), int(self.imageSize/2-self.textHeight/2), int(self.imageSize/2+self.textWidth/2), int(self.imageSize/2+self.textHeight/2))
        ic = image.crop(box)
        for i in range(10):  # with the BLUR filter, you can blur a few times to get the effect you're seeking
            ic = ic.filter(ImageFilter.BLUR)
        image.paste(ic, box)

    def addIcon(self, sub, image, posY):
        try:
            response = requests.get(self.reddit.subreddit(sub).icon_img)
            logo = Image.open(BytesIO(response.content))
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
        except:
            print("No img")

    def getRedditPostAsImage(self):    
        response = requests.get('https://picsum.photos/1000')
        background = Image.open(BytesIO(response.content))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)
        
        
        for submission in self.reddit.subreddit(self.sub).top(time_filter="day", limit=1):
            title = submission.title

            bg = background.copy()
            self.textHeight = self.setHeight(title)
            self.blurBox(bg)
            self.addText(title, bg)
            self.addIcon(self.sub, bg, int(self.imageSize/2-self.textHeight/2+self.elementPadding))
            # bg = bg.resize((300,300))

            # bg.save("outputs/" + submission.author.name + ".jpg")
            bg.show()
            print(submission.author.name + " is finished!")
            return bg