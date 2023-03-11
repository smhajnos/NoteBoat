# -*- coding: utf-8 -*-
"""
Created on Fri May 27 17:20:58 2022

@author: Sam Hajnos
"""

import nextcord
from nextcord import SlashOption
from nextcord.ext import commands, tasks
import noteboatsecrets
import spotifychecker

nb_server = 979862989014462495
logs_channel = 979862989563904063
nb_color = 0xcb24da

intents = nextcord.Intents.all()
#intents.members = True


bot = commands.Bot(command_prefix='}', intents=intents)
sh = spotifychecker.SpotifyHandler()


@bot.slash_command(name="ping",description="Check if the bot is working", guild_ids=[nb_server])
async def ping(ctx):
    await ctx.send("Pong!")

@bot.slash_command(name="subscribe", description="Subscribe to an artist", guild_ids=[nb_server])
async def subscribe(ctx, artist):
    await ctx.send("Please wait... this may take a minute.")
    artist_name = artist
    (status_code, res) = sh.subscribe(str(ctx.user.id), artist_name)
    if status_code==spotifychecker.SUCCESS:
        embed = getSubbedEmbed(res,True)
        await ctx.send(embed=embed)
    elif status_code==spotifychecker.ARTIST_NOT_FOUND:
        await ctx.send("I couldn't find an artist called {}".format(artist_name))
    elif status_code==spotifychecker.ALREADY_SUBSCRIBED:
        await ctx.send("It looks like you are already subscribed to that artist.")
    elif status_code==spotifychecker.OTHER_ERROR:
        await ctx.send("Hmm... something went wrong. Try again or contact the developer for support.")
    
@bot.slash_command(name="unsubscribe", description="Unsubscribe from an artist", guild_ids=[nb_server])
async def unsubscribe(ctx, artist):
    await ctx.send("Please wait... this may take a minute.")
    artist_name = artist
    (status_code, res) = sh.unsubscribe(str(ctx.user.id), artist_name)
    if status_code==spotifychecker.SUCCESS:
        embed = getSubbedEmbed(res, False)
        await ctx.send(embed=embed)
    elif status_code==spotifychecker.ARTIST_NOT_FOUND:
        await ctx.send("I couldn't find an artist called {}".format(artist_name))
    elif status_code==spotifychecker.OTHER_ERROR:
        await ctx.send("Hmm... something went wrong. Try again or contact the developer for support.")

@bot.slash_command(name="view_subscriptions", description="View the artists you are currently subscribed to", guild_ids=[nb_server])
async def view_subscriptions(ctx, user : str = SlashOption(description="Target user",required=False)):
    if user:
        user_id = [int(s) for s in user.split() if s.isdigit()][0]
        user2 = await bot.get_user(user_id)
    else:
        user_id = ctx.user.id
        user2 = ctx.user
    if user2.nick:
        user_name = user2.nick
    else:
        user_name = user2.name
    subs = sh.getSubscriptions(user_id)
    if subs:
        embed = getSubsEmbed(user_name, subs)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't seem to be subscribed to anyone. Try `/subscribe`.")
    
    
def getSubbedEmbed(info, sub=True): #True for subscribe, False for unsubscribe
    if sub:
        embed=nextcord.Embed(title="Subscribed", description="Subscribed to {}".format(info["name"]), color=0xcb24da)
        embed.set_footer(text="Unsubscribe with /unsubscribe")
    else:
        embed=nextcord.Embed(title="Unsubscribed", description="Unsubscribed from {}".format(info["name"]), color=0xcb24da)
        embed.set_footer(text="Resubscribe with /subscribe")
    embed.set_thumbnail(url=info["image"])
    return embed

def getSubsEmbed(user, subs):
    substext=[]
    i = 1
    for artist in subs:
        substext.append("{}. {}".format(i, artist))
        i+=1
    text = "\r\n".join(substext)
    embed=nextcord.Embed(title="Subscriptions for {}".format(user),description=text, color=nb_color)
    embed.set_footer(text="Unsubscribe with /unsubscribe")
    return embed

@tasks.loop(seconds=3600)
async def check():
    print("Checking")
    sh.check()
    print("Processing pending")
    while sh.pendingCount() > 0:
        res = sh.getNextPending()
        user = await bot.fetch_user(int(res["user"]))
        print("Notifying user {} of new album {}".format(user.name, res["album_name"]))
        try:
            await user.send("Hey! New release from {artist_name}, {album_name}. Check it out here: {url}".format(**res))
        except:
            await log("Couldn't send message to {}. If they are still here, investigate.".format(user.name))
        sh.unpend(res["ID"],res["album"])
    print("Done. Waiting til next check.")

async def log(s):
    lc = bot.get_channel(logs_channel)
    await lc.send(s)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}') 
    main_channel = bot.get_channel(logs_channel)
    await main_channel.send("Starting")
    if not check.is_running():
        check.start()


print("Starting bot")
bot.run(noteboatsecrets.DISCORD_TOKEN)