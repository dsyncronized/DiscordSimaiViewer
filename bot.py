from PySimaiParser.SimaiParser import core
import discord
import io
import json
import asyncio
from renderer import draw_frame, render_chart
from discord.ext import commands

# discord bot

print(discord.__version__)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.slash_command(name="simai", description="visualize simai snippet")
async def simai(ctx, notation: discord.Option(str), approach_time: float = 0.7):
    await ctx.respond("Rendering...")

    notation = "&inote_1=\n" + notation
    chart = core.SimaiChart()
    chart.load_from_text(notation)

    json_data = chart.to_json()
    data = json.loads(json_data)
    chart_data = data["fumens_data"][0]["note_events"]

    await asyncio.to_thread(render_chart, chart_data, approach_time)

    await ctx.interaction.edit_original_response(content="Done!")
    await ctx.send(file=discord.File("chart.mp4"))

    with open("chart_data.json", "w", encoding="utf-8") as f:
        json.dump(chart_data, f, ensure_ascii=False, indent=4)
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    await ctx.send(file=discord.File("chart_data.json"))
    await ctx.send(file=discord.File("data.json"))
    
bot.run('your bot token here')