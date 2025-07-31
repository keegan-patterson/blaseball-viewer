# This one's for Sparks!!!
import requests
import json
import math

stats = ["tragicness",
"buoyancy",
"thwackability",
"moxie",
"divinity",
"musclitude",
"patheticism",
"martyrdom",
"cinnamon",
"baseThirst",
"laserlikeness",
"continuation",
"indulgence",
"groundFriction",
"shakespearianism",
"suppression",
"unthwackability",
"coldness",
"overpowerment",
"ruthlessness",
"pressurization",
"omniscience",
"tenaciousness", 
"watchfulness",
"anticapitalism",
"chasiness"]

weather = ["Void",
"Sun 2",
"Overcast",
"Rainy",
"Sandstorm",
"Snowy",
"Acidic",
"Solar Eclipse",
"Glitter",
"Blooddrain",
"Peanuts",
"Lots of Birds",
"Feedback",
"Reverb",
"Black Hole",
"Coffee",
"Coffee 2",
"Coffee 3s",
"Flooding",
"Salmon",
"Polarity Plus",
"Polarity Minus",
"???",
"Sun 90",
"Sun Point One",
"Sum Sun",
"????",
"????",
"Jazz",
"Night"]

class Players:
    def __init__(self, player_ids=None, json_list=None):
        if json_list is not None:
            self.num_players = len(json_list)
            self.json = json_list
        elif player_ids is not None:
            base_str = 'https://www.blaseball.com/database/players?ids='
            if isinstance(player_ids, str):
                base_str += f'{player_ids},'
            else:
                for loop in range(0,len(player_ids)):
                    base_str += f'{player_ids[loop]},'
                base_str = base_str.strip(",")
            self.req = requests.get(base_str)
            if self.req.status_code != 200:
                print("OH NO, error accessing player server!")
            self.json = self.req.json()
            self.num_players = len(player_ids)
            
    def get_all_attr(self, player_num):
        attrs = []
        attrs.append(self.json[player_num]["permAttr"])
        attrs.append(self.json[player_num]["seasAttr"])
        attrs.append(self.json[player_num]["weekAttr"])
        return attrs

    def get_stat(self, player_num, stat_name):
        if stat_name == "name" :
            return self.json[player_num][f'{stat_name}']
        else:
            is_elsewhere = False
            stat_value = self.json[player_num][f'{stat_name}']
            item_total = 0.0
            for item in self.json[player_num]["items"]:
                if item["health"] > 0:
                    for adj in item["root"]["adjustments"]:
                        if adj["type"] == 1 and stats[adj["stat"]] == stat_name:
                            item_total += float(adj["value"])
                    if item["prefixes"]:
                        for pre in item["prefixes"]:
                            for adj in pre["adjustments"]:
                                if adj["type"] == 1 and stats[adj["stat"]] == stat_name:
                                    item_total += float(adj["value"])
            coeff = 1.0
            if "OVERPERFORMING" in self.json[player_num]["permAttr"]:
                coeff = 1.2
            elif "UNDERPERFORMING" in self.json[player_num]["permAttr"]:
                coeff = 0.8
            p_attributes = self.json[player_num]["permAttr"]
            if "SHELLED" in p_attributes:
                def_stats = ["anticapitalism", "chasiness", "omniscience",
                 "tenaciousness", "watchfulness"]
                if stat_name not in def_stats:
                    coeff = 0.0
            if "ELSEWHERE" in p_attributes:
                coeff = 0.0
                is_elsewhere = True
            return [coeff * (stat_value + item_total), is_elsewhere]


class Team:
    def __init__(self, team_id):
        self.req = requests.get(f'https://www.blaseball.com/database/team?id={team_id}')
        if self.req.status_code != 200:
            print("OH NO, error accessing team server!")
        self.json = self.req.json()
        #print(self.get_stat("fullName"))
                                                                                             
    def get_stat(self, stat_name):
        return self.json[f'{stat_name}']


class Game:
    def __init__(self, game_id):
        self.req = requests.get(f'https://www.blaseball.com/database/gameById/{game_id}')
        if self.req.status_code != 200:
            print("OH NO, error accessing game server!")
        self.json = self.req.json()
        #print(f'\n {self.get_stat("homeTeamName")} VS {self.get_stat("awayTeamName")}')

    def get_stat(self, stat_name):
        return self.json[f'{stat_name}']


class Day:
    def __init__(self, season, day):
        #self.state = State()
        #self.json = self.state.get_stat("tomorrowSchedule")
        self.season_idx = season - 1
        self.day_idx = day - 1
        self.json = self.get_day_json(self.season_idx, self.day_idx)
        # prev_json, prev_pitchers is arranged oldest day to newest
        s_idx = self.json[0]["seriesIndex"]
        s_len = self.json[0]["seriesLength"]
        self.prev_json = []
        self.prev_pitchers = []
        if(s_idx > 1):
            while(s_idx > 1):
                s_idx -= 1
                
                # Previous series jsons
                cur_json = self.get_day_json(self.season_idx, self.day_idx - s_idx)
                self.prev_json.append(cur_json)

                # Previous series pitchers
                pitcher_list = []
                for game in cur_json:
                    pitcher_list.append(game["homePitcher"])
                    pitcher_list.append(game["awayPitcher"])
                self.prev_pitchers.append(Players(pitcher_list))
        self.pitcher_import()
        self.home_lineups = []
        self.away_lineups = []
        self.home_teams = []
        self.away_teams = []
        for loop in range(0, len(self.json)):
            home_team = Team(self.json[loop]["homeTeam"])
            away_team = Team(self.json[loop]["awayTeam"])
            self.home_teams.append(home_team)
            self.away_teams.append(away_team)
            self.home_lineups.append(Players(home_team.get_stat("lineup")))
            self.away_lineups.append(Players(away_team.get_stat("lineup")))
        self.home_lineup_valindex = []
        self.away_lineup_valindex = []
        self.home_div = []
        self.away_div = []
        self.home_path = []
        self.away_path = []
        self.analyze_lineups()
        self.home_lineup_fielding_valindex = []
        self.away_lineup_fielding_valindex = []
        self.analyze_defense()
        
    def pitcher_import(self):
        home_pitchers = []
        away_pitchers = []
        for loop in range(0, len(self.json)):
            home_pitchers.append(self.json[loop]["homePitcher"])
            away_pitchers.append(self.json[loop]["awayPitcher"])
        self.home_pitchers = Players(home_pitchers)
        self.away_pitchers = Players(away_pitchers)
        reordered_home = []
        for i in range(len(home_pitchers)):
            temp_h = home_pitchers[i]
            for j in range(len(self.home_pitchers.json)):
                if temp_h == self.home_pitchers.json[j]['id']:
                    reordered_home.append(self.home_pitchers.json[j])
        reordered_away = []
        for i in range(len(away_pitchers)):
            temp_a = away_pitchers[i]
            for j in range(len(self.away_pitchers.json)):
                if temp_a == self.away_pitchers.json[j]['id']:
                    reordered_away.append(self.away_pitchers.json[j])
        
        self.home_pitchers = Players(None, reordered_home)
        self.away_pitchers = Players(None, reordered_away)
        
        self.home_pitcher_valindex = []
        self.away_pitcher_valindex = []
        self.analyze_pitchers()
        
        
    def superdense_lineup_import(self):
        x = 5

    def get_day_json(self, season, day):
        self.req = requests.get(f'https://www.blaseball.com/database/games?day={day}&season={season}')
        if self.req.status_code != 200:
            print("OH NO, error accessing blaseball data stream!")
        return self.req.json()

    def get_stats(self, game):
        return self.json[game]

    def get_stat(self, game, stat_name):
        return self.json[game][f'{stat_name}']
        
    def get_pitcher_star_rating(self, players, idx):
        ruth = players.get_stat(idx, "ruthlessness")[0]
        over = players.get_stat(idx, "overpowerment")[0]
        unth = players.get_stat(idx, "unthwackability")[0]
        shak = players.get_stat(idx, "shakespearianism")[0]
        supp = players.get_stat(idx, "suppression")[0]
        cold = players.get_stat(idx, "coldness")[0]
        val_preweight = (ruth ** 0.4) * (over ** 0.15) * (unth ** 0.5) * (shak ** 0.1) * (supp ** 0.05) * (cold ** 0.025)
        return (val_preweight * 10) / 2
        

    def analyze_pitchers(self):
        h_valindexs = []
        a_valindexs = []
        for i in range(self.home_pitchers.num_players):
            h_valindexs.append(self.get_pitcher_star_rating(self.home_pitchers, i))
            a_valindexs.append(self.get_pitcher_star_rating(self.away_pitchers, i))
        self.home_pitcher_valindex = h_valindexs
        self.away_pitcher_valindex = a_valindexs

    def analyze_lineups(self):
        h_valindexs = []
        a_valindexs = []
        home_divs = []
        away_divs = []
        h_paths = []
        a_paths = []

        for i in range(0, len(self.home_lineups)):
            h_lnp = self.home_lineups[i]
            h_buoy = self.sum_of_stat(h_lnp, "buoyancy", True)[0]
            h_div = self.sum_of_stat(h_lnp, "divinity", True)[0]
            h_mox = self.sum_of_stat(h_lnp, "moxie", True)[0]
            h_thw = self.sum_of_stat(h_lnp, "thwackability", True)[0]
            h_path = self.sum_of_stat(h_lnp, "patheticism", True)[0]
            h_mux = self.sum_of_stat(h_lnp, "musclitude", True)[0]
            h_mart = self.sum_of_stat(h_lnp, "martyrdom", True)[0]

            a_lnp = self.away_lineups[i]
            a_buoy = self.sum_of_stat(a_lnp, "buoyancy", True)[0]
            a_div = self.sum_of_stat(a_lnp, "divinity", True)[0]
            a_mox = self.sum_of_stat(a_lnp, "moxie", True)[0]
            a_thw = self.sum_of_stat(a_lnp, "thwackability", True)[0]
            a_path = self.sum_of_stat(a_lnp, "patheticism", True)[0]
            a_mux = self.sum_of_stat(a_lnp, "musclitude", True)[0]
            a_mart = self.sum_of_stat(a_lnp, "martyrdom", True)[0]

            star_total_h = (h_thw ** 0.35) * (h_mox ** 0.075) * (h_div ** 0.35) * (h_mux ** 0.075) * ((1.0 - h_path) ** 0.05) * (h_mart ** 0.02) * (h_buoy ** 0.05)
            star_total_a = (a_thw ** 0.35) * (a_mox ** 0.075) * (a_div ** 0.35) * (a_mux ** 0.075) * ((1.0 - a_path) ** 0.05) * (a_mart ** 0.02) * (a_buoy ** 0.05)

            h_valindexs.append(((star_total_h * 10) / 2))
            a_valindexs.append((star_total_a * 10) / 2)
            # div
            home_divs.append(h_div)
            away_divs.append(a_div)
            # patheticism
            h_paths.append(h_path)
            a_paths.append(a_path)
        self.home_lineup_valindex = h_valindexs
        self.away_lineup_valindex = a_valindexs
        self.home_div = home_divs
        self.away_div = away_divs
        self.home_path = h_paths
        self.away_path = a_paths

    def sum_of_stat(self, p, stat_name, adjusted):
        total_stat = 0.0
        variance = 0.0
        active_players = p.num_players
        elsewhere_players = 0
        for j in range(0, p.num_players):
            res = p.get_stat(j, stat_name)
            total_stat = total_stat + res[0]
            if res[1]: #is_elsewhere
                elsewhere_players += 1
        mean = total_stat / (p.num_players - elsewhere_players)
        for j in range(0, p.num_players):
            res = p.get_stat(j, stat_name)
            stat_val = res[0]
            if not res[1]:
                variance += (mean - stat_val) ** 2
        std_dev = math.sqrt(variance / p.num_players)
        if adjusted:
            return [mean, std_dev]
        else:
            return [total_stat, std_dev]

    def analyze_defense(self):
        h_valindexs = []
        a_valindexs = []
        for i in range(0, len(self.home_lineups)):
            h_num = self.home_lineups[i].num_players / 2

            h_anti = self.sum_of_stat(self.home_lineups[i], "anticapitalism", True)[0]
            h_anti += self.home_pitchers.get_stat(i, "anticapitalism")[0] / h_num
            h_chas = self.sum_of_stat(self.home_lineups[i], "chasiness", True)[0]
            h_chas += self.home_pitchers.get_stat(i, "chasiness")[0] / h_num
            h_omni = self.sum_of_stat(self.home_lineups[i], "omniscience", True)[0]
            h_omni += self.home_pitchers.get_stat(i, "omniscience")[0] / h_num
            h_tena = self.sum_of_stat(self.home_lineups[i], "tenaciousness", True)[0]
            h_tena += self.home_pitchers.get_stat(i, "tenaciousness")[0] / h_num
            h_watc = self.sum_of_stat(self.home_lineups[i], "watchfulness", True)[0]
            h_watc += self.home_pitchers.get_stat(i, "watchfulness")[0] / h_num

            a_num = self.away_lineups[i].num_players / 2

            a_anti = self.sum_of_stat(self.away_lineups[i], "anticapitalism", True)[0]
            a_anti += self.away_pitchers.get_stat(i, "anticapitalism")[0] / a_num
            a_chas = self.sum_of_stat(self.away_lineups[i], "chasiness", True)[0]
            a_chas += self.away_pitchers.get_stat(i, "chasiness")[0] / a_num
            a_omni = self.sum_of_stat(self.away_lineups[i], "omniscience", True)[0]
            a_omni += self.away_pitchers.get_stat(i, "omniscience")[0] / a_num
            a_tena = self.sum_of_stat(self.away_lineups[i], "tenaciousness", True)[0]
            a_tena += self.away_pitchers.get_stat(i, "tenaciousness")[0] / a_num
            a_watc = self.sum_of_stat(self.away_lineups[i], "watchfulness", True)[0]
            a_watc += self.away_pitchers.get_stat(i, "watchfulness")[0] / a_num

            h_total = h_anti + h_chas + h_omni + h_tena + h_watc
            a_total = a_anti + a_chas + a_omni + a_tena + a_watc
            h_valindexs.append(h_total)
            a_valindexs.append(a_total)
        self.home_lineup_fielding_valindex = h_valindexs
        self.away_lineup_fielding_valindex = a_valindexs
    
    def print_series_info(self, home_nick):
        s_idx = self.json[0]["seriesIndex"]
        s_len = self.json[0]["seriesLength"]
        print(f'Game {s_idx} of {s_len}')
        if(s_idx > 1):
            while(s_idx > 1):
                cur_json = self.prev_json[(s_len - 1) - s_idx]
                cur_ptch = self.prev_pitchers[(s_len - 1) - s_idx]
                game_idx = -1
                # which game has the given home nickname
                for i in range(len(cur_json)):
                    if cur_json[i]["homeTeamNickname"] == home_nick:
                        game_idx = i
                # which pitchers are playing, and how hard
                home_p_idx = cur_json[game_idx]["homePitcher"]
                away_p_idx = cur_json[game_idx]["awayPitcher"]
                h_v = 0.0
                a_v = 0.0
                for i in range(len(cur_ptch.json)):
                    p_id = cur_ptch.json[i]["id"]
                    if home_p_idx == p_id:
                        h_v = round(self.get_pitcher_star_rating(cur_ptch, i), 3)
                        h_n = cur_ptch.get_stat(i, "name")
                        h_mod = cur_ptch.json[i]["permAttr"]
                    elif away_p_idx == p_id:
                        a_v = round(self.get_pitcher_star_rating(cur_ptch, i), 3)
                        a_n = cur_ptch.get_stat(i, "name")
                        a_mod = cur_ptch.json[i]["permAttr"]
                h_s = cur_json[game_idx]["homeScore"]
                a_s = cur_json[game_idx]["awayScore"]
                h_e = self.make_emoji(cur_json[game_idx]["homeTeamEmoji"], cur_json[game_idx]["homeTeamNickname"])
                a_e = self.make_emoji(cur_json[game_idx]["awayTeamEmoji"], cur_json[game_idx]["awayTeamNickname"])
                s_idx -= 1
                print(f'\n{s_len - s_idx} days ago:')
                print(f'{h_e} {h_s} VS {a_e} {a_s}')
                print(f'{h_n} VS {a_n}')
                print(f'{h_v} VS {a_v}')
                print(f'{h_mod} VS {a_mod}')
                
    def make_emoji(self, emoji_string, team_nick):
        moji = (chr)
        if team_nick == "Lift":
            moji = str(emoji_string)[0:1]
        else:
            moji = chr(int(emoji_string, 16))
        return moji
        
    def print_pitcher_info(self, loop):
        print('\n[PITCHERS]')
        print(f'{self.home_pitchers.get_stat(loop, "name")} VS {self.away_pitchers.get_stat(loop, "name")}')
        print(f'{" ".join(str(e) for e in self.home_pitchers.get_all_attr(loop))} VS {" ".join(str(e) for e in self.away_pitchers.get_all_attr(loop))}')
        print(f'{format(self.home_pitcher_valindex[loop], ".3f")} VS {format(self.away_pitcher_valindex[loop], ".3f")} -Overall pitcher value')
        h_mod, a_mod = "-----", "-----"
        h_fld = self.json[loop]["homePitcherMod"][0:5]
        a_fld = self.json[loop]["awayPitcherMod"][0:5]
        if len(h_fld) > 0:
            h_mod = h_fld
        if len(a_fld) > 0:
            a_mod = a_fld
        print(f'{h_mod} VS {a_mod}')
        print(f'{format(self.home_pitchers.get_stat(loop, "ruthlessness")[0], ".3f")} VS {format(self.away_pitchers.get_stat(loop, "ruthlessness")[0], ".3f")} -Ruthlessness (less balls, more strike zone)')
        print(f'{format(self.home_pitchers.get_stat(loop, "unthwackability")[0], ".3f")} VS {format(self.away_pitchers.get_stat(loop, "unthwackability")[0], ".3f")} -Unthwackability (more strikes and outs)')
        print(f'{format(self.home_pitchers.get_stat(loop, "overpowerment")[0], ".3f")} VS {format(self.away_pitchers.get_stat(loop, "overpowerment")[0], ".3f")} -Overpowerment (Lowers home runs but effects all hits)')
        print(f'{format(self.home_pitchers.get_stat(loop, "suppression")[0], ".3f")} VS {format(self.away_pitchers.get_stat(loop, "suppression")[0], ".3f")} -Suppression (Counters buoyancy and converts flyouts to groundouts)')
        print(f'{format(self.home_pitchers.get_stat(loop, "shakespearianism")[0], ".3f")} VS {format(self.away_pitchers.get_stat(loop, "shakespearianism")[0], ".3f")} -Shakespearianism (convert fielders choices into double plays)\n')

    def print_schedule(self):
        print_order = {}
        for loop in range(0, len(self.json)):
            pitch_v = (self.home_pitcher_valindex[loop] - self.away_pitcher_valindex[loop]) * 0.33
            line_v = (self.home_lineup_valindex[loop] - self.away_lineup_valindex[loop]) * 0.66
            print_order[loop] = abs(pitch_v + line_v)

        print("Play ball!")
        print(f"Blaseball Season { d.json[0]['season'] + 1} Day { d.json[0]['day'] + 1}")
        for loop in sorted(print_order, key=print_order.get):
            away_emoji = self.away_teams[loop].get_stat("emoji")
            away_nick = self.away_teams[loop].get_stat("nickname")
            away_pitchers = self.away_teams[loop].get_stat("rotation")
            a_moji = self.make_emoji(away_emoji, away_nick)

            home_emoji = self.home_teams[loop].get_stat("emoji")
            home_nick = self.home_teams[loop].get_stat("nickname")
            home_pitchers = self.home_teams[loop].get_stat("rotation")
            h_moji = self.make_emoji(home_emoji, home_nick)

            print("-----------------------------------------------------")
            home_name = self.home_teams[loop].get_stat("fullName")
            away_name = self.away_teams[loop].get_stat("fullName")
            
            print(f'{h_moji + home_name}\n      VS.                    {weather[self.json[loop]["weather"]].upper()}\n          {a_moji + away_name}')
            
            self.print_series_info(home_nick)
            
            self.print_pitcher_info(loop)
            
            print('[LINEUP]')
            print(f'{round(self.home_lineup_valindex[loop], 4)} VS {round(self.away_lineup_valindex[loop], 4)} -Star avg. of lineup')
            print(f'{round(self.home_lineup_fielding_valindex[loop], 4)} VS {round(self.away_lineup_fielding_valindex[loop],4)} -Defense of lineup')
            self.print_avg_stat_formatted([["divinity", "home"], ["divinity", "away"], ["patheticism", "home"], ["patheticism", "away"]], loop)
            self.print_avg_stat_formatted([["moxie", "home"], ["moxie", "away"], ["baseThirst", "home"], ["baseThirst", "away"]], loop)
            self.print_avg_stat_formatted([["thwackability", "home"], ["thwackability", "away"],["buoyancy", "home"], ["buoyancy", "away"]], loop)
            self.print_avg_stat_formatted([["laserlikeness", "home"], ["laserlikeness", "away"],["anticapitalism", "home"], ["anticapitalism", "away"]], loop)
            self.print_avg_stat_formatted([["omniscience", "home"], ["omniscience", "away"],["watchfulness", "home"], ["watchfulness", "away"]], loop)

    def print_avg_stat(self, stat_name, loop_x):
        h_stat = self.sum_of_stat(self.home_lineups[loop_x], stat_name, True)
        a_stat = self.sum_of_stat(self.away_lineups[loop_x], stat_name, True)
        print(f'{round(h_stat[0], 4)} | {round(a_stat[0], 4)}')
        print(f'    VS    [{str.swapcase(stat_name)} AVERAGE]')
        print(f'{round(h_stat[1], 4)} | {round(a_stat[1], 4)} - std dev')
        print(f'---------------------------------------------')

    def print_avg_stat_formatted(self, stat_list, loop_x):
        topbar = "-" * (1 + (len(stat_list) * 13))
        avgline = "|"
        nameline = "|"
        sdevline = "|"

        for statwhere in stat_list:
            if statwhere[1] == "home":
                statval = self.sum_of_stat(self.home_lineups[loop_x], statwhere[0], True)
            else:
                statval = self.sum_of_stat(self.away_lineups[loop_x], statwhere[0], True)
            avgline += f" AVG: {format(statval[0], '.3f')} |"
            nameinternal = str.swapcase(statwhere[1] + '  ' + statwhere[0][:4])
            nameline += " " + nameinternal + " |"
            sdevline += f" SD:  {format(statval[1], '.3f')} |"

        print(topbar)
        print(avgline)
        print(nameline)
        print(sdevline)

