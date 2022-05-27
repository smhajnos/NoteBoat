# -*- coding: utf-8 -*-
"""
Created on Fri May 27 17:20:58 2022

@author: sam
"""

from nextcord.ext import commands
import noteboatsecrets
import spotifychecker

bot = commands.Bot(command_prefix='}')
sh = spotifychecker.SpotifyHandler()

@bot.command()
async def ping(ctx):
    await ctx.reply('Pong!')
    

async def check():
    sh.check()
    while sh.pendingCount() > 0:
        res = sh.getNextPending()
        user = await bot.fetch_user(int(res["user"]))
        await user.send("Hey! New album from {artist_name}, {album_name}. Check it out here: {url}".format(**res))
        sh.unpend(res["ID"],res["album"])


@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')   
    while 1:
        await check()



bot.run(noteboatsecrets.DISCORD_TOKEN)