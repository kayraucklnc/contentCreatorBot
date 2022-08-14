from ast import arg
from discord.ext import commands, tasks

class Controller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.index = 0
        self.printer.start()

        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is online")
        
    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.channel.send("Pong!")
        
    @commands.command()
    async def purge(self, ctx):
        await ctx.channel.purge()

    @tasks.loop(seconds=2.0)
    async def printer(self):
        await self.bot.get_channel(1008439697678287010).send(str(self.index))
        self.index += 1

    @printer.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()
        
async def setup(bot):
    await bot.add_cog(Controller(bot))
    