import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve APP_ID (Bot Token)
APP_ID = os.getenv("APP_ID")

if APP_ID is None:
    raise ValueError("Missing APP_ID. Ensure you have a .env file with APP_ID=YOUR_BOT_TOKEN")

# Discord Channel ID (Replace with actual channel ID)
CHANNEL_ID = 1337117398322647070  

# Setup bot with necessary permissions
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Triggered when the bot successfully logs in."""
    await bot.wait_until_ready()  # Ensure bot is fully ready before proceeding
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

    try:
        channel = await bot.fetch_channel(CHANNEL_ID)  # Ensure it's awaited
        if isinstance(channel, discord.TextChannel):
            embed = discord.Embed(
                title="Hello, I am the email blast system bot",
                description="Reply to this message with `!emailme [your email]` to register your email!",
                color=discord.Color.blurple()
            )
            embed.set_footer(text="RCOS 2025")

            await channel.send(embed=embed)
            print(f"Embed message sent successfully in {channel.name} (ID: {channel.id})")
        else:
            print("⚠️ Error: The fetched channel is not a TextChannel.")
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
    returnEmbed.set_footer(text="RCOS 2025")
    
    await ctx.send(embed=returnEmbed)

# Run the bot
bot.run(APP_ID)