from instagramBot import InstaBot
import traceback
import io
import discord
from discord.ext import commands, tasks
from reddit import redditScrapper

class Controller(commands.Cog):
    
    class Settings:
        def __init__(self):
            self.commentAmount = 4
            self.scrapTime = 30
    
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.reddit = redditScrapper("askreddit")
        self.printer.start()
        self.bot.loop.create_task(self.setChannelIds())
        self.settings = self.Settings()
        
        
    async def setChannelIds(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

        self.general = self.bot.get_channel(1008439697678287010)
        self.upcoming = self.bot.get_channel(1008464497574428803)
        self.posted = self.bot.get_channel(1008812540744192120)
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


    @tasks.loop(seconds=40.0)
    async def printer(self):
        view = CustomView()
        try:
            print("------- Creating Images -------")
            # postArr = self.reddit.getRedditPostAsImage(postCount=1, commentCount=self.settings.commentAmount, filter="day", isTesting=True)

            # print("Sending Images now!")
            # for post in postArr:
            #     with io.BytesIO() as image_binary:
            #                 post.img.save(image_binary, 'PNG')
            #                 image_binary.seek(0)
            #                 await self.upcoming.send(post.title, file=discord.File(fp=image_binary, filename='image.png'), view=view)
            # print("Images sent")
            
            await self.upcoming.send("Test", view=view)
            
            
        except Exception as e:
            await self.general.send(f"Failed 😥 \n {e}")
            print(traceback.format_exc())

 

    @printer.before_loop
    async def before_printer(self):
        print('Waiting...')
        await self.bot.wait_until_ready()
        

class CustomView(discord.ui.View):
    
    @discord.ui.button(label='Accept', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        insta = InstaBot()
        insta.uploadAlbum()
        
                    
        deletedSent = await interaction.guild.get_channel(1008812540744192120).send(interaction.message.content)
        
        await interaction.message.reply(deletedSent.jump_url)
        await interaction.message.delete(delay=2.0)

    @discord.ui.button(label='Decline', style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        # button = manage_components.create_button(style=ButtonStyle.URL, label="Your channel", url=f'https://discord.com/channels/{member.guild.id}/{channel.id}')
        
        deletedSent = await interaction.guild.get_channel(1008812540744192120).send(interaction.message.content)
        await interaction.message.delete(delay=2.0)
        
        # for child in self.children:
        #     child.disabled=True
        # await interaction.response.edit_message(view=self)
        
        
async def setup(bot):
    await bot.add_cog(Controller(bot))