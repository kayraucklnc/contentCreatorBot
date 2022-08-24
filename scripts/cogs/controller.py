import asyncio
import signal
from instagramBot import InstaBot
import traceback
import io
import time
import discord
import validators
from discord.ext import commands, tasks
from reddit import redditScrapper
import sys
import json

dataBase = dict()
try:
    with open('databse.json') as infile:
        data = json.load(infile)
except:
    pass


def signal_handler(signal, frame):
    with open('databse.json', 'w') as outfile:
        json.dump(dataBase, outfile)
    print ('Dumped to file')
    sys.exit(0)
    sys.pause()

signal.signal(signal.SIGINT, signal_handler)

class Settings:
    def __init__(self):
        self.defaultCaption = "#reddit"
        self.commentAmount = 1
        self.linkCommentCount = 0
        self.printerDelta = 60 * 5
        self.digestDelta = 60 * 60 * 8
        self.filterTime = "day"
        self.subs = ["askreddit", "askmen", 
                     "explainlikeimfive", "tooafraidtoask", 
                     "jokes", "showerthoughts", "crazyideas"]
        self.mode = len(self.subs) - 1

    def getSub(self):
        self.mode += 1
        self.mode = self.mode % len(self.subs)
        return self.subs[self.mode]


settings = Settings()
# instaBot = InstaBot()


class Controller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.general = 1008439697678287010
        self.upcoming = 1008464497574428803
        self.posted = 1008812515339276430
        self.deleted = 1008812540744192120
        self.links = 1009948563226247238

        self.reddit = redditScrapper(settings.getSub())
        # self.dailyPrinter.start()
        # self.digester.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")

    @commands.Cog.listener()
    async def on_message(self, ctx):
        if not ctx.author.bot:
            if ctx.channel.id == self.links:
                await self.linkSent(ctx)

    @commands.command(name="showsubs")
    async def showsubs(self, ctx):
        await ctx.channel.send(f"Sub list is {settings.subs}")
        
    @commands.command(name="addsub")
    async def addsub(self, ctx, sub):
        settings.subs.append(sub)
        await ctx.channel.send(f"New sub list is {settings.subs}")
        
    @commands.command(name="nextsub")
    async def nextsub(self, ctx):
        await ctx.channel.send(f"Next sub is - {settings.subs[(settings.mode + 1) % len(settings.subs) - 1]}")
        
    @commands.command(name="printnow")
    async def printnow(self, ctx):
        await self.dailyPrinter()


    @commands.command()
    async def purge(self, ctx):
        await ctx.channel.purge()

    def subredditPrinter(self):
        postArr = self.reddit.getRedditPostAsImage(postCount=1, commentCount=settings.commentAmount,
                                                   filter=settings.filterTime, isTesting=False)
        self.reddit.changeSub(settings.getSub())

        listOfImgs = self.arrToListOFImages(postArr)

        return postArr, listOfImgs
    
    def onePostPrinter(self, link):
        postArr = self.reddit.getPostFromLink(link, commentCount=settings.linkCommentCount)
        self.reddit.changeSub(settings.getSub())
        listOfImgs = self.arrToListOFImages(postArr)
        return postArr, listOfImgs

    def arrToListOFImages(self, postArr):
        print("Sending Images now!")
        listOfImgs = []
        for post in postArr:
            with io.BytesIO() as image_binary:
                post.img.save(image_binary, 'PNG')
                image_binary.seek(0)
                listOfImgs.append(discord.File(fp=image_binary, filename=f'{post.title}.png'))
        return listOfImgs

    @tasks.loop(seconds=settings.printerDelta)
    async def dailyPrinter(self):
        try:
            view = UpcomingView(self)
            print("------- Creating Images -------")

            postArr, listOfImgs = await asyncio.to_thread(self.subredditPrinter)
            view.add_item(discord.ui.Button(label="Post", style=discord.ButtonStyle.link, url=postArr[0].url))

            await self.bot.get_channel(self.upcoming).send(postArr[0].title, files=listOfImgs, view=view)
            print("Images sent")

        except Exception as e:
            await self.bot.get_channel(self.general).send(f"Failed 😥  ```{e}```")
            print(traceback.format_exc())
            
    @tasks.loop(seconds=settings.digestDelta)
    async def digester(self):
        # SHOULD DISABLE BUTTONS BEFORE DIGESTING
        try:
            view = PostedView()
            toDigest = [i async for i in self.bot.get_channel(self.upcoming).history(limit=1)]

            if len(toDigest) > 0 and len(toDigest[0].attachments) > 0:
                toDigest = toDigest[0]
                await toDigest.add_reaction("⏳")
                
                files = [await f.to_file() for f in toDigest.attachments]

                await self.bot.get_channel(self.posted).send(toDigest.content, files=files, view=view)
                # instaBot.uploadAlbum(files, hash(toDigest.content), toDigest.content +  settings.defaultCaption)
                
                # To add the url for the post itself.
                # view.add_item(discord.ui.Button(label="Post", style=discord.ButtonStyle.link, url=url))
                
                await toDigest.add_reaction("✅")
                await toDigest.delete()
            else:
                await self.bot.get_channel(self.general).send(f"{time.ctime()} - Nothing do digest 💤💤💤")
                
        except Exception as e:
            await self.bot.get_channel(self.general).send(f"{time.ctime()} - Digest failed - 😥 \n {e}")
            print(traceback.format_exc())

    @dailyPrinter.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
    
    @digester.before_loop
    async def before_digester(self):
        await self.bot.wait_until_ready()

    async def linkSent(self, ctx):
        if validators.url(ctx.content):
            try:
                await ctx.add_reaction("⏳")
                view = UpcomingView(self)
                print("------- Creating Images -------")
                
                postArr, listOfImgs = await asyncio.to_thread(self.onePostPrinter, ctx.content)
                view.add_item(discord.ui.Button(label="Post", style=discord.ButtonStyle.link, url=postArr[0].url))
                await self.bot.get_channel(self.upcoming).send(postArr[0].title, files=listOfImgs, view=view)
                
                print("Images sent")
                
                await ctx.add_reaction("👍")
                await ctx.clear_reaction("⏳")
            except Exception as e:
                await self.bot.get_channel(self.general).send(f"Failed 😥  ```{e}```")
                print(traceback.format_exc())
        else:
            await ctx.delete()
            


class UpcomingView(discord.ui.View):
    def __init__(self, other):
        self.other = other
        self.postedView = PostedView()
        super().__init__()

    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)

            files = [await f.to_file() for f in interaction.message.attachments]
            content = interaction.message.content
            await interaction.message.delete()
            await self.other.bot.get_channel(1008812515339276430).send(content, files=files, view=self.postedView)
            
            instaBot.uploadAlbum(files, hash(interaction.message.content), interaction.message.content + settings.defaultCaption)
        except:
            print(traceback.format_exc())
            

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)

            await interaction.message.delete()
        except:
            print(traceback.format_exc())


class PostedView(discord.ui.View):
    @discord.ui.button(label='Delete Post', style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.bot.get_channel(1008812540744192120).send(interaction.message.content,
                                                             files=[await f.to_file() for f in
                                                                    interaction.message.attachments])

        await interaction.response.defer()
        await interaction.message.delete()

        instaBot.deleteAlbum(interaction.message.content, "caption")


async def setup(bot):
    await bot.add_cog(Controller(bot))
