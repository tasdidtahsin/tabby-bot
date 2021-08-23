# TabbyBot
# Developed by Tasdid Tahsin
# Email: tasdidtahsin@gmail.com

import discord
from discord.ext import commands
import json
from asyncio import sleep
from PIL import Image, ImageFont, ImageDraw
import os
from time import time
import io
import requests
import pymongo
from pymongo import MongoClient
import json
import asyncio
from discord import utils
import csv

import dbl


cluster0 = MongoClient('MongoDB Cluster Key')
db = cluster0['tabbybot']
collection = db['tournaments']


bot_token = 'Discord Bot Token'
client = commands.Bot(command_prefix = ['?','?'])

client.remove_command('help')


TopGG_Token = 'TopGG Token'
dbl.DBLClient(client, TopGG_Token, autopost=True) # Autopost will post your guild count every 30 minutes


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    print("-----------------------------")

    act = f'Tabbycat sites in {len(client.guilds)}+ tournaments [.commands]'
    while True:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=act))
        await asyncio.sleep(180)


@client.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.MissingPermissions):
        await ctx.channel.purge(limit = 1)
        await ctx.send(f'*You are missing the basic required Permission(s)*')
    #    if isinstance(error, commands.CommandNotFound):
    #        await ctx.send(f'*Command not found. *.help* for valid commands')

    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.purge(limit = 1)
        await ctx.send(f'*Command is missing required Argument*')
    
    if isinstance(error, commands.MissingRole):
        await ctx.send(f'*Command is missing required Role*')
    
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send(f'*Command is missing required Role*')
        
    if isinstance(error, commands.BotMissingPermissions):
        await ctx.send(f"**The bot is missing required permissions. Please give the bot ADMINISTRATOR Permission to work flawlessly**")        



#unmute

@client.command()
async def unmute(ctx, Member: discord.Member):
    await Member.edit(mute=False)
    await ctx.send(f"> {Member.mention} was unmuted successfully")

#defean

@client.command()
async def undeafen(ctx, Member: discord.Member):
    await Member.edit(deafen=False)
    await ctx.send(f"> {Member.mention} was undeafened successfully")

#destroy entries
@client.command(aliases = ['delete-data'])
@commands.has_permissions(administrator = True)
async def delete_data(ctx, *, confirmation = ''):
    if confirmation == 'YES I AM 100% SURE':
        collection.delete_one({'_id' : ctx.guild.id})
        await ctx.send("ALL TAB DATA SYNCED WITH THIS GUILD WAS DELETED SUCCESSFULLY")
    else:
        await ctx.send("Type **YES I AM 100% SURE** after the command to confirm what you are doing")
    



#sync with tab

@client.command()
@commands.has_permissions(administrator = True)
async def sync(ctx, url, token):

    try:
        await ctx.channel.purge(limit = 1)
    except:
        await ctx.send('> Please give the bot `Manage Messages` permission. These data are confidential. I need to remove them first to proceed')
        return

    if url.endswith('/'):
        x = url.split('/')[-2]
        x = str(x)
        p = len(x)+1
        y = url[:-p]
    else:
        x = url.split('/')[-1]
        x = str(x)
        p = len(x)
        y = url[:-p]
        
    slug = y+'api/v1/tournaments/'+x+'/'

    print(slug)
    
    guild = ctx.guild.id

    teams = slug + 'teams'
    adjudicators = slug + 'adjudicators'
    Token = 'token '+token

    r = requests.get(teams,
                    headers={
                    'Authorization' : Token
                    })

    teams = r.json()


    for team in teams:
        for speakers in team['speakers']:
            if speakers['url_key'] == None:
                await ctx.send("Sync failed! **Please generate Private URL for all participants and generate checkin identifier for them. Then try again.**")
                return
            del speakers["gender"]
            del speakers["anonymous"]
            del speakers["categories"]
            del speakers["pronoun"]
            del speakers["phone"]
        del team['institution']
        del team['reference']
        del team['long_name']
        del team['code_name']
        del team['use_institution_prefix']
        del team['break_categories']
        del team['institution_conflicts']


    r = requests.get(adjudicators,
                    headers={
                    'Authorization' : Token
                    })

    adjudicators = r.json()


    for adjudicator in adjudicators:
        if adjudicator['url_key'] == None:
            await ctx.send("Sync failed! **Please generate Private URL for all participants and generate checkin identifier for them. Then try again.**")
            return
        del adjudicator["gender"]
        del adjudicator["anonymous"]
        del adjudicator["institution"]
        del adjudicator["base_score"]
        del adjudicator['trainee']
        del adjudicator['independent']
        del adjudicator['institution_conflicts']
        del adjudicator['adjudicator_conflicts']
        del adjudicator['team_conflicts']
        del adjudicator["pronoun"]
        del adjudicator["phone"]

    r = requests.get(slug[:-1],
                    headers={
                    'Authorization' : Token
                    })

    r = r.json()
    
    print(json.dumps(r, indent = 2))
    name = r['name']

    print(name)
    
    if url.endswith('/'):
        url = url
    else:
        url = url+'/'

    data = {"_id" : guild,
            "tabby" : ctx.message.author.mention,
            "tournament" : slug,
            "name" : name,
            "site" : url,
            "token" : token,
            "teams" : teams,
            "adjudicators" : adjudicators,
    }


    collection.insert_one(data)
    print("\n\nCOMPLETED SUCCESSFULLY")

    await ctx.author.send(f'Hey there!\n **Tournament: {name}** was successfully synced with **Guild: {ctx.guild}!** I will be there to help you out. Happy tabbing! Also add my blood brother **Hear! Hear!** to your server for better management and awesome timekeeping from the link below. Don\'t forget to vote for him!\n https://top.gg/bot/706179030977740810')



#status
@client.command()
async def status(ctx):
    
    f = collection.find_one({"_id" : ctx.guild.id})

    user = f["tabby"]
    site = f["site"]
    name = f["name"]
    
    print(site, name, user)

    await ctx.send(f'''Tournament: **{name}**
Tab Director: **{user}**
Tabbycat Site: {site}''')



#feedback submission

@client.command()
async def feedback(ctx, rnd, oralist: discord.Member, score):


    try:
        await ctx.channel.purge(limit = 1)
    except:
        await ctx.send('> Please send your feedback in the tournament server. If something is wrong, contact your Tabby')
        return
    _round = rnd
    # Make API Calls Here

    adj = oralist.id
    discord_id = ctx.message.author.id
    guild = ctx.guild.id
    score = str(score)
    dbt = rnd



    x = collection.find_one({'_id': guild})
    #print(json.dumps(x, indent = 2))

    token = 'Token '+x['token']
    feedback = x['tournament']+'feedback'
    print(feedback)



    # Fetch the URL of the _adj

    x = collection.find_one({'_id': guild}, {'adjudicators' : {'$elemMatch' : {'discord_id': adj}}})
    #print(json.dumps(x, indent = 2))
    
    if x == {'_id': guild}:
        await ctx.send(f"The adjudicator is not in the bot's database. Please double check that you are mentioning the correct adjudicator or try using your private URL")

    adj_url = x['adjudicators'][0]['url']
    print(adj_url)


    # Fetch the Team URL from the DB
    x = collection.find_one({'_id': guild}, {'teams' : {'$elemMatch' : {'speakers.discord_id': discord_id}}})
    #print(json.dumps(x, indent=2))
    team_url = x['teams'][0]['url']
    print(team_url)


    # Fetch the Debate URL from the tabbyCat site

    x = collection.find_one({'_id': guild})
    #print(json.dumps(x, indent = 2))

    url = x['tournament']+'rounds'

    r = requests.get(url,
                    headers={
                    'Authorization' : token
                    })
    rounds = r.json()

    for rnd in rounds:
        pairing = rnd['url']+'/pairings'
        if rnd['abbreviation'] == dbt:
            break

    r = requests.get(pairing,
                    headers={
                    'Authorization' : token
                    })

    pairings = r.json()
    #print(json.dumps(pairings, indent = 2))


    found = False
    for pairing in pairings:
        #now_in = pairing["url"]
        #print(now_in)
        for a in pairing["teams"]:
            #print('    '+a['team'])
            if a["team"] == team_url: 
                found = True
                break
        if found == True:
            debate = pairing["url"]
            break
    print(debate)


    print(token)

    r = requests.post(
        feedback,
        json = {
                'adjudicator': adj_url,
                'source': team_url,
                'debate': debate,
                'score': score,
                'answers': [],
                'ignored': False,
                'confirmed' : True,
                'participant_submitter' : None
                },
        headers={
                'Authorization': token
                })
    if r.status_code == 201:
        print('Created!')
    else:
        print(r.status_code, r.text)



    if r.status_code != 201:
        await ctx.send(f'Oops! Something went wrong, {ctx.message.author.mention}. Please try again with the correct syntax. For farther instructions, contact your Tabby\n *Error Message*: `{r.text}`')

    if r.status_code == 201:
        await ctx.send(f'Feedback submitted and accepted successfully! {ctx.message.author.mention}')

        img = Image.open('./assets/feedback.png')
        draw = ImageDraw.Draw(img)
        rnd = str(_round)

        rating = str(score)
        adj = str(f'@{oralist}')

        ratingFont = ImageFont.truetype("./assets/fonts/segoe ui/bold.ttf", 49)
        adjFont    = ImageFont.truetype("./assets/fonts/segoe ui/semibold.ttf", 20)
        rndFont    = ImageFont.truetype("./assets/fonts/segoe ui/bold.ttf", 22)

        draw.text((121, 26), rating, font = ratingFont, fill = 'black')
        draw.text((220, 60), adj, font = adjFont, fill = 'black')
        draw.text((220, 11), rnd, font = rndFont, fill = 'black')

        arr = io.BytesIO()
        img.save(arr, format='PNG')
        arr.seek(0)
        file = discord.File(arr, filename = 'feedback.png')

        #img.save(f'{name}.png')
        #file = discord.File(open(f'{name}.png', 'rb'))

        #await ctx.send(f'Feedback for {oralist.mention} was sent successfully! {ctx.message.author.mention}')
        await ctx.author.send(f'**Feedback for @{oralist} was sent successfully!** Contact your Tabby if something is wrong', file=file)
        await sleep(20)
        del arr

    #except:
    #    await ctx.send("You are not allowed to send this feedback. *If you think, there's something wrong, contact your tabby.*")




#checkin

@client.command(aliases = ['REGISTER', 'Register', 'registration', r' register', r' REGISTER', r' Register'])
async def register(ctx, key):


    try:
        await ctx.channel.purge(limit = 1)
    except:
        await ctx.send('> Please register in the tournament server. If something is wrong, contact your Tabby')
        return

    p = collection.find_one({'_id' : ctx.guild.id})
    site = p['site']
    if site.endswith('/'):
        site = site
    else:
        site = site+'/'
    
    pvt_url = site+'privateurls/'+key+'/'
    

    try:
        #make API calls here

        key = key
        discord_id = ctx.message.author.id
        guild = ctx.guild.id

        x = collection.find_one({'_id': guild}, {'teams' : {'$elemMatch' : {'speakers.url_key': key}}})

        if x == {'_id' : guild}:
            
            print("EXECUTING THE ADJ registration CODES 3:)")
            x = collection.find_one({'_id': guild}, {'adjudicators' : {'$elemMatch' : {'url_key': key}}})

            if x == {'_id' : guild}:
                    
                f = collection.find_one({"_id": guild})
                    
                tournament = f['tournament']+'adjudicators'
                Token = 'Token '+f['token']
                print(Token, tournament)    
                    
                r = requests.get(tournament,
                                headers={
                                'Authorization' : Token
                                })
                    
                print('Got through the HTTP Requests')
                print(r.status_code)
                #print(r.text)
                    
                adjs = r.json()
                #p = json.dumps(adjs, indent = 2)
                
                found = False
                
                for a in adjs:
                    if a['url_key'] == key:
                        url = a['url']
                        name = a['name']
                        email = a['email']
                        url_key = a['url_key']
                        _id = a['id']
                        adj_core = a['adj_core']
                        found = True
                        break
                
                if found == False:
                        
                    tournament = f['tournament']+'teams'
                    Token = 'Token '+f['token']
                    print(Token, tournament)    
                        
                    r = requests.get(tournament,
                                    headers={
                                    'Authorization' : Token
                                    })
                        
                    print('Got through the HTTP Requests')
                    print(r.status_code)
                    #print(r.text)
                        
                    teams = r.json()
        
                    find = False
                    key_found = False
                    
                    for team in teams:
                        for speakers in team['speakers']:
                            
                            if speakers['url_key'] == key:
                                key_found = True
                                find = True

                            if key_found == True:
                                del speakers["gender"]
                                del speakers["anonymous"]
                                del speakers["categories"]
                                del speakers["pronoun"]
                                del speakers["phone"]
    
                        if find == True:
                            del team['institution']
                            del team['reference']
                            del team['long_name']
                            del team['code_name']
                            del team['use_institution_prefix']
                            del team['break_categories']
                            del team['institution_conflicts']
                            tm = team
                            break
                    #tm = json.dumps(tm, indent=2)
                    #print(tm)
                                
                    
                    
                    
                    collection.update_one({"_id" : guild}, {'$addToSet' : {"teams" : tm}})
                    
                    print("DONE!")
                    
                    
                    collection.update_one({"_id" : guild, "teams": {'$elemMatch': {"speakers.url_key": key}}}, {'$set' : {"teams.$[team].speakers.$[speaker].discord_id" : discord_id}}, array_filters = [{"team.speakers.url_key": key},{"speaker.url_key": key}])
                    await ctx.send(f"> {ctx.message.author.mention} synced with tab-system successfully!")
                    Kobe = collection.find_one({'_id' : guild})
                    Token = 'Token '+Kobe['token']

                    print(Token)
                    
                    x = collection.find_one({"_id": guild}, {"teams": {'$elemMatch': {"speakers.url_key": key}}})
                    
                    print(x)

                    for a in x['teams'][0]['speakers']:
                        personal_url = a['url']
                        name = a['name']
                        if a["url_key"] == key:
                            break
                    team_name = x['teams'][0]['short_name']

                    print(personal_url)

                    r = requests.put(personal_url+'/checkin',
                                    headers={
                                    'Authorization' : Token
                                    } )
                    if r.status_code == 200:
                        print("Successfully Checked in")
                        await ctx.send(f'> **{name}** of **{team_name}** *checked in successfully!*')

                    await ctx.author.send(f'Hey there, **{name}!**\n You were successfully synced with the tab-system and checked in! Your personal key is** {key} **\n and your private URL is {pvt_url}')
                        
                    
                    try:                    
                        role = utils.get(ctx.guild.roles, name = 'Debater')
                        if role != None:
                            await ctx.message.author.add_roles(role) 
                        else:
                            await ctx.guild.create_role(name = 'Debater', color = discord.Colour(0xe6b60d))
                            r = utils.get(ctx.guild.roles, name = 'Debater')
                            await ctx.message.author.add_roles(r) 

                    except:
                        print("*** Error in AUTO_ROLE")
                    
                    return
                    
                    
                                    
                adj_info = {"url" : url,
                        "id" : _id,
                        "name" : name,
                        "email" : email,
                        "url_key" : url_key,
                        "adj_core" : adj_core
                        }
                
                collection.update_one({"_id" : guild}, {'$addToSet' : {"adjudicators" : adj_info}})
                
                print("DONE!")
            
            
            collection.update_one({"_id" : guild, "adjudicators": {'$elemMatch': {"url_key": key}}}, {'$set' : {"adjudicators.$[adjudicator].discord_id" : discord_id}}, array_filters = [{"adjudicator.url_key": key}])
            await ctx.send(f"> {ctx.message.author.mention} synced with tab-system successfully!")


            Kobe = collection.find_one({'_id' : guild})
            Token = 'Token '+Kobe['token']
            print(Token)
            
            x = collection.find_one({'_id': guild}, {'adjudicators' : {'$elemMatch' : {'url_key': key}}})


            personal_url = x['adjudicators'][0]['url']
            name = x['adjudicators'][0]['name']
            print(personal_url)

            r = requests.put(personal_url+'/checkin',
                            headers={
                            'Authorization' : Token
                            })
            
            if r.status_code == 200:
                print("Successfully Checked in")
                await ctx.send(f'> **{name}** *checked in successfully!*')

            await ctx.author.send(f'Hey there, **{name}!**\n You were successfully synced with the tab-system and checked in! Your personal key is** {key} **\n and your private URL is {pvt_url}')
                
            try:
                
                
                role = utils.get(ctx.guild.roles, name = 'Adjudicator')
                if role != None:
                    await ctx.message.author.add_roles(role) 
                else:
                    await ctx.guild.create_role(name = 'Adjudicator', color = discord.Colour(0x22a777))
                    rl = utils.get(ctx.guild.roles, name = 'Adjudicator')
                    await ctx.message.author.add_roles(rl)
                
                
                if x['adjudicators'][0]['adj_core'] == True:
                    role = utils.get(ctx.guild.roles, name = 'AdjCore')
                    if role != None:
                        await ctx.message.author.add_roles(role) 
                    else:
                        await ctx.guild.create_role(name = 'AdjCore', color = discord.Colour(0x34d269))
                        rl = utils.get(ctx.guild.roles, name = 'AdjCore')
                        await ctx.message.author.add_roles(rl)
                                        
            
                
                        
            except:
                print("*** Error in AUTO_ROLE")

        else:
            collection.update_one({"_id" : guild, "teams": {'$elemMatch': {"speakers.url_key": key}}}, {'$set' : {"teams.$[team].speakers.$[speaker].discord_id" : discord_id}}, array_filters = [{"team.speakers.url_key": key},{"speaker.url_key": key}])
            await ctx.send(f"> {ctx.message.author.mention} synced with tab-system successfully!")
            Kobe = collection.find_one({'_id' : guild})
            Token = 'Token '+Kobe['token']

            print(Token)

            for a in x['teams'][0]['speakers']:
                personal_url = a['url']
                name = a['name']
                if a["url_key"] == key:
                    break
            team_name = x['teams'][0]['short_name']

            print(personal_url)

            r = requests.put(personal_url+'/checkin',
                            headers={
                            'Authorization' : Token
                            } )
            if r.status_code == 200:
                print("Successfully Checked in")
                await ctx.send(f'> **{name}** of **{team_name}** *checked in successfully!*')
            
            await ctx.author.send(f'Hey there, **{name}!**\n You were successfully synced with the tab-system and checked in! Your personal key is** {key} **\n and your private URL is {pvt_url}')
                
            
            try:                    
                role = utils.get(ctx.guild.roles, name = 'Debater')
                if role != None:
                    await ctx.message.author.add_roles(role) 
                else:
                    await ctx.guild.create_role(name = 'Debater', color = discord.Colour(0xe6b60d))
                    r = utils.get(ctx.guild.roles, name = 'Debater')
                    await ctx.message.author.add_roles(r) 

            except:
                print("*** Error in AUTO_ROLE")

                

    except:
        await ctx.send(f"*Oops, Something is wrong! Please ask your* **Tab Team** *to generate Checkin Identifier for you and then try again. Pass this error message to help them identify the problem:* `{r.text}` ")


#checkout

@client.command(aliases = ['check-out'])
async def checkout(ctx):

    try:
        await ctx.channel.purge(limit = 1)
    except:
        await ctx.send('> Please check-out on the tournament server. If something is wrong, contact your Tabby')
        return

    while True:
        #make API calls here
        discord_id = ctx.message.author.id
        guild = ctx.guild.id

        x = collection.find_one({'_id': guild}, {'teams' : {'$elemMatch' : {'speakers.discord_id': discord_id}}})

        if x == {'_id' : guild}:
            
            print("EXECUTING THE ADJ CHECK OUT CODES 3:)")
            x = collection.find_one({'_id': guild}, {'adjudicators' : {'$elemMatch' : {'discord_id': discord_id}}})

            Kobe = collection.find_one({'_id' : guild})
            Token = 'Token '+Kobe['token']
            print(Token)

            personal_url = x['adjudicators'][0]['url']
            name = x['adjudicators'][0]['name']
            print(personal_url)

            r = requests.delete(personal_url+'/checkin',
                            headers={
                            'Authorization' : Token
                            })
            
            if r.status_code == 200:
                print("Successfully Checked out")
                await ctx.author.send(f'You were successfully checked out!')
                await ctx.send(f'> **{name}** *checked out successfully!*')

        else:
            
            Kobe = collection.find_one({'_id' : guild})
            Token = 'Token '+Kobe['token']

            print(Token)

            for a in x['teams'][0]['speakers']:
                personal_url = a['url']
                name = a['name']
                if a["discord_id"] == discord_id:
                    break
            team_name = x['teams'][0]['short_name']

            print(personal_url)

            r = requests.delete(personal_url+'/checkin',
                            headers={
                            'Authorization' : Token
                            } )
            if r.status_code == 200:
                print("Successfully Checked out")
                await ctx.author.send(f'You were successfully checked out!')
                await ctx.send(f'> **{name}** of **{team_name}** *checked out successfully!*')
        return

    #except:
    #    await ctx.send("*Oops, Something is wrong! Please try again or use your private URL*")

#add_adj


#checkin

@client.command(aliases = ['check-in', 'chicken'])
async def checkin(ctx):

    try:
        await ctx.channel.purge(limit = 1)
    except:
        await ctx.send('> Please check-in on the tournament server. If something is wrong, contact your Tabby')
        return

    try:
        #make API calls here
        discord_id = ctx.message.author.id
        guild = ctx.guild.id

        x = collection.find_one({'_id': guild}, {'teams' : {'$elemMatch' : {'speakers.discord_id': discord_id}}})

        if x == {'_id' : guild}:
            
            print("EXECUTING THE ADJ CHECK OUT CODES 3:)")
            x = collection.find_one({'_id': guild}, {'adjudicators' : {'$elemMatch' : {'discord_id': discord_id}}})

            Kobe = collection.find_one({'_id' : guild})
            Token = 'Token '+Kobe['token']
            print(Token)

            personal_url = x['adjudicators'][0]['url']
            name = x['adjudicators'][0]['name']
            print(personal_url)

            r = requests.put(personal_url+'/checkin',
                            headers={
                            'Authorization' : Token
                            })
            
            if r.status_code == 200:
                print("Successfully Checked out")
                await ctx.author.send(f'You were successfully checked in!')
                await ctx.send(f'> **{name}** *checked in successfully!*')

        else:
            
            Kobe = collection.find_one({'_id' : guild})
            Token = 'Token '+Kobe['token']

            print(Token)

            for a in x['teams'][0]['speakers']:
                personal_url = a['url']
                name = a['name']
                if a["discord_id"] == discord_id:
                    break
            team_name = x['teams'][0]['short_name']

            print(personal_url)

            r = requests.put(personal_url+'/checkin',
                            headers={
                            'Authorization' : Token
                            } )
            if r.status_code == 200:
                print("Successfully Checked out")
                await ctx.author.send(f'You were successfully checked in!')
                await ctx.send(f'> **{name}** of **{team_name}** *checked in successfully!*')
    
    except:
        await ctx.send("*Oops, Something is wrong! Please try again or use your private URL*")



#motion

@client.command()
async def motion(ctx, rnd):

    # Make API Calls Here

    guild = ctx.guild.id
    dbt = str(rnd)



    x = collection.find_one({'_id': guild})
    #print(json.dumps(x, indent = 2))

    token = 'Token '+x['token']


    url = x['tournament']+'rounds'

    r = requests.get(url,
                    headers={
                    'Authorization' : token
                    })
    rounds = r.json()
    


    #print(json.dumps(rounds, indent = 2))

    for rnd in rounds:
                        
        if rnd['abbreviation'] == dbt: 
            if rnd['motions_released'] == False:
                await ctx.send(f"The motion for {dbt} is not released yet! Try again later.")
                break   
            for a in rnd['motions']:
                n = 1
                motion = a['text']
                print(motion)
                info_slide = a['info_slide']
                print(info_slide)
                
                if info_slide != "":
                    _info = f'**Info Slide:**\n{info_slide}'
                else:
                    _info = ""
                await ctx.send(f'Motion {n} for {dbt} :** {motion}**\n\n{_info}')
                
                n = n+1
            



#help

@client.command('commands')
async def _help(ctx, page=1):

    if page == 1:
        await ctx.send(""">  **TABBYBOT COMMAND LIST**
             
>  **BASICS ** *(To use these commands, the guild must be synced with a Tabbycat tournament)*
**```
~ register      : Registers you for the tournament and synceds you with the tab and gives you appropriate roles ~ ?register <8 digit identification key>

~ checkin       : Checkin to the tab for the current round

~ checkout      : Checkout yourself if you are going to be AFK

~ feedback      : Submit feedback on adjudicators ~ ?feedback <Round Abdreviation> <@Mention adj> <score> ~ IE: ?feedback R2 @tasdidtahsin 9

~ motion        : Get motion for any round ~ ?motion <Round Abbreviation>

~ status        : Shows the server status when it is synced with the Tabbycat```**
>   **UTILITY**
**```
~ undeafen      : Undeafens server deafend users ~ ?undeafen @Mention    

~ unmute        : Unmutes server muted users ~ ?unmute @Mention

~ announce      : ?announce "ANNOUNCEMENT IN THE QUOTES" ~ Announces a message to all the debate text channel. Requires user to have MANAGE MESSAGES PERMISSION.```**

  ***Use ` ? ` or mention **@TabbyBot** before all commands***
  
  **PAGE 1 of 2 | `?commands 2` for next page**

""")

    if page == 2:
        await ctx.send(""">  **TABBYBOT COMMAND LIST**
                       
>   **SYNC SERVER WITH THE TAB** 
**```
~ sync          : Syncs the guild with the tabbycat site ~ ?sync <TABBYCAT_SITE_URL> <API_TOKEN> ~ IE: ?sync https://td-tabby.herokuapp.com/testtourney 2389cj3n5y893u492cium81389vn189vu89 "You can get the  token from the Get API Token / Change Password Menu of the Tabbycat site home page"

~ delete-data   : Delete all the data from the database synced with the guild ~ ?deleta-data YES I AM 100% SURE```**
>   **VENUE CREATION**
**```
~ create        : ?create <Number of rooms> <BP/AP/APBP> ~ Creates venues an required roles for debates. Reqires user to have ADMINISTRATOR PERMISSION ~ IE: ?create 8 BP will create 8 rooms for BP debate. Use AP for 3v3, BP for British Parliamentery, BPAP for Hybrid Venues. This command also creates @Debater and @Adjudicator roles itself if those are not already created. The venues are only accessable by those two roles and admin. 

~ destroy       : ?destroy YES I AM 100% SURE ~ Requires user to have ADMINISTRATOR PERMISSION, destroys all rooms, in case you do something wrong while creating the venues```**

~ del-cat       : ?del-cat CategoryKeyWord ~ Requires user to have ADMINISTRATOR PERMISSION, destroys all categories with the given KeyWord, in case there are pre created rooms with different category name```**

~ del-cat-s     : ?del-cat-s CategoryKeyWord ~ Requires user to have ADMINISTRATOR PERMISSION, destroys all categories starting with the given KeyWord, in case there are pre created rooms with different category name```**

>   **OTHERS**
**```
~ about         : Know more about the bot and the team```**
  ***Use ` ? ` or mention **@TabbyBot** before all commands***
  
  **PAGE 2 of 2 | `?commands 1` for previous page**

""")

@client.command()
async def about(ctx):
    await ctx.send("""```TabbyBot is the first ever virtual assistant tab director made using the new Tabbycat API. This bot is for the tab directors and debaters to make tabbing online tournaments more easier. It basically syncs your tournament discord guild with the TabbyCat tab-system and give various automation features. It can create venues and do magic in any server, no template required! (Forked from BubunBot and upgraded later). The bot requires Tabbycat version 2.4 or later. 


  Developed by   : Tasdid Tahsin [tasdidtahsin#7276]
  Project Mentor : Étienne Beaulé [Étienne#7236]
  Credits        : Irhum [adorablemonk#4060] & Najib Hayder [Najib#7917]
 
</> Coded in Python3 using Tabbycat API v1, Discord.py & MongoDB
```
You can deploy Tabbycat 2.4 from here: https://heroku.com/deploy?template=https://github.com/TabbycatDebate/tabbycat/tree/master
Join the support server to reach us any time: https://discord.gg/hMbGq8a
""")




@client.event
async def on_guild_join(guild):
    await guild.owner.send("""

Hey there!
Thanks for adding me to your server. I'm free of charge, but **you have to credit my developers** putting the text below in your server's welcome page or acknowledgement channel. You don't have to copy paste that. Just type `?about` in the channel you want to give credit in, I'll put credits there.

```TabbyBot is the first ever virtual assistant tab director made using the new Tabbycat API. This bot is for the tab directors and debaters to make tabbing online tournaments more easier. It basically syncs your tournament discord guild with the TabbyCat tab-system and give various automation features. It can create venues and do magic in any server, no template required! (Forked from BubunBot and upgraded later). The bot requires Tabbycat version 2.4 or later. 

The release of Tabbycat 2.4 will be in a few days. Till then, stay tuned!

  Developed by   : Tasdid Tahsin [tasdidtahsin#7276]
  Project Mentor : Étienne Beaulé [Étienne#7236]
  Credits        : Irhum [adorablemonk#4060] & Najib Hayder [Najib#7917]
 
</> Coded in Python3 using Tabbycat API v1, Discord.py & MongoDB
```
                           
""")




######## MODERATION COMMANDS FROM BUBUN ############

AUDITORIUM_PREFIX = "Auditorium"
ADMIN_CATEGORY = "Admin"
WAIT = 15

ADJ = "Adjudicator"
ADMIN_ROLE = "Admin"
CORE = ["AdjCore", "Tab Team", "Equity Team", ADMIN_ROLE]

formats = {"BP": [(2, "OG"), (2, "OO"), (2, "CG"), (2, "CO")], "AP": [(3, "Gov"), (3, "Opp")],  "3v3": [(3, "Gov"), (3, "Opp")], "BPAP": [(2, "OG"), (2, "OO"), (2, "CG"), (2, "CO"), (3, "Gov"), (3, "Opp")]}


@client.command(name="begin-debate", aliases=["start-debate"],
            help="Requires Manage Messages Permission. Moves people out from prep rooms, sends them to debate rooms. DO NOT RUN UNLESS CONFIDENT TIME IS OVER")
@commands.has_permissions(manage_messages=True)
async def begin_debate(ctx):
    rooms = [room for room in ctx.guild.categories if "Venue" in room.name]

    await asyncio.wait([room_summon_helper(room) for room in rooms])    

@client.command(name="call-to-venue", aliases=["call-to-room"],
            help="Requires 'Adjudicator' Role. Moves people out from prep rooms for a specific debate room, and calls them in. Can be called by either core or adjes")
@commands.has_role('Adjudicator')
async def room_summon(ctx):
    room_category = ctx.message.channel.category
    await room_summon_helper(room_category)

async def room_summon_helper(room_category):
    prep_channels = [channel for channel in room_category.voice_channels if "Prep" in channel.name]
    debate_channel = [channel for channel in room_category.voice_channels if "Debate" in channel.name][0]

    await asyncio.wait([move(member, debate_channel) for channel in prep_channels for member in channel.members])

async def move(member, channel):
    if member.voice.self_mute:
        await member.edit(voice_channel=channel)
        await asyncio.sleep(0.125)
    else:
        await member.edit(voice_channel=channel, mute=True)
        await asyncio.sleep(WAIT)
        await member.edit(mute=False)

@client.command(name="call-all-to", aliases=["call-to"],
            help="Calls all people to the VOICE CHANNEL SPECIFIED. Does not affect people in results discussion or admin channels")
@commands.has_permissions(administrator = True)
async def call_to(ctx, *, voice_channel):


    await ctx.send(f"** COMMAND HAS BEEN REMOVED DUE TO POLICY CHANGES BY DISCORD **")

    
    """

    await ctx.send(f"Initializing the command given by {ctx.message.author.mention}")
    await ctx.guild.owner.send(f"`call-to-audi` used by {ctx.message.author.mention}")
    room_name = str(voice_channel)
    auditorium = [channel for channel in ctx.guild.voice_channels if room_name == channel.name][0]
    members = []
    

    for channel in ctx.guild.voice_channels:
        if auditorium_check(channel):
            members.extend(channel.members)

    await asyncio.wait([move(member, auditorium) for member in members])

    await ctx.send("**Moved every valid user successfully!**")

def auditorium_check(channel):
    if channel.category:

        if channel.category.name == ADMIN_CATEGORY:
            return False
    if "Result" in channel.name:
        return False
    if AUDITORIUM_PREFIX in channel.name:
        return False
    else:
        return True
"""

@client.command(name="call-to-auditorium", aliases=["call-to-audi", "call-to-hall"],
            help="Calls all people to the the first voice channel containing AUDITORIUM in its name. Does not affect people in results discussion or admin channels")
@commands.has_permissions(administrator = True)
async def call_to_auditorium(ctx):
    
    await ctx.send(f"** COMMAND HAS BEEN REMOVED DUE TO POLICY CHANGES BY DISCORD **")

"""   
   
    auditorium = [channel for channel in ctx.guild.voice_channels if AUDITORIUM_PREFIX in channel.name][0]
    members = []

    await ctx.send(f"Initializing the command given by {ctx.message.author.mention}")
    await ctx.guild.owner.send(f"`call-to-audi` used by {ctx.message.author.mention}")

    for channel in ctx.guild.voice_channels:
        if auditorium_checks(channel):
            members.extend(channel.members)
            
    print(members)

    await asyncio.wait([move(member, auditorium) for member in members])

    await ctx.send("**Moved every valid user successfully!**")


def auditorium_checks(channel):
    if channel.category:

        if channel.category.name == ADMIN_CATEGORY:
            return False
    if "Result" in channel.name:
        return False
    if AUDITORIUM_PREFIX in channel.name:
        return False
    else:
        return True

"""


@client.command(name="announce", help="Requires MANAGE MESSAGES PERMISSION.Format is %announce \"text here in quotes\". Sends text to all debate channels")
@commands.has_permissions(manage_messages = True)
async def announce(ctx, text: str):
    debate_tcs = [channel for channel in ctx.guild.text_channels if "debate" in channel.name]
    await asyncio.wait([channel.send(text) for channel in debate_tcs])
    await ctx.send(f"Announcement was sent successfully! {ctx.message.author.mention}")

"""
@client.command(name="summon", help="Requires MANAGE MESSAGES PERMISSION. Format is %summon @username. Only one user at a time. Moves @username to the channel you are in, even if @username would normally be unable to access the channel")
@commands.has_permissions(manage_messages = True)
async def summon(ctx, text):
    user = utils.find(lambda x: x.id == int(text[3:-1]), ctx.guild.members)

    caller_state = ctx.author.voice
    user_voice_state = user.voice

    if user_voice_state is not None and caller_state is not None:
        await user.edit(voice_channel=caller_state.channel, mute=True)
        await asyncio.sleep(WAIT)
        await user.edit(mute=False)
    elif caller_state is None:
        await ctx.send("*You're* not connected to a voice channel")
    elif user_voice_state is None:
        await ctx.send("Target isn't connected to a voice channel")

    await user.send(f"You were moved by **{ctx.message.author}**")
"""

@client.command(name="create", help="Reqires ADMINISTRATOR PERMISSION, example %create 2 4 BP creates 2 floors of 4 venues each, with BP format prep rooms. Use VS or AP for 3v3, BPAP for hybrid debate rooms")
@commands.has_permissions(administrator = True)
async def create(ctx, num_rooms: int, debate_format, prefix=''):
    
    if num_rooms > 20:
        await ctx.send("Please create less than 20 rooms per category. Also avoid making venues continuously else you might get rate limited. To add prefix before venue name, put the prefix after the number of rooms seperated by a space. IE `?create 20 BP A`")
        return
   
    
    if debate_format not in ["BP", "AP", "3v3", "BPAP"]:
        await ctx.send(f"The command format is `?create <Number of Rooms> <Debate Format>` *IE: ?create 12 BP* Valid formats are `BP`, `AP`, `3v3`, `BPAP` ")
        return
        

    format_info = formats[debate_format]
    rooms = []
    
    #Role Check
    
    role = utils.get(ctx.guild.roles, name = 'Debater')
    if role == None:
        await ctx.guild.create_role(name = 'Debater', color = discord.Colour(0xe6b60d))
        
    role = utils.get(ctx.guild.roles, name = 'Adjudicator')
    if role == None:
        await ctx.guild.create_role(name = 'Adjudicator', color = discord.Colour(0x22a777))
                                

    with open('permissions.json') as fp:
        permissions = json.load(fp)

    
    for room in range(1, num_rooms + 1):
        room_number = prefix+str(room)
        room_category = await ctx.guild.create_category(f"Venue {room_number}")
        await asyncio.sleep(1)
        rooms.append((room_category, room_number))

    await asyncio.wait([create_rooms(room[0], room[1], format_info, permissions) for room in rooms])
    await ctx.send(f"Created {num_rooms} Venues")

async def create_rooms(room_category, room_number, format_info, permissions):
    await room_category.create_text_channel(f"{room_number}-debate")
    await asyncio.sleep(1)
    await room_category.create_voice_channel(f"{room_number}: Debate")
    await asyncio.sleep(1)
    
    prep_rooms = await create_prep_rooms(room_category, room_number, format_info)
    await asyncio.sleep(1)
    adj_room = await room_category.create_voice_channel(f"{room_number}: Results Discussion")
    await asyncio.sleep(1)
    prep_awaitables = [change_permissions(channel, permissions["Prep Rooms"]) for channel in prep_rooms]
    adj_awaitables = [change_permissions(adj_room, permissions["Results Discussion"])]

    await asyncio.wait(prep_awaitables + adj_awaitables)

async def create_prep_rooms(room_category, room_number, format_info):
    rooms = []
    for team_name in format_info:
        room = await room_category.create_voice_channel(f"{room_number} Prep: {team_name[1]}", user_limit=team_name[0])
        rooms.append(room)
        await asyncio.sleep(1)

    return rooms

async def change_permissions(channel, permissions_dict):
    awaitables = []
    guild = channel.guild

    for role_name in permissions_dict.keys():
        role = utils.get(guild.roles, name=role_name)
        awaitables.append(channel.set_permissions(role, **permissions_dict[role_name]))

    await asyncio.wait(awaitables)



@client.command(name="destroy", help="Requires ADMINISTRATOR PERMISSION, destroys all rooms, in case one calls %create wrong")
@commands.has_permissions(administrator = True)
async def destroy(ctx, *, confirmation = ''):
    if confirmation == "YES I AM 100% SURE":
        cats = [cat for cat in ctx.guild.categories if "Venue" in cat.name]
        await asyncio.wait([destroy_cat(cat) for cat in cats])

    else:
        await ctx.send("Type **YES I AM 100% SURE** after the command to confirm what you are doing")
    
async def destroy_cat(cat):
    for channel in cat.channels:
        await asyncio.sleep(1)
        await channel.delete() 
    await cat.delete()
    
@client.command(name="delete-categories", aliases = ['del-cat'], help="Requires ADMINISTRATOR PERMISSION, destroys all rooms, in case one calls %create wrong")
@commands.has_permissions(administrator = True)
async def delete_categories(ctx, *, confirmation = ''):
    if confirmation != '':
        cats = [cat for cat in ctx.guild.categories if confirmation in cat.name]
        await asyncio.wait([destroy_cat(cat) for cat in cats])
        

@client.command(name="delete-categories-s", aliases = ['del-cat-s'], help="Requires ADMINISTRATOR PERMISSION, destroys all rooms, in case one calls %create wrong")
@commands.has_permissions(administrator = True)
async def delete_categories_s(ctx, *, confirmation = ''):
    if confirmation != '':
        cats = [cat for cat in ctx.guild.categories if cat.name.startswith(confirmation)]
        await asyncio.wait([destroy_cat(cat) for cat in cats])





client.run(bot_token)