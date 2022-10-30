from dotenv import load_dotenv
import nextcord
import json
import os
from nextcord.ext import commands
from nextcord import File, ButtonStyle
from nextcord.ui import Button, View, Select
import requests
import datetime
from tabulate import tabulate

intents =  nextcord.Intents.all()
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
API_KEY = os.getenv("API_KEY")
client = commands.Bot(command_prefix='!', intents=intents)



bot = commands.Bot(command_prefix='!', intents=intents)

def getSeriesMatches(matchType, json_object):
    if matchType=="international":
        return json_object["typeMatches"][0]["seriesMatches"]
    return json_object["typeMatches"][1]["seriesMatches"]

def getMatchParams(data, key):
    if data is None:
        return ""
    if "inngs1" not in data:
        return ""
    if key not in data["inngs1"]:
        return "-"
    return data["inngs1"][key]

def getLiveMatch(data):
    for matchDetail in data:
        if("matchDetailsMap" in matchDetail):
            for match in matchDetail["matchDetailsMap"]["match"]:
                if match["matchInfo"]["state"] == "In Progress":
                    return match
    return None

@bot.slash_command(
    name="start",
    description="Match Type",
    guild_ids=[1035957142651412560],
)
async def support(ctx):
    International = Button(custom_id="international", label="International", style=ButtonStyle.blurple)
    Women = Button(custom_id="women", label="Women", style=ButtonStyle.blurple)
    async def matchCallback(interaction):
        url = "https://cricbuzz-cricket.p.rapidapi.com/series/v1/"+interaction.data["values"][0]

        headers = {
            "X-RapidAPI-Key": API_KEY,
            "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
        }

        response = requests.request("GET", url, headers=headers)
        json_object = json.loads(response.text)
        # print(response.text)
        matchDetails = json_object["matchDetails"]
        date = datetime.datetime.today().strftime("%d/%m/%Y")

        # for i in range(len(matchDetails)):
        #     if "matchDetailsMap" not in matchDetails[i]:
        #         continue
        #     if datetime.datetime.strptime(matchDetails[i]["matchDetailsMap"]["key"], "%a, %d %b %Y").strftime("%d/%m/%Y")==date:
        #         break
        match = getLiveMatch(matchDetails)
        if match is None:
            await interaction.response.send_message("No live matches available")
            return

        team1=match["matchInfo"]["team1"]
        team2=match["matchInfo"]["team2"]
        currentBat = team1["teamName"] if match["matchInfo"]["currBatTeamId"] == team1["teamId"] else team2["teamName"]
        matchname=team1["teamName"]+"vs"+team2["teamName"]+" "+match["matchInfo"]["matchDesc"]
        status=match["matchInfo"]["status"]
        if "team1Score" in match["matchScore"]:
            team1score=match["matchScore"]["team1Score"]
        else:
            team1score=None
        if "team2Score" in match["matchScore"]:
            team2score=match["matchScore"]["team2Score"]
        else:
            team2score=None
        l = [[team1["teamName"], getMatchParams(team1score,"runs"), getMatchParams(team1score, "wickets"), getMatchParams(team1score, "overs")], [team2["teamName"], getMatchParams(team2score,"runs"), getMatchParams(team2score, "wickets"), getMatchParams(team2score, "overs")]]
        table = tabulate(l, headers=['Team', 'Runs', 'Wickets', 'Overs'], tablefmt='orgtbl')

        await interaction.response.send_message(matchname+"\nStatus:"+status+"\nCurrent batting:"+currentBat+"\nScoreCard:\n"+table)

    async def int_callback(interaction):
        # print(interaction.data)
        url = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
        headers = {
	        "X-RapidAPI-Key": API_KEY,
	        "X-RapidAPI-Host": "cricbuzz-cricket.p.rapidapi.com"
        }
        response = requests.request("GET", url, headers=headers)
        # print(response.text)
        json_object = json.loads(response.text)
        seriesMatches = getSeriesMatches(interaction.data["custom_id"], json_object)
        view = View()
        select = Select(custom_id="123", min_values=1, max_values=1)
        select.callback = matchCallback
        for i in range(len(seriesMatches)):
            if "seriesAdWrapper" not in seriesMatches[i]:
                continue
            matchId = str(seriesMatches[i]["seriesAdWrapper"]["seriesId"])
            matchName = seriesMatches[i]["seriesAdWrapper"]["seriesName"]
            select.append_option(nextcord.SelectOption(value=matchId, label=matchName))
            
        view.add_item(select)
        await interaction.response.send_message(view=view)

    International.callback = int_callback
    Women.callback = int_callback
    myview = View()
    myview.add_item(International)
    myview.add_item(Women)
    await ctx.send("hi\n123", view=myview)

bot.run(TOKEN)