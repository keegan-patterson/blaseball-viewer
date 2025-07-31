from PIL import Image, ImageOps
from PIL import ImageFont
from PIL import ImageDraw 
import requests
import io
import json
import random
import os
from Models import Players, weather, Team


def make_emoji(emoji_string, team_nick):
    if team_nick == "Lift":
        emoji = str(emoji_string)[0:1]
    else:
        emoji = chr(int(emoji_string, 16))
    return emoji


positions = {
    "batter": (0.43, 0.93),
    "pitcher": (0.5, 0.77),
    "first": (0.84, 0.76),
    "second": (0.55, 0.73),
    "third": (0.15, 0.75),
    "fourth":(0.06, 0.70),
    "feed":(0.39, 0.17),
    "home_score":(0.39, 0.30),
    "away_score":(0.50, 0.30),
    "at_bat_emoji":(0.59, 0.275),
    "at_bat_letters":(0.542, 0.275),
    "credit":(0,0),
    "innings":(0.09, 0.82),
    "innings_image":(.1, .85),
    "outings":(0.85, 0.92),
    "outings_balls":(.8, .95),
    "strikes":(.6, .9),
    "strikes_balls":(.61, .9),
    "balls":(.6, .92),
    "balls_balls":(.61, .92), #nice
    "outs":(.6, .94),
    "outs_balls":(.61, .94),
    "first_baseman":(.88, .74),
    "second_baseman":(.57, .71),
    "third_baseman":(.12, .73),
    "right_field":(.92, .70),
    "center_field":(.45, .68),
    "left_field":(.19, .70),
    "date":(.90, .0)
}

class ParkView: 
    
    def __init__(self):
        self.bg_filename = 'images/blallpark.jpeg'
        self.bg_overlay = ''
        self.bg = Image.open('images/blallpark.jpeg')
        self.cur_state = self.bg
        self.sprite_js = self.get_hetreasky_js()
        self.cached_players = {}
        
    def get_park_image(self):
        return self.cur_state

    def show_park(self):
        if os.path.isfile(self.bg_overlay):
            img = Image.open(self.bg_overlay)
            self.cur_state.paste(img, (0,0), img)
        
        self.cur_state.show()
        
    def add_fielders(self, defenders_json, team_nick=None):
        defender_pos = [["left_field", .27], ["first_baseman", .7], ["second_baseman", .43], ["center_field", .25], ["third_baseman", .7], ["right_field", .30]]
        for i in range(0, len(defender_pos)):
            if i >= len(defenders_json):
                break
            player_id = defenders_json[i]["id"]
            player_name = defenders_json[i]["name"]
            self.add_player(player_name, defender_pos[i][0], defender_pos[i][1], player_id, team_nick)
        
    # Player positions are maintained by percentage in enum above
    def add_player(self, player_name, pos_str, scale, id=None, team_name=None):
        if player_name == "":
            return
        p_img = self.get_hetreasky_pic(player_name, team_name)
        p_img = p_img.crop(p_img.getbbox())
        p_img = p_img.resize((int(p_img.size[0] * scale), int(p_img.size[1] * scale)))
        pos_x = self.bg.size[0] * positions[pos_str][0]
        pos_y = self.bg.size[1] * positions[pos_str][1]
        img_x = pos_x - p_img.size[0] / 2
        img_y = pos_y - p_img.size[1]
        self.cur_state.paste(p_img, (int(img_x), int(img_y)), mask=p_img)
        
        #Name?
        draw = ImageDraw.Draw(self.cur_state)
        font = ImageFont.truetype("times.ttf", 14)
        draw.text((pos_x, pos_y),player_name,(255,255,255),font=font)
        
    def add_feed(self, text):
        font_size = 15
        max_chars = 23
        feed_x = int(self.bg.size[0] * positions["feed"][0])
        feed_y = int(self.bg.size[1] * positions["feed"][1])
        
        img = self.cur_state
        draw = ImageDraw.Draw(img)
        #font = ImageFont.truetype("times.ttf", font_size)
        font = ImageFont.truetype("kongtext.ttf", font_size)

        # outcomes list instead of feed update
        if isinstance(text, list):
            outcomes = "Game Over."
            for l in text:
                outcomes = outcomes + " " + l
            text = outcomes
        
        offset = 0
        while text != "":
            if(len(text) > max_chars):
                draw.text((feed_x, feed_y + offset),text[0:max_chars],(255,255,255),font=font)
                if(text[0:max_chars].find("\n") != -1):
                    offset = offset + font_size
                text = text[max_chars:]
            else:
                draw.text((feed_x, feed_y + offset),text[0:len(str(text))],(255,255,255),font=font)
                text = ""
            offset = offset + font_size
            
    
    def add_score(self, home_nick, away_nick, home_runs, away_runs):
        home_str = home_nick + ": " + str(home_runs)
        away_str = away_nick + ": " + str(away_runs)
        self.add_text_at_position(home_str, "home_score")
        self.add_text_at_position(away_str, "away_score")
        
    def add_credit(self, text):
        self.add_text_at_position(text, "credit")

    def add_at_bat(self, text):
        self.add_text_at_position("AT BAT:", "at_bat_letters")
        self.add_emoji_at_position(text, "at_bat_emoji")

    def add_strikes(self, at_bat, max):    
        self.add_text_at_position("S", "strikes")
        self.add_balls_at_pos("strikes_balls", at_bat, max)
        
    def add_balls(self, at_bat, max):    
        self.add_text_at_position("B", "balls")
        self.add_balls_at_pos("balls_balls", at_bat, max)
        
    def add_outs(self, at_bat, max):    
        self.add_text_at_position("O", "outs")
        self.add_balls_at_pos("outs_balls", at_bat, max)
        
    def add_innings(self):
        self.image_at_position("images/Innings.PNG", "innings_image", 100)
        
    def image_at_position(self, filename, posname, size):
        i_x = int(self.bg.size[0] * positions[posname][0])
        i_y = int(self.bg.size[1] * positions[posname][1])
        i_img = Image.open(filename)
        i_img = i_img.resize((size, size))
        self.cur_state.paste(i_img, (i_x, i_y), i_img)
    
    def add_balls_at_pos(self, pos, num, max):
        size = 30
        b_x = int(self.bg.size[0] * positions[pos][0])
        b_y = int(self.bg.size[1] * positions[pos][1])
        b_img = Image.open("images/Ball_Icon.PNG")
        a_img = Image.open("images/Antiball_Icon.PNG")
        b_img = b_img.resize((size, size))
        a_img = a_img.resize((size, size))
        
        for i in range(max):
            if i < num:
                self.cur_state.paste(b_img, (b_x + (size * i), b_y), b_img)
            else:
                self.cur_state.paste(a_img, (b_x + (size * i), b_y), a_img)
    
    def add_text_at_position(self, text, position):
        font_size = 20
        home_x = int(self.bg.size[0] * positions[position][0])
        home_y = int(self.bg.size[1] * positions[position][1])
    
        img = self.cur_state
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("times.ttf", font_size)
        draw.text((home_x, home_y),text,(255,255,255),font=font)

    def add_emoji_at_position(self, text, position):
        font_size = 20
        home_x = int(self.bg.size[0] * positions[position][0])
        home_y = int(self.bg.size[1] * positions[position][1])

        img = self.cur_state
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("NotoEmoji-VariableFont_wght.ttf", font_size, encoding='utf-8')
        draw.text((home_x, home_y),text,(255,255,255),font=font)
    
    def get_hetreasky_pic(self, player_name, team_name=None):
        if team_name == "Houston":
            team_name = "Spies"
        if team_name == "Seattle":
            team_name = "Garages"
        if team_name == "Mexico City":
            team_name = "Wild Wings"

        name_in_pieces = player_name.split(" ")
        if len(name_in_pieces) > 1:
            if name_in_pieces[-1] in ["I", "II", "III", "IV", "V", "VI", "VII", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII"]:
                player_name = player_name[:player_name.find(name_in_pieces[-1]) - 1]
        
        
        if player_name == "Wyatt Mason":
            player_name = "NaN"
        
        player_start = self.sprite_js.find(player_name)
        # Player not found
        if player_start == -1:
            null_img = Image.open("images/Unknown_Player_Image.png")
            return null_img.resize((128, 128))

        sprite_list = self.get_sprite_list(player_name)
        # sprite_id = random.randrange(0, len(sprite_list))
        # sprite_id = self.get_default_sprite(player_name)
        sprite_id = -1
        if team_name is not None:
            for i in range(0, len(sprite_list)):
                if team_name.replace(" ", "") in sprite_list[i]:
                    sprite_id = i
        # sprite_id = INSERT TEAM NAME FINDER
        # if player_name in ["NaN","Chorby Short","Chorby Soul","Aldon Cashmoney","Nagomi McDaniel","Jaylen Hotdogfingers"]:
        if sprite_id == -1:
            sprite_id = random.randrange(0, len(sprite_list))
        
        image_filename = sprite_list[sprite_id].strip("\"")
        if not os.path.isfile("images/" + image_filename):
            url = "https://miniblaseball.surge.sh/images/" + image_filename
            raw = requests.get(url)
            image = Image.open(io.BytesIO(raw.content))
            image.save("images/" + image_filename)
        else:
            image = Image.open("images/" + image_filename)
        return image
        
        
    def get_sprite_list(self, player_name):
        player_start = self.sprite_js.find(player_name)
        p_s = self.sprite_js[player_start:].find("sprites:")
        sprite_and_more = self.sprite_js[player_start + p_s + 9:]
        sprite_end = sprite_and_more.find(']')
        sprite_list = str(sprite_and_more[:sprite_end])
        return sprite_list.split(",")

    def get_default_sprite(self, player_name):
        player_start = self.sprite_js.find(player_name)
        p_s = self.sprite_js[player_start:].find("default-sprite\":")
        sprite_and_more = self.sprite_js[player_start + p_s + 16:]
        sprite_end = sprite_and_more.find(',')
        default_num = sprite_and_more[:sprite_end]
        if default_num[-1] == "}":
            default_num = int(default_num[0:-1])
        else:
            default_num = int(default_num)
        return default_num
        
        
    def get_hetreasky_js(self):
        con = str(requests.get("https://miniblaseball.surge.sh/build/bundle.js").content)
        start_i = con.find("var fs=[")
        end_i = con.find(";function bs(e)")
        return con[start_i:end_i]
        
    def set_weather(self, w):
        w_name = w["name"]
        w_name = w_name.replace(" ", "_")
        fp = 'images/' + w_name + ".JPG"
        fp_overlay = "images/" + w_name + "_Overlay.PNG"
        if os.path.isfile(fp):
            self.bg = Image.open(fp).convert("RGBA")
            self.cur_state = self.bg
            self.bg_filename = fp
            self.bg_overlay = fp_overlay
        else:
            self.bg = Image.open('images/blallpark.jpeg')
            self.cur_state = self.bg

if __name__ == '__main__':
    fake_defenders_json = json.loads('[ { "id": "0148c1b0-3b25-4ae1-a7ce-6b1c4f289747", "name": "Rosales Darkness" }, { "id": "c3dc7aa2-e27b-4859-bbf0-47ba66c03186", "name": "Frankie Incarnate" }, { "id": "190a0f31-d686-4ac4-a7f3-cfc87b72c145", "name": "Nerd Pacheco" }, { "id": "4c1d37a8-75ec-4f98-b26d-a6b16ea84195", "name": "Willem Governor" }, { "id": "3c331c87-1634-46c4-87ce-e4b9c59e2969", "name": "Yosh Carpenter" }, { "id": "11f8da13-b186-4f1b-9615-6c56f9f0ac8b", "name": "Ralph Vincent" }, { "id": "d55ca982-4d41-4bee-99d1-93ce0ec03062", "name": "Audrey Leonard" }, { "id": "5f509284-5d6b-4cfc-95df-0ed6c726841c", "name": "Lupita Juice" }, { "id": "305921e8-3f4d-4c91-a280-d7bf1a449b08", "name": "Torus McGhee" } ]')
    pv = ParkView()
    pv.set_weather({"name": "Horizon"})
    pv.add_fielders(fake_defenders_json)
    pv.add_at_bat(make_emoji("0x1F3B8", "Garages"))
    pv.add_player('Liquid Friend', "batter", 1.0)
    pv.add_player('Jaylen Hotdogfingers', "pitcher", 0.8)
    pv.add_player('Wyatt Mason X', "first", 0.77)
    pv.add_player('Quack Enjoyable', "second", 0.5)
    pv.add_player('Sparks Beans', "third", 0.77)  
    pv.add_player('Uncle Plasma X', "fourth", 0.3)    
    pv.add_feed("The commissioner is doing a great job")
    pv.add_score("Hall Stars", "Eggs", 4, 20)
    pv.add_strikes(2, 3)
    pv.add_balls(1, 4)
    pv.add_outs(0, 3)
    pv.add_innings()
    pv.add_credit("All images by @HetreaSky, used unoffically without permission just a fandontkillme")
    pv.show_park()
    pv.get_sprite_list("Chorby Short")
