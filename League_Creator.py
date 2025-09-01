from pywebio.input import *
from pywebio.output import *
from pywebio import start_server

Leagues={}
selected_league=None

def home_page():
    global selected_league
    clear()
    put_html("<H1>Welcome to League Creator<H1>")
    if Leagues:
        put_text("Leagues:")
        league_choice=list(Leagues.keys())

        def leagues_option(name):
            global selected_league
            selected_league=name
            league_page()

        put_buttons(league_choice, onclick=leagues_option)
    else:
        put_text(" ")
    put_buttons(["+"], onclick=[create_league1])




def create_league1():
    clear()
    put_html("<H1>Create League<H2>")
    data=input_group("League info", [
        input("Enter teams name", name="name", required=True),
        select("Select number of teams", name="teams", options=[str(i) for i in range(2,21)], required=True)
    ])
    league_name=data["name"].strip()
    number_teams=int(data["teams"])

    if league_name in Leagues:
        toast("League already exists", color="error")
        home_page()
        return

    Leagues[league_name]={"teams":[], "fixtures":[], "results":{}, "points":{}}
    create_league2(league_name, number_teams)



def create_league2(league_name, number_teams):
    clear()
    put_html(f"<H1>Enter the names for the {number_teams} teams:")
    inputs=[]
    for i in range(number_teams):
        inputs.append(input(f"Team {i+1} name:", name=f"team{i}", required=True))

    data=input_group("Teams", inputs)
    teams=[data[f"team{i}"].strip() for i in range(number_teams)]
    Leagues[league_name]["teams"]=teams
    Leagues[league_name]["points"]={team: 0 for team in teams}
    create_fixtures(league_name)
    toast("League fixtures have been created", color='success')
    home_page()

def create_fixtures(league_name):
    teams=Leagues[league_name]["teams"][:]
    fixtures=[]

    if len(teams)%2 !=0:
        teams.append("BYE")

    num_rounds=len(teams)-1
    num_matches_per_round=len(teams)//2

    for round_num in range(num_rounds):
        round_matches=[]
        for i in range(num_matches_per_round):
            home=teams[i]
            away=teams[-i-1]
            if home !="BYE" and away!="BYE":
                match_id=f"Match-day{round_num+1} Match{i+1}"
                round_matches.append((match_id, home, away))
        teams.insert(1, teams.pop())
        fixtures.append(round_matches)
    Leagues[league_name]["fixtures"]=fixtures
    Leagues[league_name]["results"]={m[0]: None for r in fixtures for m in r}


def league_page():
    clear()
    put_html(f"<H1>{selected_league}</H1>")
    put_buttons(['Leaderboard', 'Fixtures', 'Results', 'Back'], onclick=[leaderboard, fixtures, results, home_page])

def fixtures():
    clear()
    put_html("<H1> Fixtures </H1>")
    put_buttons(["Back"], onclick=[league_page])
    fixtures_list=Leagues[selected_league]["fixtures"]
    for round_num, matches in enumerate(fixtures_list, start=1):
        put_html(f"<H3>Match-day {round_num} </H3>")
        for match_id, home, away in matches:
            result=Leagues[selected_league]["results"].get(match_id)
            result_str=f"{result[0]}-{result[1]}" if result else "Not played yet"
            put_text(f"{home} vs {away}| Result:{result_str}")
            put_buttons(["Edit result"], onclick=[lambda mid=match_id, h=home, a=away: edit_result(mid, h, a)])
    put_buttons(["Back"], onclick=[league_page])


def edit_result(match_id, home, away):
    clear()
    scores=input_group(f"Enter the scores for {home} vs {away}", [
        input(f"{home} score:", type=NUMBER, name='home_score', required=True),
        input(f"{away} score:", type=NUMBER, name='away_score', required=True)
    ])

    Leagues[selected_league]["results"][match_id]=(int(scores['home_score']), int(scores['away_score']))
    points_update(selected_league)
    toast("Result updated", color='success')
    fixtures()


def results():
    clear()
    put_html("<H1>Fixtures</H1>")
    for round_matches in Leagues[selected_league]["fixtures"]:
        for match_id, home, away in round_matches:
            result = Leagues[selected_league]["results"].get(match_id)
            result_str = f"{result[0]}-{result[1]}" if result else "Not played yet"
            put_text(f"{match_id}: {home} vs {away}| Result:{result_str}")
    put_buttons(['Back'], onclick=[league_page])

def points_update(league_name):
    teams=Leagues[league_name]["teams"]
    table = {t: {"played": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "PTS": 0} for t in teams}
    for round_matches in Leagues[league_name]["fixtures"]:
        for match_id, home, away in round_matches:
            result=Leagues[league_name]["results"].get(match_id)
            if result:
                home_score, away_score=result
                table[home]["played"]+=1
                table[away]["played"]+=1
                table[home]["GF"]+=home_score
                table[home]["GA"]+=away_score
                table[away]["GF"]+=away_score
                table[away]["GA"]+=home_score

                if home_score>away_score:
                    table[home]["W"]+=1
                    table[away]["L"]+=1
                    table[home]["PTS"]+=3
                elif away_score>home_score:
                    table[away]["W"]+=1
                    table[home]["L"]+=1
                    table[away]["PTS"]+=3
                else:
                    table[home]["D"]+=1
                    table[away]["D"]+=1
                    table[home]["PTS"]+=1
                    table[away]["PTS"]+=1

    Leagues[league_name]["points"]={t: table[t]["PTS"]for t in teams}
    Leagues[league_name]["table"]=table


def leaderboard():
    clear()
    put_html("<H1>Leaderboard</H1>")
    points_update(selected_league)
    table=Leagues[selected_league]["table"]
    rows=[]
    sorted_teams=sorted(table.items(), key=lambda kv: (kv[1]["PTS"], kv[1]["GF"] - kv[1]["GA"], kv[1]["GF"]), reverse=True)
    put_html(f"<H3>{selected_league}</H3>")
    put_text("#|Team|P|W|D|L|GF|GA|GD|PTS")
    for pos,(team, stats) in enumerate(sorted_teams, start=1):
        gd=stats["GF"] - stats["GA"]
        put_text(f"{pos}. {team} | {stats['played']} | {stats['W']} | {stats['D']} | {stats['L']} | "
                 f"{stats['GF']} | {stats['GA']} | {gd} | {stats['PTS']}")
    put_buttons(["Back"], onclick=[league_page])










if __name__ == '__main__':
    start_server(home_page, port=8080)
