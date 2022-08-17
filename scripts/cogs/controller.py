from ast import Delete
from hmac import digest
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
        self.printerDelta = 60*15
        self.digestDelta = 60*100
        self.filterTime = "hour"
        self.subs = ["askreddit", "showerthoughts", "askmen", "explainlikeimfive", "tooafraidtoask", "jokes", "unethicallifeprotips", "crazyideas"]
        self.mode = len(self.subs)-1
        
    def getSub(self):
        self.mode += 1
        self.mode = self.mode % len(self.subs)
        return self.subs[self.mode]

settings = Settings()
settings.mode = 5
instaBot = InstaBot()


class Controller(commands.Cog):   
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.reddit = redditScrapper(settings.getSub())
        self.printer.start()
        self.digester.start()
        self.bot.loop.create_task(self.setChannelIds())
        
        
    async def setChannelIds(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

        self.general = self.bot.get_channel(1008439697678287010)
        self.upcoming = self.bot.get_channel(1008464497574428803)
        self.posted = self.bot.get_channel(1008812515339276430)
        self.deleted = self.bot.get_channel(1008812540744192120)


    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")
        
    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.channel.send("Pong!")                  
        
    @commands.command()
    async def purge(self, ctx):
        await ctx.channel.purge()


    @tasks.loop(seconds=settings.printerDelta)
    async def printer(self):
        view = UpcomingView()
        try:
            print("------- Creating Images -------")
            postArr = self.reddit.getRedditPostAsImage(postCount=1, commentCount=settings.commentAmount, filter=settings.filterTime, isTesting=False)
            self.reddit.changeSub(settings.getSub())
            
            print("Sending Images now!")
            listOfImgs = []
            for post in postArr:
                with io.BytesIO() as image_binary:
                            post.img.save(image_binary, 'PNG')
                            image_binary.seek(0)
                            listOfImgs.append(discord.File(fp=image_binary, filename=f'{post.title}.png'))
                
            await self.upcoming.send(postArr[0].title,files=listOfImgs, view=view)
            print("Images sent")
            
            
        except Exception as e:
            await self.general.send(f"Failed 😥 \n {e}")
            print(traceback.format_exc())
            
            
    @tasks.loop(seconds=settings.digestDelta)
    async def digester(self):
        # SHOULD DISABLE BUTTONS BEFORE DIGESTING
        try:
            view = PostedView()
            toDigest = [i async for i in self.bot.get_channel(1008464497574428803).history(limit=1)]
            
            if(len(toDigest) > 0):
                toDigest = toDigest[0]
                
                url = instaBot.uploadAlbum(toDigest.content, "Caption")
                view.add_item(discord.ui.Button(label="Post",style=discord.ButtonStyle.link,url=url))

                await self.bot.get_channel(1008812515339276430).send(toDigest.content, files=[await f.to_file() for f in toDigest.attachments], view=view)
                await toDigest.delete()
            else:
                await self.general.send(f"Nothing do digest 😁 - {time.ctime()}")
                
              
        except Exception as e:
            await self.general.send(f"Digest failed - {time.ctime()}😥 \n {e}")
            print(traceback.format_exc())

 

    @printer.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
        
    @digester.before_loop
    async def before_printer(self):
        await self.bot.wait_until_ready()
        

class UpcomingView(discord.ui.View):
    @discord.ui.button(label='Accept', style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        
        await self.bot.get_channel(1008812515339276430).send(interaction.message.content, files=[await f.to_file() for f in interaction.message.attachments])

        
        await interaction.response.defer()
        await interaction.message.delete()
        instaBot.uploadAlbum(interaction.message.content, "caption")

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        # button = manage_components.create_button(style=ButtonStyle.URL, label="Your channel", url=f'https://discord.com/channels/{member.guild.id}/{channel.id}')
        
        await interaction.message.delete()
        await interaction.response.defer()
        
        # for child in self.children:
        #     child.disabled=True
        # await interaction.response.edit_message(view=self)
        
class PostedView(discord.ui.View):
    @discord.ui.button(label='Delete Post', style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        await self.bot.get_channel(1008812540744192120).send(interaction.message.content, files=[await f.to_file() for f in interaction.message.attachments])

        
        await interaction.response.defer()
        await interaction.message.delete()
        
        instaBot.deleteAlbum(interaction.message.content, "caption")
        
async def setup(bot):
    await bot.add_cog(Controller(bot))