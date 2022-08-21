import asyncio
from instagramBot import InstaBot
import traceback
import io
import time
import discord
from discord.ext import commands, tasks
from reddit import redditScrapper

class Settings:
    def __init__(self):
        self.commentAmount = 2
        self.printerDelta = 60*0.2
        self.digestDelta = 60*100
        self.filterTime = "day"
        self.subs = ["askreddit", "unethicallifeprotips", "askmen", "explainlikeimfive", "tooafraidtoask", "jokes", "showerthoughts", "crazyideas"]
        self.mode = len(self.subs)-1
        
    def getSub(self):
        self.mode += 1
        self.mode = self.mode % len(self.subs)
        return self.subs[self.mode]

settings = Settings()
settings.mode = 0
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
        # self.printer.start()
        # self.digester.start()


    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")

    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if(not ctx.author.bot):
            await ctx.add_reaction("👍")

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.channel.send("Pong!")                  
        
    @commands.command()
    async def purge(self, ctx):
        await ctx.channel.purge()
        
    def printerWrapper(self): 
        postArr = self.reddit.getRedditPostAsImage(postCount=1, commentCount=settings.commentAmount, filter=settings.filterTime, isTesting=False)
        self.reddit.changeSub(settings.getSub())
        
        print("Sending Images now!")
        listOfImgs = []
        for post in postArr:
            with io.BytesIO() as image_binary:
                        post.img.save(image_binary, 'PNG')
                        image_binary.seek(0)
                        listOfImgs.append(discord.File(fp=image_binary, filename=f'{post.title}.png'))
        
        return postArr, listOfImgs
    
    @tasks.loop(seconds=settings.printerDelta)
    async def printer(self):
        try:
            view = UpcomingView(self)
            print("------- Creating Images -------")
            
            postArr, listOfImgs = await asyncio.to_thread(self.printerWrapper)
            view.add_item(discord.ui.Button(label="Post",style=discord.ButtonStyle.link,url=postArr[0].url))            
                
            await self.bot.get_channel(self.upcoming).send(postArr[0].title,files=listOfImgs, view=view)
            print("Images sent")
            
        except Exception as e:
            await self.bot.get_channel(self.general).send(f"Failed 😥  ```{e}```")
            print(traceback.format_exc())
            
    async def digester(self):
        # SHOULD DISABLE BUTTONS BEFORE DIGESTING
        try:
            view = PostedView()
            toDigest = [i async for i in self.bot.get_channel(1008464497574428803).history(limit=1)]
            
            if(len(toDigest) > 0):
                toDigest = toDigest[0]
                
                url = instaBot.uploadAlbum(toDigest.content, "Caption")
                view.add_item(discord.ui.Button(label="Post",style=discord.ButtonStyle.link,url=url))

                await self.bot.get_channel(self.posted).send(toDigest.content, files=[await f.to_file() for f in toDigest.attachments], view=view)
                await toDigest.delete()
            else:
                await self.bot.get_channel(self.general).send(f"Nothing do digest 😁 - {time.ctime()}")
                
              
        except Exception as e:
            await self.bot.get_channel(self.general).send(f"Digest failed - {time.ctime()}😥 \n {e}")
            print(traceback.format_exc())
        
    @printer.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()

class UpcomingView(discord.ui.View):
    def __init__(self, other):
        self.other = other
        self.postedView = PostedView()
        super().__init__()
    
    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):        
        try:
            for child in self.children:
                child.disabled=True
            await interaction.response.edit_message(view=self)
                
            files = [await f.to_file() for f in interaction.message.attachments]
            content = interaction.message.content
            await interaction.message.delete()
            await self.other.bot.get_channel(1008812515339276430).send(content, files=files, view = self.postedView)
        except:
            print(traceback.format_exc())

        
        instaBot.uploadAlbum(interaction.message.content, "caption")

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children:
            child.disabled=True
        await interaction.response.edit_message(view=self)
        
        await interaction.message.delete()
        
class PostedView(discord.ui.View):
    @discord.ui.button(label='Delete Post', style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await self.bot.get_channel(1008812540744192120).send(interaction.message.content, files=[await f.to_file() for f in interaction.message.attachments])

        
        await interaction.response.defer()
        await interaction.message.delete()
        
        instaBot.deleteAlbum(interaction.message.content, "caption")
        
async def setup(bot):
    await bot.add_cog(Controller(bot))