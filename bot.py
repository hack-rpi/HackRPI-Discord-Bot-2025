import discord
from discord.ext import commands
from discord import ui
from discord.ui import Button, View
from discord import app_commands
import os
from dotenv import load_dotenv
import dateparser
from datetime import datetime
import asyncio
import certifi
from pymongo.mongo_client import MongoClient

from insert_into_collection import insert_announcement
from get_database import getDataBase

# REFERENCES
# referencing roles: https://discordpy.readthedocs.io/en/stable/api.html#discord.Role.name\


uri = "mongodb+srv://seanhyde04:8kWiZWCqz1hsdGaV@discordbotannouncements.elqf3.mongodb.net/?retryWrites=true&w=majority&appName=DiscordBotAnnouncements"
client = MongoClient(uri, tlsCAFile=certifi.where())
try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error: {e}")
    
#get database
dbname = getDataBase()
collection = dbname['announcements']



markdownImage = "markdownTips.png"


# Load environment variables from .env file
load_dotenv()

# Retrieve APP_ID (Bot Token)
APP_ID = os.getenv("APP_ID")


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

def is_organizer(role_name: str):
    async def predicate(interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            return False
        
        return any(role.name == role_name for role in interaction.user.roles)
    return app_commands.check(predicate)


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
                "`!schedule_announcement` - Schedule and create a new announcment, indicate date and time and follow all instructions shown. Links not required."
                "`\n!immediate_announcement` - Create an immediate announcement, follow all instructions shown, and an announcement will be sent as soon as you submit."
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
tree = bot.tree
bot.help_command = CustomHelpCommand()

# will only be triggered once the bot is added to the new server, so long as the bot doesn't go down
@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    await bot.wait_until_ready()  # Ensure bot is fully ready before proceeding
    await bot.tree.sync()
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
class ScheduleAnnouncement(ui.Modal, title="Schedule Announcement"):
    titleOfMessage = ui.TextInput(label="Title", placeholder="Enter your title here...", required=True, style=discord.TextStyle.short)
    time = ui.TextInput(label="Date", placeholder="Input natural language: \"Tomorrow at 5PM...\"", required=True, style=discord.TextStyle.short)
    message = ui.TextInput(label="Message", placeholder="Enter your message here...", required=True, style=discord.TextStyle.long)
    links = ui.TextInput(label="Links", placeholder="Enter any links here...", required=False)
    name = ui.TextInput(label="Name", placeholder="Enter your name here...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        parsedTime = dateparser.parse(self.time.value, settings={'TIMEZONE': 'US/Eastern'})
        
        if parsedTime is None:
            await interaction.response.send_message("Invalid date format. Please use natural language like 'July 30 at 5:30PM'.", ephemeral=True)
            return

        # Get the current time
        now = datetime.now()
        
        # Calculate the time difference in seconds to delay the send announcement func 
        delay = (parsedTime - now).total_seconds()
        
        if delay <= 0:
            await interaction.response.send_message("The specified time is in the past. Please provide a future time.", ephemeral=True)
            return
        
        # Send scheduled announcement to DB
        insert_announcement(self.titleOfMessage.value, parsedTime, self.message.value, self.links.value, self.name.value  )

        # Acknowledge the interaction immediately so the modal closes
        await interaction.response.send_message(f'Announcement scheduled for {parsedTime}', ephemeral=True)

        async def send_announcement_after_delay():
            await asyncio.sleep(delay)  # delay without blocking rest of bot functions

            # Fetch the announcement channel
            channel = await interaction.client.fetch_channel(ANNOUNCEMENTS_CHANNEL_ID)

            # Create the embed message
            embed = discord.Embed(
                title=self.titleOfMessage.value,
                description=self.message.value,
                color=discord.Color.red(),
            )

            if self.links.value:
                embed.add_field(name="Links", value=self.links.value)

            embed.set_footer(text=f'Announced by {self.name.value}')

            await channel.send(embed=embed)

        # Schedule the function as a background task so we don't pause entire bot while waiting for announcement
        asyncio.create_task(send_announcement_after_delay())
        

# TREE VERSION OF SCHEDULE ANNOUNCEMENT
@tree.command(
    name= "schedule_announcement",
    description="Create an announcement that is scheduled to be posted at the time you have indicated."
    )
@is_organizer("Organizer")
async def schedule_announcement(interaction: discord.Interaction):
    view = View()
    modalButton = Button(label="Click here to schedule announcement.")

    async def modalButtonClicked(interaction: discord.Interaction):
        await interaction.response.send_modal(ScheduleAnnouncement())

    modalButton.callback = modalButtonClicked
    view.add_item(modalButton)

    embed = discord.Embed(
        title="Schedule Your Announcement Below",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Helpful Markdown Tips",
        value="See the attached image below for Markdown formatting help!",
        inline=False
    )

    # Attach the image
    file = discord.File("markdownTips.png", filename="markdownTips.png")
    embed.set_image(url="attachment://markdownTips.png")  # Reference the attached image

    await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=True)



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
    
    
#Tree command for announce immediately
@tree.command(
    name="announce_now",
    description="Create an announcement immediately."
)
@is_organizer("Organizer")
async def announce_now(interaction: discord.Interaction):
    view = discord.ui.View()
    modalButton = discord.ui.Button(label="Click here to create an announcement.")

    async def modalButtonClicked(button_interaction: discord.Interaction):
        await button_interaction.response.send_modal(AnnounceImmediately())

    modalButton.callback = modalButtonClicked
    view.add_item(modalButton)

    embed = discord.Embed(
        title="Send Your Announcement Below",
        color=discord.Color.blue(),
    )
    embed.add_field(
        name="Helpful Markdown Tips",
        value="See the attached image below for Markdown formatting help!",
        inline=False
    )
    file = discord.File("markdownTips.png", filename="markdownTips.png")
    embed.set_image(url="attachment://markdownTips.png")

    # For slash commands:
    await interaction.response.send_message(embed=embed, file=file, view=view, ephemeral=True)
    
    
@tree.command(
    name="see_scheduled_announcements",
    description="See all scheduled announcements."
)
@is_organizer("Organizer")
async def see_scheduled_announcements(interaction: discord.Interaction):
    """
    Slash command to view all scheduled announcements with pagination.
    """
    #Fetch all documents from the collection as a list
    doc_list = list(collection.find())

    #If there are no documents, send an ephemeral message
    if not doc_list:
        await interaction.response.send_message(
            "No scheduled announcements found.",
            ephemeral=True
        )
        return

    #Create the paginator View, passing in the list of documents
    view = AnnouncementsPaginatorView(doc_list)

    
    embed = view.create_embed()

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class AnnouncementsPaginatorView(discord.ui.View):
    """
    A View that paginates through a list of announcement documents.
    """
    def __init__(self, doc_list):
        super().__init__(timeout=None)  # or set a timeout in seconds
        self.doc_list = doc_list
        self.cur_page = 0
        self.max_page = len(doc_list) - 1

    def create_embed(self) -> discord.Embed:
        """Builds and returns an embed for the current page."""
        doc = self.doc_list[self.cur_page]

        # Create a basic embed with title, message, and color
        embed = discord.Embed(
            title=doc.get("title", "No Title"),
            description=doc.get("message", "No Message"),
            color=discord.Color.blue()
        )

        # Display the scheduled time (convert to string if it's a datetime)
        scheduled_time = doc.get("time", "No Time")
        embed.add_field(name="Scheduled Time", value=str(scheduled_time), inline=False)

        # If there are links, show them
        links = doc.get("links")
        if links:
            embed.add_field(name="Links", value=links, inline=False)

        # Footer shows who announced and page number
        embed.set_footer(
            text=f"Announced by {doc.get('name', 'Unknown')} | Page {self.cur_page+1}/{self.max_page+1}"
        )
        return embed

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ):
        """Handle clicking the Previous button."""
        if self.cur_page > 0:
            self.cur_page -= 1
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(
        self, 
        interaction: discord.Interaction, 
        button: discord.ui.Button
    ):
        """Handle clicking the Next button."""
        if self.cur_page < self.max_page:
            self.cur_page += 1
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)
        

class SeePastAnnouncements(discord.ui.View):
    def __init__(self, doc_list):
        super().__init__(timeout=None)
        self.doc_list = doc_list
        self.cur_page = 0
        self.max_page = len(doc_list) - 1

    def create_embed(self) -> discord.Embed:
        """Builds and returns an embed for the current page."""
        while self.cur_page <= self.max_page:
            doc = self.doc_list[self.cur_page]
            scheduled_time = doc.get("time")

            if isinstance(scheduled_time, str):
                scheduled_time = datetime.fromisoformat(scheduled_time)

            if scheduled_time <= datetime.now():
                embed = discord.Embed(
                    title=doc.get("title", "No Title"),
                    description=doc.get("message", "No Message"),
                    color=discord.Color.blue()
                )
                embed.add_field(name="Scheduled Time", value=str(scheduled_time), inline=False)

                links = doc.get("links")
                if links:
                    embed.add_field(name="Links", value=links, inline=False)

                embed.set_footer(
                    text=f"Announced by {doc.get('name', 'Unknown')} | Page {self.cur_page+1}/{self.max_page+1}"
                )
                return embed
            else:
                self.cur_page += 1

        return discord.Embed(
            title="No past announcements found.",
            description="All remaining announcements are scheduled for the future.",
            color=discord.Color.red()
        )

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cur_page > 0:
            self.cur_page -= 1
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.cur_page < self.max_page:
            self.cur_page += 1
        embed = self.create_embed()
        await interaction.response.edit_message(embed=embed, view=self)

# Command
@tree.command(
    name="see_past_announcements",
    description="See all announcements that have already been posted."
)
@is_organizer("Organizer")
async def see_past_announcements(interaction: discord.Interaction):
    doc_list = list(collection.find())

    if not doc_list:
        await interaction.response.send_message(
            "No scheduled announcements found.",
            ephemeral=True
        )
        return

    view = SeePastAnnouncements(doc_list)
    embed = view.create_embed()

    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    



    
def main():
    bot.run(APP_ID)
    

if __name__ == "__main__":
    main()