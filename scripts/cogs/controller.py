import asyncio
from instagramBot import InstaBot
import traceback
import io
import time
import discord
import validators
from discord.ext import commands, tasks
from reddit import redditScrapper

class Settings:
    def __init__(self):
        self.defaultCaption = "#reddit"
        self.commentAmount = 8
        self.linkCommentCount = 8
        self.printerDailyDelta = 60 * 5
        self.printerWeeklyDelta = 60 * 60 * 24 * 7
        self.digestDelta = 60 * 60 * 8
        self.subs = ["askreddit", "askmen", 
                     "explainlikeimfive", "tooafraidtoask", 
                     "jokes", "showerthoughts", "tifu"]
        self.mode = len(self.subs) - 1

    def getSub(self):
        self.mode += 1
        self.mode = self.mode % len(self.subs)
        return self.subs[self.mode]


settings = Settings()
instaBot = InstaBot()


class Controller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.general = 1008439697678287010
        self.upcoming = 1008464497574428803
        self.posted = 1008812515339276430
        self.deleted = 1008812540744192120
        self.links = 1009948563226247238

        self.reddit = redditScrapper(settings.getSub())
        self.dailyPrinter.start()
        self.digester.start()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")

    async def cog_command_error(self, ctx, error):
        await ctx.send(f"An error occurred in the Test cog: {error}")

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
        
    @commands.command(name="removesub")
    async def removesub(self, ctx, sub):
        settings.subs.remove(sub)
        await ctx.channel.send(f"New sub list is {settings.subs}")
        
    @commands.command(name="nextsub")
    async def nextsub(self, ctx):
        await ctx.channel.send(f"Next sub is - {settings.subs[(settings.mode + 1) % len(settings.subs) - 1]}")
        
    @commands.command(name="printnow")
    async def printnow(self, ctx, time):
        await ctx.message.add_reaction("⏳")
        await self.printerMain(time)
        await ctx.message.add_reaction("✅")
        
    @commands.command(name="printnowsub")
    async def printnowsub(self, ctx, time, sub):
        await ctx.message.add_reaction("⏳")
        settings.mode = settings.mode.index(sub)
        await self.printerMain(time)
        await ctx.message.add_reaction("✅")
        
    @commands.command(name="digestnow")
    async def digestnow(self, ctx):
        await self.digester()
        
    @commands.command(name="printertime")
    async def printertime(self, ctx, seconds):
        settings.printerDailyDelta = int(seconds)
        self.dailyPrinter.change_interval(seconds=settings.printerDailyDelta)
        await ctx.message.add_reaction("✅")
        
    @commands.command(name="digesttime")
    async def digesttime(self, ctx, seconds):
        settings.digestDelta = int(seconds)
        self.digester.change_interval(seconds=settings.digestDelta)
        await ctx.message.add_reaction("✅")
        
    @commands.command(name="showsettings")
    async def showsettings(self, ctx):
        await ctx.channel.send(vars(settings))
        
    @commands.command(name="commentcount")
    async def commentcount(self, ctx, count):
        settings.commentAmount = count
        settings.linkCommentCount = count
        await ctx.message.add_reaction("✅")

    @commands.command()
    async def purge(self, ctx):
        await ctx.channel.purge()

    def subredditPrinter(self, filter):
        postArr = self.reddit.getRedditPostAsImage(postCount=1, commentCount=settings.commentAmount, filter=filter, isTesting=False)
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

    @tasks.loop(seconds=settings.printerDailyDelta)
    async def dailyPrinter(self):
        await self.printerMain("day")
        
    @tasks.loop(seconds=settings.printerWeeklyDelta)
    async def weeklyPrinter(self):
        await self.printerMain("week")

    async def printerMain(self, time):
        try:
            view = UpcomingView(self)
            print("------- Creating Images -------")

            postArr, listOfImgs = await asyncio.to_thread(self.subredditPrinter, time)
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
                instaBot.uploadAlbum(files, hash(toDigest.content), toDigest.content +  settings.defaultCaption)
                
                # To add the url for the post itself.
                # view.add_item(discord.ui.Button(label="Post", style=discord.ButtonStyle.link, url=url))
                
                await toDigest.add_reaction("✅")
                await toDigest.delete()
            else:
                await self.bot.get_channel(self.general).send(f"{time.ctime()} - Nothing do digest 💤💤💤")
                
        except Exception as e:
            await self.bot.get_channel(self.general).send(f"{time.ctime()} - Digest failed - 😥 \n {e}")
            print(traceback.format_exc())

    @weeklyPrinter.before_loop
    async def before_weeklyPrinter(self):
        await asyncio.sleep(settings.printerWeeklyDelta)
        await self.bot.wait_until_ready()
        
    @dailyPrinter.before_loop
    async def before_printer(self):
        await asyncio.sleep(settings.printerDailyDelta)
        await self.bot.wait_until_ready()
    
    @digester.before_loop
    async def before_digester(self):
        await asyncio.sleep(settings.digestDelta)
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
        except Exception as e:
            await self.other.bot.get_channel(1008439697678287010).send(e)
            print(traceback.format_exc())
            

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(view=self)

            await interaction.message.delete()
        except Exception as e:
            await self.other.bot.get_channel(1008439697678287010).send(e)
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
