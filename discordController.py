import discord
import io
from discord.ext import commands
# from reddit import redditScrapper

intents = discord.Intents.default()
client = discord.Client(intents=intents)
# app = redditScrapper("askreddit")

# Define a simple View that gives us a confirmation menu
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()
        print("anan")

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    try:
        # await message.author.send("Collecting image")
        view = Confirm()
        await message.author.send('Do you want to continue?', view=view)
    except:
        pass
    # with io.BytesIO() as image_binary:
    #         app.getRedditPostAsImage(postCount=1, commentCount=0, filter="all")[0].save(image_binary, 'PNG')
    #         image_binary.seek(0)
    #         await message.author.send(file=discord.File(fp=image_binary, filename='image.png'))



client.run('MTAwNzc1NjQyMTQ3NzE3OTM5Mg.GPUpsy.fEOlBeHccJ8HUoTyqRpG9s7IR0mLDMpzK4VIpE')