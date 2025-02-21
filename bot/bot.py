import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# REFERENCES
# referencing roles: https://discordpy.readthedocs.io/en/stable/api.html#discord.Role.name\


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
        
        
#DONT NEED THIS ----------------------------------------------------------------------------------------------

#@bot.command()
#async def email_me(ctx, *, email: str):
    #emailObtained = email.strip() 
    #print(f'Received email from user: {ctx.author}: {emailObtained}')

    # Implement email storage logic here 
    #Assume sent to backend api to be used for emailing or something of the sort
    
    #probably need to add a confirmation system so mistyped entries can be retried.

    # Send confirmation embed
    #returnEmbed = discord.Embed(
        #title="Email Received",
        #description=f"Here is the email you provided: **{emailObtained}**",
        #color=discord.Color.green(),
    #)
    #returnEmbed.set_footer(text="Made with ❤️ by HackRPI.")
    
    #await ctx.send(embed=returnEmbed)
#--------------------------------------------------------------------------------------------------------------


# see_announcements command (ROLE PERMISSIVE) ------------------------------------------------------------------
# Will just return a list of scheduled announcments
# Assuming this will be privately messaged to user who uses this command, as if we put it in a channel, anyone can see (unless private channel)
# has to communicate with backend to pull scheduled announcements that the bot can output
# Inputs: Just the command !see_announcments
# Output: list of all scheduled announcments (from discord command created announcements, as well as the ones created on the actual website)
#@bot.command()
#async def see_announcements():
    
#end-----------------------------------------------------------------------------------------------------------
    

# schedule_announcements command (ROLE PERMISSIVE) ------------------------------------------------------------
# Only some users are allowed to use this. 
# role permissive command (I CANT FIND ANY EXAMPLES ANYWHERE)
# Inputs: Date, Time, (gotta find a good way to ask for this information to make sure we dont run into issues with the inputs), message
# Might honestly be a better format to just privately message the user who uses this command with the link to the website page to make an announcement
#
# Output: A stored announcement in a data structure, then when the time is hit, it posts the announcement
#@bot.command()
#async def schedule_announcement():
    
#end------------------------------------------------------------------------------------------------------------


# announcement_immediately command (ROLE PERMISSIVE) -----------------------------------------------------------
# Only some users are allowed to use this.
# Need to find out how to create roll permissive bot commands - discord.py docs not very helpful 
# we need this to create an announcment in the coressponding channel, @everyone then create an embed message with the wanted information
# Inputs: Title of Announcement, Message
# Output: embed message in the announcement channel

@bot.command()
@commands.has_role("Admin HackRPI") # Role in my testing discord server for testing purposes
async def announcement_immediately(ctx, title: str, *, message: str):
        channel = await bot.fetch_channel(CHANNEL_ID)
        
        if channel is None:
            await ctx.send("Error: Announcement channel not found.")
        return

        embed = discord.Embed(
        title=title,  # Use the provided title
        description=message,  # Use the provided message
        color=discord.Color.red()
        )
    
        embed.set_footer(text=f"Announced by {ctx.author.display_name}")

        await channel.send("@everyone")
        await channel.send(embed=embed)
        
        await ctx.send("Announcment posted Successfully")
    
    
#end -----------------------------------------------------------------------------------------------------------
    

# Run the bot
bot.run(APP_ID)