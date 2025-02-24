import discord
from discord.ext import commands
from discord import ui
from discord.ui import Button, View
import os
from dotenv import load_dotenv
import dateparser
import pause
from datetime import datetime

# REFERENCES
# referencing roles: https://discordpy.readthedocs.io/en/stable/api.html#discord.Role.name\


# Load environment variables from .env file
load_dotenv()

# Retrieve APP_ID (Bot Token)
APP_ID = os.getenv("APP_ID")

adminRoll = "Admin HackRPI"

if APP_ID is None:
    raise ValueError("Missing APP_ID. Ensure you have a .env file with APP_ID=YOUR_BOT_TOKEN")

# Discord Channel ID (Replace with actual channel ID)
CHANNEL_ID = 1337117398322647070  
ANNOUNCEMENTS_CHANNEL_ID = 1342590654592847903

preferred_channel_id = None

# Setup bot with necessary permissions
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Custom Help Class
class CustomHelpCommand(commands.HelpCommand):
    def get_command_signiture(self, command):
        return f'`!{command.qualified_name} {command.signature}`'
    
    async def send_bot_help(self,mapping):
        embed = discord.Embed(
            title = "HackRPI Discord Bot Help",
            description = "See the following commands below to find help for what you need!",
            color = discord.Color.blue()
        )
        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "Commands")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)
                
        ### GUESSING ON HOW THESE WILL FUNCTION        
        embed.add_field(
            name = "Examples",
            value = (
                "`!announcement 09/09/2000, 5:00PM \"Welcome to HackRPI. Good luck!` - Schedule and create a new announcment, indicate date and time, enclose message in quotes."
                "`\n!resources` - All resources offered to help you create your project."
            ),
        inline = False
        )
        embed.set_footer(text="Made with ❤️ by HackRPI.")
        
        channel = self.get_destination()
        await channel.send(embed=embed)
        
    async def send_command_help(self, command):
        embed = discord.Embed(
            title=f'Help with `{command.name}` command',
            description=command.help or "No description available",
            color=discord.Color.orange()
        )
        embed.add_field(
            name="Usage",
            value=self.get_command_signature(command),
            inline=False
        )
        await self.get_destination().send(embed=embed)  
        

# Initialize the bot with the desired command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents, help_command=CustomHelpCommand())
bot.help_command = CustomHelpCommand()



# will only be triggered once the bot is added to the new server, so long as the bot doesn't go down
@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    await bot.wait_until_ready()  # Ensure bot is fully ready before proceeding
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)  # Ensure it's awaited
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="Hello, I am the HackRPI Discord Bot!",
                description="Use !help to see all commands.",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="RCOS 2025")

            await channel.send(embed=embed)
            print(f"Embed message sent successfully in {channel.name} (ID: {channel.id})")
        else:
            print("Error: The fetched channel is not a TextChannel.")
    except discord.NotFound:
        print(f" Error: Channel ID {CHANNEL_ID} not found.")
    except discord.Forbidden:
        print("Error: Bot lacks permission to fetch/send messages in this channel.")
    except Exception as e:
        print(f" Unexpected error: {e}")


# see_announcements command (ROLE PERMISSIVE) ------------------------------------------------------------------
# Will just return a list of scheduled announcments
# Assuming this will be privately messaged to user who uses this command, as if we put it in a channel, anyone can see (unless private channel)
# has to communicate with backend to pull scheduled announcements that the bot can output
# Inputs: Just the command !see_announcments
# Output: list of all scheduled announcments (from discord command created announcements, as well as the ones created on the actual website)
# Best output format is probably using discord pagination, each response sent as an embed, and then we can cycle through different announcements using reactions.
# @bot.command()
# async def see_announcements():
    
#end-----------------------------------------------------------------------------------------------------------
    

# schedule_announcements command (ROLE PERMISSIVE) ------------------------------------------------------------
# Only some users are allowed to use this. 
# role permissive command (I CANT FIND ANY EXAMPLES ANYWHERE)
# Inputs: Date, Time, (gotta find a good way to ask for this information to make sure we dont run into issues with the inputs), message
# Might honestly be a better format to just privately message the user who uses this command with the link to the website page to make an announcement
#
# Output: A stored announcement in a data structure, then when the time is hit, it posts the announcement

# Creating a discord Modal for scheduling the event instead of just typing the text out.
class ScheduleAnnouncement(ui.Modal, title = 'Schedule Announcement'):
    titleOfMessage = ui.TextInput(label="Title", placeholder="Enter your title here...", required=True, style= discord.TextStyle.long)
    # Picking time may be better to use option pickers, rather than text input... Gotta look into this.
    time = ui.TextInput(label = "Date", placeholder="Input natural language: \"Tomorrow at 5PM...\"", required=True, style= discord.TextStyle.short)
    message = ui.TextInput(label = "Message", placeholder="Enter your message here...", required=True, style= discord.TextStyle.short)
    links = ui.TextInput(label= "Links", placeholder= "Enter any links here...", required= False)
    name = ui.TextInput(label = "Name", placeholder="Enter your name here...")
    
    async def on_submit(self, interaction: discord.Interaction):
        # IMPLEMENT LOGIC TO CHECK FOR TIME AND THEN POST ANNOUNCEMENT WHEN TIME HITS...
        parsedTime = dateparser.parse(self.time.value, settings={'TIMEZONE': 'US/Eastern'} )
        print(f"This is the parsed time using dateparser that we can use: {parsedTime}")
        channel = await bot.fetch_channel(ANNOUNCEMENTS_CHANNEL_ID)
        embed = discord.Embed(
            title= self.titleOfMessage.value,
            description= self.message.value,
            color= discord.Color.red(),
        )
        if self.links.value == None:
            print("NO LINKS ENTERED.")
        else:
            embed.add_field(
            name="Links",
            value= self.links.value,
        )
        embed.set_footer(text= f'Announced by {self.name.value}') # name recieved from modal
        await interaction.response.send_message(f'Announcement will be sent at {self.time.value}', ephemeral=True) #Ephemeral just means that it is only visible to user who sent the form.

        pause.until(parsedTime)
        await channel.send(embed=embed)
        

        
@bot.command()
@commands.has_role(adminRoll)
async def schedule_announcement(ctx):
    
    view = View()
    modalButton = Button(label = "Click here to schedule announcement.")
    async def modalButtonClicked(interaction: discord.Interaction):
        await interaction.response.send_modal(ScheduleAnnouncement())
    modalButton.callback = modalButtonClicked
    view.add_item(modalButton)
    await ctx.reply("Schedule your announcent below.", view=view)
    
#end------------------------------------------------------------------------------------------------------------


# announce_immediately command (ROLE PERMISSIVE) -----------------------------------------------------------
# Only some users are allowed to use this.
# Need to find out how to create roll permissive bot commands - discord.py docs not very helpful 
# we need this to create an announcment in the coressponding channel, @everyone then create an embed message with the wanted information
# Inputs: Title of Announcement, Message
# Output: embed message in the announcement channel
class AnnounceImmediately(ui.Modal, title = "Announce Now!"):    
    titleOfAnnouncement = ui.TextInput(label = "Title", placeholder = "Enter your title here...")
    message = ui.TextInput(label = "Message", placeholder="Enter your message here...", style=discord.TextStyle.long)
    links = ui.TextInput(label="Links", placeholder="Paste any links you want in the message...", required=False)
    name = ui.TextInput(label = "Name", placeholder="Enter your name here...")
    
    async def on_submit(self, interaction: discord.Interaction):
        channel = await bot.fetch_channel(ANNOUNCEMENTS_CHANNEL_ID)
        embed = discord.Embed(
            title = self.titleOfAnnouncement.value, #title we received by modal
            description = self.message.value, #message received from modal
            color = discord.Color.red()
        )
        if self.links.value == None:
            print("NO LINKS ENTERED.")
        else:
            embed.add_field(
            name="Links",
            value= self.links.value,
        )
        embed.set_footer(text= f'Announced by {self.name.value}') # name recieved from modal
        await channel.send(embed=embed)
        
        #Close the modal and make sure it doesn't show an error
        await interaction.response.send_message("Announcement sent successfully!", ephemeral= True) #Ephemeral just means that it is only visible to user who sent the form.
    

@bot.command()
@commands.has_role(adminRoll) # Role in my testing discord server for testing purposes. Will replace with actual admin role(s) that has access to announcements.
async def announce_immediately(ctx):
        channel = await bot.fetch_channel(ANNOUNCEMENTS_CHANNEL_ID)
        
        view = View()
        modalButton = Button(label = "Click here to create an announcement.")
        
        async def modalButtonClicked(interaction: discord.Interaction):
            await interaction.response.send_modal(AnnounceImmediately())
        modalButton.callback = modalButtonClicked
        view.add_item(modalButton)
        
        embed = discord.Embed(
            title="Send Your Announcement Below",
            color = discord.Color.red(),
        )
        await ctx.reply(embed=embed, view=view)
        
    
    
#end -----------------------------------------------------------------------------------------------------------
    

# Run the bot
bot.run(APP_ID)