from cgi import test
from distutils.log import error
import io
import discord
from discord.ext import commands, tasks
from reddit import redditScrapper

class Controller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.reddit = redditScrapper("askreddit")
        self.printer.start()
        self.bot.loop.create_task(self.setChannelIds())
        
    async def setChannelIds(self):
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()

        self.general = self.bot.get_channel(1008439697678287010)


    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")
        
    @commands.command(name="ping")
    async def ping(self, ctx):
        view = Counter()
        await ctx.send('Press to increment', view=view)
        await ctx.channel.send("Pong!")                  
        
    @commands.command()
    async def purge(self, ctx):
        await ctx.channel.purge()


    @tasks.loop(minutes=3.0)
    async def printer(self):
        try:
            await self.general.send("------- Creating Images -------")
            postArr = self.reddit.getRedditPostAsImage(postCount=1, commentCount=3, filter="day", isTesting=True)

            print("Sending Images now!")
            for post in postArr:
                with io.BytesIO() as image_binary:
                            post.img.save(image_binary, 'PNG')
                            image_binary.seek(0)
                            await self.bot.get_channel(1008439697678287010).send(post.title, file=discord.File(fp=image_binary, filename='image.png'),)
            await self.general.send("Done....")
            print("Images sent finished")
        except Exception as e:
            await self.general.send("Images Failed 😥")
            print(e)

 

    @printer.before_loop
    async def before_printer(self):
        print('Waiting...')
        await self.bot.wait_until_ready()
        
        
async def setup(bot):
    await bot.add_cog(Controller(bot))    
    
class Counter(discord.ui.View):
    @discord.ui.button(label='0', style=discord.ButtonStyle.red)
    async def counter(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        number = int(button.label)
        button.label = str(number + 1)
        if number + 1 >= 5:
            button.style = discord.ButtonStyle.green
            
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        
    @discord.ui.button(label='8', style=discord.ButtonStyle.blurple, row=3)
    async def counter2(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        number = int(button.label)
        button.label = str(number - 1)
        if number - 1 < 0:
            button.style = discord.ButtonStyle.red
            
        await interaction.message.edit(view=self)
        await interaction.response.defer()
        