import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Announcements will work as follows: Bot pulls from website announcements page and vice versa
# when annoucment is posted on either website or through announcement command on bot, it is posted
# on both ends. 

# Load environment variables from .env file
load_dotenv()

# Retrieve APP_ID (Bot Token)
APP_ID = os.getenv("APP_ID")

if APP_ID is None:
    raise ValueError("Missing APP_ID. Ensure you have a .env file with APP_ID=YOUR_BOT_TOKEN")

# Discord Channel ID (Replace with actual channel ID)
CHANNEL_ID = 1337117398322647070  

preferred_channel_id = None

# Setup bot with necessary permissions
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True


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
        
        

@bot.command()
async def emailme(ctx, *, email: str):
    emailObtained = email.strip() 
    print(f'Received email from user: {ctx.author}: {emailObtained}')

    # Implement email storage logic here 
    #Assume sent to backend api to be used for emailing or something of the sort
    
    #probably need to add a confirmation system so mistyped entries can be retried.

    # Send confirmation embed
    returnEmbed = discord.Embed(
        title="Email Received",
        description=f"Here is the email you provided: **{emailObtained}**",
        color=discord.Color.green(),
    )
    returnEmbed.set_footer(text="Made with ❤️ by HackRPI.")
    
    await ctx.send(embed=returnEmbed)

# Run the bot
bot.run(APP_ID)