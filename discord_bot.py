import os
import asyncio
import logging
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime
import pytz
from edspy import edspy
from static import *

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True 
bot = commands.Bot(command_prefix="/", intents=intents)

CHANNEL_IDS = {
    50188: int(os.getenv('CS_STAFF_CHANNEL_ID')),
    20568: int(os.getenv('CS_STUDENT_CHANNEL_ID')),
}

ed_client = edspy.EdClient()

class EventHandler:
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @edspy.listener(edspy.ThreadNewEvent)
    async def on_new_thread(self, event: edspy.ThreadNewEvent):
        thread: edspy.Thread = event.thread
        course: edspy.Course = await ed_client.get_course(thread.course_id)

        user = '[Redacted for FERPA]'
        url_pattern = r'https?://\S+|www\.\S+'
        clean_document = re.sub(url_pattern, 'Redacted URL for FERPA', thread.document)

        pacific_tz = pytz.timezone('America/Los_Angeles')
        now_pacific = datetime.now(pacific_tz)

        embed = discord.Embed(
            title=f'#{thread.number} **{thread.title}**',
            description=clean_document,
            url=f'{BASE_URL}/courses/{thread.course_id}/discussion/{thread.id}',
            color=EMBED_COLORS.get(thread.type, UKNOWN_COLOR),
            timestamp=now_pacific
        )
        embed.set_author(name=f'{course.code} • {thread.category}', url=f'{BASE_URL}/courses/{thread.course_id}/discussion')
        embed.set_footer(text=user, icon_url=USER_ICON)

        channel_id = CHANNEL_IDS.get(thread.course_id)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    await setup_ed_client()

async def setup_ed_client():
    ed_client.add_event_hooks(EventHandler(bot=bot))
    print("Subscribed to courses!")
    await ed_client.subscribe(list(CHANNEL_IDS.keys()))

@bot.command(name='test')
async def test_command(ctx):
    await ctx.send('Test command executed successfully!')

bot.run(DISCORD_TOKEN)
