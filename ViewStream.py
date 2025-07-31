# This one's for Sparks!!!
from PIL import Image, ImageTk
from PIL import ImageFont
from PIL import ImageDraw
import requests
import pysher
import gzip
import logging
import json
import os
import math
import time
import sys
import logging
import base64
from tkinter import Tk, Canvas
import PlarkView

# root = logging.getLogger()
# root.setLevel(logging.INFO)
# ch = logging.StreamHandler(sys.stdout)
# root.addHandler(ch)


def make_emoji(emoji_string, team_nick):
    if team_nick == "Lift":
        emoji = str(emoji_string)[0:1]
    else:
        emoji = chr(int(emoji_string, 16))
    return emoji

def get_color_from_hex(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def game_json_to_park(game_json, event_json, state):
    #if(event_json["changedState"])
    for key in event_json["changedState"].keys():
        state[key] = event_json["changedState"][key]

    # print(game_json)
    pv = PlarkView.ParkView()
    pv.set_weather(game_json["weather"])

    h_nick = game_json["homeTeam"]["nickname"]
    a_nick = game_json["awayTeam"]["nickname"]
    h_runs = state["homeScore"]
    a_runs = state["awayScore"]

    seas = 2
    day = game_json["day"]
    day = int(day) + 1

    if state["teamAtBat"] == "HOME":
        pv.add_fielders(state["defenders"], a_nick)
        runner_team = h_nick
        fielder_team = a_nick
        runner_emoji = game_json["homeTeam"]["emoji"]
        runner_team_color = get_color_from_hex(game_json["homeTeam"]["primaryColor"])
        fielder_team_color = get_color_from_hex(game_json["awayTeam"]["primaryColor"])
    else:
        pv.add_fielders(state["defenders"], h_nick)
        runner_team = a_nick
        fielder_team = h_nick
        runner_emoji = game_json["awayTeam"]["emoji"]
        runner_team_color = get_color_from_hex(game_json["awayTeam"]["primaryColor"])
        fielder_team_color = get_color_from_hex(game_json["homeTeam"]["primaryColor"])

    pv.add_at_bat(make_emoji(runner_emoji, runner_team))

    if "defenders" in state.keys() and state["defenders"] is not None and len(state["defenders"]) > 1:
        pv.add_fielders(state["defenders"], fielder_team)

    if "baserunners" in state.keys() and len(state["baserunners"]) > 0:
        for base_runner in state["baserunners"]:
            if "player" in base_runner.keys():
                boi_id = base_runner["player"]["id"]
                boi_name = base_runner["player"]["name"]
                base_int = base_runner["baseNumber"]
            else:
                boi_id = base_runner["id"]
                boi_name = base_runner["name"]
                base_int = base_runner["base"]

            base_name = ["first", "second", "third", "fourth"][base_int - 1]
            player_offset = [0.77, 0.5, 0.77, 0.3][base_int - 1]
            pv.add_player(boi_name, base_name, player_offset, boi_id, runner_team)

    if state["teamAtBat"] == "HOME":
        pitch_team_nick = a_nick
        batter_team_nick = h_nick
    else:
        pitch_team_nick = h_nick
        batter_team_nick = a_nick
    if "pitcher" in state.keys() and state["pitcher"] is not None:
        pv.add_player(state["pitcher"]["name"], "pitcher", 0.8, state["pitcher"]["id"], pitch_team_nick)
    if "batter" in state.keys() and state["batter"] is not None:
        pv.add_player(state["batter"]["name"], "batter", 1.0, state["batter"]["id"], batter_team_nick)

        pv.add_strikes(state["strikes"], game_json["gameStates"][0]["strikesNeeded"])
        pv.add_outs(state["outs"], game_json["gameStates"][0]["outsNeeded"])
        pv.add_balls(state["balls"], game_json["gameStates"][0]["ballsNeeded"])

    if "inning" in state.keys():
        pv.add_balls_at_pos("outings_balls", 0, state["inning"])

    # if game_json["lastUpdate"] == "Game Over.":
    #     pv.add_feed(game_json["outcomes"])
    # else:

    pv.add_feed(event_json["displayText"])
    pv.add_credit("All player art by HetreaSky; Blaseball by The Game Band")
    pv.add_text_at_position("Innings: infinite", "innings")
    pv.add_innings()

    if "inning" in state.keys():
        inning = state["inning"]
        pv.add_text_at_position("Outings: " + str(inning), "outings")

    pv.add_text_at_position("Season: " + str(seas) + " Day:" + str(day), "date")
    pv.add_score(h_nick, a_nick, h_runs, a_runs)
    return pv.get_park_image(), state

def set_state(game_json):
    if len(game_json["gameStates"]) > 0 and game_json["gameStates"][0]:
        state = game_json["gameStates"][0]
    else:
        state = {"homeScore": 0, "awayScore": 0, "teamAtBat": "AWAY", "strikes": 0, "outs": 0, "balls": 0}
    return state


window_size = ()

def connect_to_game(game_json):
    if not game_json:
        return

    print(game_json)

    global window_size
    window_size = (1600, 700)

    #tk window
    root = Tk()
    canvas = Canvas(root, width=1600, height=700)
    canvas.pack(fill="both", expand=True)
    img = ImageTk.PhotoImage(Image.open("images/blallpark.jpeg"))
    canvas.create_image(800, 350, image=img)
    root.update()

    def resize_me(event):
        if event.widget is root:
            global window_size
            window_size = (event.width, event.height)
            print("{0}, {1}".format(event.width, event.height))
    root.bind('<Configure>', resize_me)

    event_list = []

    pusher = pysher.Pusher("c481dafb635a60adffdd", "us3")

    def my_func(*args, **kwargs):
        print("processing Args:", args)
        print("processing Kwargs:", kwargs)
        coded_message = json.loads(args[0])['message']
        mes = json.loads(gzip.decompress(base64.b64decode(coded_message)))
        event_list.extend(mes)

    def connect_handler(data):
        print("Connection established!")
        channel = pusher.subscribe('game-feed-{0}'.format(game_json["id"]))
        channel.bind('game-data', my_func)

    pusher.connection.bind('pusher:connection_established', connect_handler)
    pusher.connect()

    #Start Stream
    times_ticked_without_update = 0
    connected_once = False
    state = set_state(game_json)
    while times_ticked_without_update < 30:
        if event_list:
            event_json = event_list.pop(0)
            # print(event_json)

            img_and_state = game_json_to_park(game_json, event_json, state)
            img_to_resize = img_and_state[0]
            resized_park_image = img_to_resize.resize(window_size)
            park_pil_image = ImageTk.PhotoImage(resized_park_image)
            state = img_and_state[1]
            canvas.create_image(window_size[0] / 2, window_size[1] / 2, image=park_pil_image)
            times_ticked_without_update = 0
            connected_once = True
        elif connected_once:
            pass
        else:
            pil_img = Image.open("images/blallpark.jpeg")
            pil_img_resized = pil_img.resize(window_size)
            img = ImageTk.PhotoImage(pil_img_resized)
            canvas.create_image(window_size[0] / 2, window_size[1] / 2, image=img)

        time.sleep(2.5)
        root.update()
        times_ticked_without_update += 1
        print("waiting {0}".format(times_ticked_without_update))

def print_box(box_json):
    size = len(box_json)
    print("---" * size, end="-\n")
    in_count = 1
    print("|", end="")
    for elem in box_json:
        pad = ""
        if(in_count < 10):
            pad = " "
        print("{0}{1}".format(pad, in_count), end="|")
        in_count += 1
    print()
    print("---" * size, end="-\n")
    print("|", end="")
    for elem in box_json:
        pad = ""
        if (box_json[elem][0] < 10):
            pad = " "
        print("{0}{1}".format(pad, box_json[elem][0]), end="|")
    print()
    print("---" * size, end="-\n")
    print("|", end="")
    for elem in box_json:
        pad = ""
        if (box_json[elem][1] < 10):
            pad = " "
        print("{0}{1}".format(pad, box_json[elem][1]), end="|")
    print()
    print("---" * size, end="-\n")


def list_and_choose_games(session):
    sim_url = "https://api2.blaseball.com//sim"
    sim_json = json.loads(session.get(sim_url).text)
    season_id = sim_json["simData"]["currentSeasonId"]

    live_games_url = "https://api2.blaseball.com//schedule//{0}//live".format(season_id)
    live_json = json.loads(session.get(live_games_url).text)
    day = live_json["dayNumber"]

    tourney_games_url = "https://api2.blaseball.com//seasons//{0}//tournaments".format(season_id)
    tourney_json = json.loads(session.get(tourney_games_url).text)
    print(tourney_json)

    game_count = 1
    game_jsons = []
    print("Welcome to day {0}! Ready to play ball? Select a game to watch:".format(day))
    for game_id in live_json["gameIds"]:
        game_url = "https://api2.blaseball.com//seasons//{0}//games//{1}?withSteps=0".format(season_id, game_id)

        game_json = json.loads(session.get(game_url).text)
        game_jsons.append(game_json)
        home_name = game_json["homeTeam"]["name"]
        away_name = game_json["awayTeam"]["name"]
        home_padding = " " * (30 - len(home_name))
        away_padding = " " * (30 - len(away_name))
        if game_count < 10:
            decimal_offset = " "
        else:
            decimal_offset = ""
        home_emoji = make_emoji(game_json["homeTeam"]["emoji"], game_json["homeTeam"]["nickname"])
        away_emoji = make_emoji(game_json["awayTeam"]["emoji"], game_json["awayTeam"]["nickname"])

        print("{0}: {1}{2}{3}{4}AT{5}{6}{7}".format(game_count, away_emoji, away_name, away_padding, decimal_offset, home_padding, home_name, home_emoji))
        game_count += 1

    # for game_id in tourney_json["gameIds"]:
    #     game_url = "https://api2.blaseball.com//seasons//{0}//games//{1}?withSteps=0".format(season_id, game_id)
    #
    #     game_json = json.loads(session.get(game_url).text)
    #     game_jsons.append(game_json)
    #     home_name = game_json["homeTeam"]["name"]
    #     away_name = game_json["awayTeam"]["name"]
    #     home_padding = " " * (30 - len(home_name))
    #     away_padding = " " * (30 - len(away_name))
    #     if game_count < 10:
    #         decimal_offset = " "
    #     else:
    #         decimal_offset = ""
    #     home_emoji = make_emoji(game_json["homeTeam"]["emoji"], game_json["homeTeam"]["nickname"])
    #     away_emoji = make_emoji(game_json["awayTeam"]["emoji"], game_json["awayTeam"]["nickname"])
    #
    #     print("{0}: {1}{2}{3}{4}AT{5}{6}{7}".format(game_count, away_emoji, away_name, away_padding, decimal_offset, home_padding, home_name, home_emoji))
    #     game_count += 1

    choice = int(input("Selection: ")) - 1

    if game_jsons[choice]["complete"]:
        box_url = "https://api2.blaseball.com//seasons//{0}//games//{1}//boxScore".format(season_id, game_id)
        # print(session.get(box_url).text)
        box_json = json.loads(session.get(box_url).text)
        print_box(box_json)
        return

    return game_jsons[choice]


def authenticate():
    status_resp = requests.Response()
    while status_resp.status_code != 200:
        email = input("Email: ")
        # email = "myemail@yahoo.com"
        passwd = input("Password: ")
        # passwd = "mypassword"

        login_payload = {"email": email, "password": passwd}

        login_uri = "https://api2.blaseball.com//auth/sign-in"
        test_uri = "https://api2.blaseball.com//tags"

        # Or just do it all as a session:
        bb_session = requests.Session()
        bb_session.post(login_uri, login_payload)
        status_resp = bb_session.get(test_uri)

        if status_resp.status_code == 401:
            print("Wrong password or login, dunkass")
        elif status_resp.status_code == 200:
            print("We're in")
        else:
            print(status_resp.status_code)

    return bb_session


if __name__ == '__main__':
    # authenticate session
    session = authenticate()

    # check available games
    game_json = list_and_choose_games(session)

    # connect to game
    connect_to_game(game_json)
