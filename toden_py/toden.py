import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import time
import discord
from discord.ext import commands
import requests 
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import asyncio
import json
import random

# Load environment variable    print(recent_uploads)
load_dotenv()
#def testme():

# Define intents
intents = discord.Intents.default()
intents.message_content = True
YOUTUBE_API_KEY = "AIzaSyDVco3BHPe_VLU8lhhDXr60nfBznrnuQRA"
API_KEY = "d604377c02a5476581fadad3c3c78750"
SENT_VIDEOS_FILE="sent_videos.json"
# Initialize YouTube API client
youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
# Create bot instance
client = commands.Bot(command_prefix="$", intents=intents)
days_of_week=["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
# Cooldown variables
last_run = time.time()
cooldown_time = 5.0  # Cooldown time in seconds

def load_questions(filename):
    words={}
    with open(filename,"r",encoding="utf-8")as file:
        for line in file:
            word, pinyin=line.strip().split("：")
            words[word]=pinyin
    return words
        

words=load_questions("fragen.txt")
user_scores={}

def cooldown():   
    """
    Check if the cooldown period is active.
    Returns True if the cooldown is active, False otherwise.
    """
    global last_run
    if time.time() < last_run + cooldown_time:
        return True  # Cooldown is active
    last_run = time.time()  # Update last_run to the current time
    return False  # Cooldown is not active
allowed_channels = [1077704169999310930]
# Global switches for "gut" and "tot"
 # Replace with youkk channel IDs
is_looping_gut = True
is_looping_tot = True
# Event: When the bot is ready

def save_sent_videos(video_ids):
    with open(SENT_VIDEOS_FILE,"w") as f:
        json.dump(video_ids,f,indent=4)

def load_sent_videos():
    if not os.path.exists(SENT_VIDEOS_FILE):
        with open(SENT_VIDEOS_FILE,"w") as file:
            json.dump([],file)
    try:
        with open(SENT_VIDEOS_FILE,"r") as file:
            data=file.read().strip()
            return json.loads(data) if data else []
    except (json.JSONDecodeError,ValueError):
        print("Corrupted json detected, ressenting sent_videos.json")
        with open(SENT_VIDEOS_FILE,"w") as file:
            json.dump([],file)
        return []
    
async def check_youtube():
    """Check YouTube for new videos and notify Discord."""
    await client.wait_until_ready()
    discord_channel = client.get_channel(1340926773805977600)
    sent_videos = load_sent_videos()  # Load sent video IDs

    while not client.is_closed():
        try:
            # Step 1: Get the Uploads Playlist ID
            print(f"checking ludwig's channel")
            channel_request = youtube.channels().list(
                part="contentDetails",
                id="UCSCTl_YRo_oHFI27qwV0y0w"
            )
            channel_response = channel_request.execute()

            if not channel_response["items"]:
                print("Invalid Channel ID or No Videos Found.")
                await asyncio.sleep(600)
                continue

            uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

            # Step 2: Get the most recent video from the playlist
            playlist_request = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=1
            )
            playlist_response = playlist_request.execute()

            if not playlist_response["items"]:
                print("No videos found in the playlist.")
                await asyncio.sleep(600)
                continue

            # Get video details
            item = playlist_response["items"][0]
            video_title = item["snippet"]["title"]
            video_id = item["snippet"]["resourceId"]["videoId"]
            published_at = item["snippet"]["publishedAt"]

            video_time = datetime.strptime(published_at, "%Y-%m-%dT%H:%M:%SZ")
            video_time = video_time.replace(tzinfo=pytz.UTC)

            current_time = datetime.now().replace(tzinfo=pytz.UTC)

            # Step 3: Check if uploaded in the last 24 hours & not already notified
            if (current_time - video_time) <= timedelta(days=1) and video_id not in sent_videos:
                sent_videos.append(video_id,current_time)  # Add video to sent list
                save_sent_videos(sent_videos)  # Save updated list

                # Create Embed Message
                embed = discord.Embed(
                   title="🌅☕️☕️🥐🍨⚘️ 🌅☕️☕️🥐🍨⚘️ Guten sonnigen Morgen Schwarzen Peter  und  Deutschland!🇩🇪🇩🇪🇩🇪🇩🇪💐❤️💐❤️💐❤️💐❤️💐❤️ Herzliches  DANKESCHÖN  Schwarzen Peter für  ein  SUPER!  SUPER!  SUPER  FABELHAFT  💥🖤🤍❤️💫 Marschlied!!!🎉🎉🎺🥁🎺🥁🎶🎶🎶🎶🎶💜 🌟🌟🌟🌟🌟 Sehr  GROSSARTIGES  Video!!!🎶💎💎💎💎🎵🎶🎶💐🎆💐🎆💐✨️💞💞Ich  wünsche  Sie  einen  sehr  wundervollen  {days_of_week[datetime.datetime.today()",
                    description=f"**{video_title}**\n🔗 [Scahu das Hier](https://www.youtube.com/watch?v={video_id})",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=item["snippet"]["thumbnails"]["high"]["url"])
                embed.set_footer(text="YouTube Updates")

                await discord_channel.send(embed=embed)
                print(f"✅ Notified about: {video_title}")

        except Exception as e:
            print(f"❌ Error checking YouTube: {e}")

        await asyncio.sleep(600)  # Check every 10 minutes


def get_bundesliga_table():
    """Fetches Bundesliga standings and returns a formatted string."""
    API_URL = "https://api.football-data.org/v4/competitions/BL1/standings" 
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(API_URL, headers=headers) 
    if response.status_code == 200:
        data = response.json()
        standings = data.get("standings", [])[0].get("table", [])
        table_lines = []
        
        for team in standings:
            table_lines.append({
                "position": str(team["position"]),
                "team_name": team["team"]["name"],
                "wins": str(team["won"]),
                "draws": str(team["draw"]),
                "losses": str(team["lost"]),
                "goals_for": str(team["goalsFor"]),
                "goals_against": str(team["goalsAgainst"]),
                "goal_diff": str(team["goalDifference"]),
                "points": str(team["points"])
            })

        # Format each row as a string
        return table_lines
    else:
        print(response.status_code)
        return []

def get_bundesliga_scores():
    """Fetches the most recent Bundesliga matchday results."""
    API_URL = "https://api.football-data.org/v4/competitions/BL1/matches" 
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        data = response.json()
        matches = data.get("matches", [])
        matchday_scores = {}

        for match in matches:
            matchday = match["matchday"]
            home_team = match["homeTeam"]["name"]
            away_team = match["awayTeam"]["name"]
            home_logo = match["homeTeam"].get("crest")
            away_logo = match["awayTeam"].get("crest")

            score = match["score"]
            full_time = score.get("fullTime", {})
            home_score = full_time.get("home")
            away_score = full_time.get("away")

            if home_score is not None and away_score is not None:
                if matchday not in matchday_scores:
                    matchday_scores[matchday] = []
                matchday_scores[matchday].append({
                    "home_team": home_team,
                    "home_logo": home_logo,
                    "home_score": home_score,
                    "away_score": away_score,
                    "away_logo": away_logo,
                    "away_team": away_team
                })
        if matchday_scores:
            latest_matchday = max(matchday_scores.keys())  # Get latest matchday
            scores = matchday_scores.get(latest_matchday, [])  # Always return a list
            return scores, latest_matchday
        else:
            return [], None  # Ensure `scores` is an empty list if no matches are found

    return [], None

@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))
    asyncio.create_task(check_youtube())
  

# Example: Checking for recent uploads from a channelecent_uploads = check_youtube(channel_id)
# Helper function to check allowed channels
def is_allowed_channel(channel_id):
    return channel_id in allowed_channels
'''
@client.command(name="prufung",description="mcq type questgion tester")
async def prufung(ctx):
    user_scores[ctx.author.id]=0
    random.shuffle(questions)
    for q in questions:
        options_text="\n".join(q["options"])
        questions_text=f"**{q['question']}**\n{options_text}\n\nReply with A,B,C,D!"
        await ctx.send(questions_text)
        def check(msg):
            return msg.author==ctx.author and msg.channel==ctx.channel and message.content.upper in ["A","B","C","D"]
        try:
            msg=await bot.wait_for("message",timeout=15.0,check=check)
            if msg.content.upper()==q["answer"]:
                await ctx.send("Correrct")
                user_scores[ctx.author.id]+=1
            else:
                await ctx.send(f"x Incorrect, the correct answer was {q['answer']}.\n")
        except asyncio.TimeoutError:
            await ctx.send("Time's up")
    score=user_scores[ctx.author.id]
    await ctx.send(f"{ctx.author.mention}, you completed the quiz! Your final score has been **{score}/{len(questions)}**")
    '''
@client.command(name="chinese",description="Test the users' chinese")
async def chinese(ctx):
    user_id=ctx.author.id
    remaining_words=words.copy()
    if user_id not in user_scores:
        user_scores[user_id]=0 
    if not words:
        embed=discord.Embed(title="Quiz schon abgeschlossen", description=f"Quiz schon abgeschlossen! {ctx.author.mention} deinen ergebnis: {user_scores[user_id]}",color=discord.Color.blue())
        await ctx.send(embed=embed)
    embed=discord.Embed(title="Chinese Quiz", color=discord.Color.blue())
    embed_message=await ctx.send(embed=embed)
    wrongones={}
    while remaining_words:
        word,pinyin=random.choice(list(remaining_words.items()))
        embed.clear_fields()
        embed.add_field(name="Questions", value=f"Was ist das richtiges pinyin fur **{word}**")
        embed.add_field(name="Current Score", value=str(user_scores[user_id]),inline=True)
        await embed_message.edit(embed=embed)
        def check(m):
            return m.author==ctx.author and m.channel==ctx.channel
        try:
            response=await client.wait_for('message',check=check,timeout=60)
            await response.delete()
            if response.content.strip().lower()=="exit":
                embed.title="Rausgegangen"
                embed.description=f"Rausgegangen, {ctx.author.mention}, du hast der quiz rausgegangen. Deinen ergebnist ist {user_scores[user_id]}"
                embed.color=discord.Color.orange()
                await embed_message.edit(embed=embed)
                return 
            if response.content.strip()==pinyin:
                if word in remaining_words:
                    del remaining_words[word]
                user_scores[user_id]+=1
                embed.add_field(name="Richtig",value=f"Das ist Richtig, die richtige antwort fur {word} ist {pinyin}.",inline=False)
                embed.add_field(name="Neue ergebnis", value=str(user_scores[user_id]),inline=True)
                embed.color=discord.Color.green()
            else:
                embed.clear_fields()
                embed.add_field(name="Falsch", value=f"Das ist falsch!!! Die richtiges antwort fur {word} ist {pinyin}",inline=False)
                embed.add_field(name="Current Score", value=str(user_scores[user_id]), inline= True)
                embed.color=discord.Color.red()
                wrongones[word]=pinyin
                del remaining_words[word]
        except TimeoutError:
            embed.clear_fields()
            embed.add_field(name="Zu langsam",value=f"Du bist zu langsam, die richtiges antwort fur {word} war {pinyin}",inline=False)
            embed.add_field(name="Neue ergebnis",value=str(user_scores[user_id]),inline=True)
            embed.color=discord.Color.dark_orange()
            return
    embed.clear_fields()
    embed.title="Quiz Abgeschlossen"
    embed.description=f"Du hast der quiz angeschlossen! Ergebnis: {user_scores[user_id]}"
    embed.color=discord.Color.gold()
    await embed_message.edit(embed=embed)
    if len(wrongones)>0:
        wrongthings="\n".join([f"**{word}** -> {pinyin}" for word,pinyin in wrongones.items()])
        embed=discord.Embed(title=f"Falsche Antworten", description=f"Hir sind alle deinen falsche Antworten \n {wrongthings}",color=discord.Color.yellow())
        await ctx.send(embed=embed)
    user_scores[user_id]=0
@client.command(name="tabelle", description="Arrange Bundesliga The Way from the API ")
async def tabelle(ctx):
    bundesliga_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Bundesliga_logo_%282017%29.svg/1200px-bundesliga_logo_%282017%29.svg.png"
    await ctx.message.add_reaction("✅")
    await ctx.send("Fetching Bundesliga Table")
    standings=get_bundesliga_table()
    if standings:
        embed=discord.Embed(title="🏆 Bundesliga Standings", description="Hier ist der Tabelle fur die Bundesliga",color=0xd3010c)
        embed.set_author(name="Bundesliga",icon_url=bundesliga_logo_url)
        for team in standings:
            team_text = (
                f"**{team['position']}. {team['team_name']}**\n"
                f"🏆 Points: {team['points']} | ⚽ GF: {team['goals_for']} | GA: {team['goals_against']} | GD: {team['goal_diff']}\n"
                f"✅ W: {team['wins']} | 🤝 D: {team['draws']} | ❌ L: {team['losses']}"
            )
            embed.add_field(name=team_text, value="‎", inline=False) 
    
        await ctx.send(embed=embed)
    else:
        await ctx.send("Failed to fetch Bundesliga standings")
# Command to toggle "gut" response
@client.command(name="spieltag", description="fetches bundesliga scores")
async def spieltag(ctx):
    bundesliga_logo_url="https://upload.wikimedia.org/wikipedia/en/thumb/d/df/Bundesliga_logo_%282017%29.svg/1200px-bundesliga_logo_%282017%29.svg.png"
    await ctx.message.add_reaction("✅")
    await ctx.send("Fetcing Bundesliga Scores...")
    scores,matchday=get_bundesliga_scores()
    if not isinstance(scores,list):
        scores=[]
    if scores:
        embed=discord.Embed(title=f"🏆 Bundesliga Matchday {matchday}", color=0xd3010c)
        embed.set_author(name="Bundesliga", icon_url=bundesliga_logo_url)
        for match in scores:
            home_team = match["home_team"]
            away_team = match["away_team"]
            home_score = match["home_score"]
            away_score = match["away_score"]

            match_text = f"```{home_team}      {home_score}-{away_score}     {away_team}```"
            embed.add_field(name=match_text, value="‎", inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("❌No recent Bundesliga matches found")

@client.command(name="togglegut", description="Toggle the response to 'gut'")
async def togglegut(ctx):
    if not is_allowed_channel(ctx.channel.id):
        await ctx.send("This command is not allowed in this channel.")
        return
    global is_looping_gut
    is_looping_gut = not is_looping_gut
    status = "on" if is_looping_gut else "off"
    await ctx.send(f"Response to 'gut' is now **{status}**.")

# Command to toggle "tot" response
@client.command(name="toggletot", description="Toggle the response to 'tot'")
async def toggletot(ctx):
    if not is_allowed_channel(ctx.channel.id):
        await ctx.send("This command is not allowed in this channel.")
        return
    global is_looping_tot
    status = "on" if is_looping_tot else "off"
    await ctx.send(f"Response to 'tot' is now **{status}**.")

# Event: When a message is received
@client.event
async def on_message(message):
    
    content_lower = message.content.lower()
    if message.author == client.user:
        return
    
    await client.process_commands(message)
    # Ignore messages in disallowed channels
    if "ludwig" in content_lower and not message.author.bot:
        await message.channel.send(f"🍃📯🦅🖤🤍❤️📯📯📯🎺🥁 Das ist ein FANTASTISCHER AUSGEZEICHNETESTE SCHÖNSTE 💪❣️💪🍃🌊 Marsch!!!!🎺💐☕️💖 Guten Morgen lieber Dr.Ludwig und sehr wunderschönen {days_of_week[datetime.today().weekday()]}!!!❤️❤️❤️❤️❤️❤️❤️❤️ Großes Herzliches DANKESCHÖN für ein SUPERRRRR WUNDERBARES Marsch und TOLLES Bild!!!.....🥰Ich bin BEGEISTERT!!!🌟......👌🥂🥂🎉💖💋💋🤗")
    if "tot" in content_lower or "toden"  in content_lower:
            await message.add_reaction("<:Peetah:1339118714120835142>")
    if "schlecht" in content_lower and not message.autho.bot:
        await message.channel.send("schlecht")

    if not is_allowed_channel(message.channel.id):
        return

    # Convert message content to lowercase

    # Check cooldown
    if cooldown():
        print("Cooldown active. Skipping message.")
        return

    # Respond to "gut"
    if "gut" in content_lower and is_looping_gut:
        await message.channel.send("gut") # Respond to "tot"
    if "tot" in content_lower and is_looping_tot:
           await message.channel.send(
            "THAT is the TOTIEST THING i have ever seen 😂 😂 😂 OMG 😂 that's so TODEN 🤣 so SCHWARZEN 👉👈 🤪 so TOT 🤩absolute GUT energy 🤪🤪"
        )
       # Process commands
# Run the bot
client.run(os.getenv('TOKEN'))
