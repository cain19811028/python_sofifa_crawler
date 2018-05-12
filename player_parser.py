import datetime
import json
import os
import requests
import time
from dao import Dao
from lxml import html

DOMAIN = "https://sofifa.com/"
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def parse_player_data(player_id):
    url  = DOMAIN + "player/" + str(player_id)
    print(url)

    response = requests.get(url, headers = HEADERS)
    content = html.fromstring(response.text)

    # short_name, full_name, position, nationality
    player = content.xpath('//div[@class="player"]')[0]
    info = player.xpath('//div[@class="info"]')[0]
    short_name = info.xpath('//h1')[0].text_content().split(' (')[0]
    meta = info.xpath('//div[@class="meta"]/span')[0].text_content()
    full_name = meta.split('Age ')[0].split('  ')[0]
    position = meta.split('Age ')[0].split('  ')[1]
    position = position.replace(' ', ',')
    nationality = info.xpath('//div[@class="meta"]/span/a')[0].attrib['href']
    nationality = nationality.split('=')[1]

    # birthday, height, weight
    data = meta.split('Age ')[1]
    data = data.split(') ')
    birthday = data[0].split('(')[1]
    birthday = datetime.datetime.strptime(birthday, '%b %d, %Y')
    birthday = birthday.strftime('%Y%m%d')
    data = data[1].split(' ')
    height = data[0].replace("cm", "")
    weight = data[1].replace("kg", "")

    # foot
    teams = player.xpath('//div[@class="teams"]')[0]
    data = teams.xpath('//ul[@class="pl"]/li')[0].text_content()
    foot = data.split("\n")[2][:1]

    param = (player_id, full_name, short_name, birthday, nationality, position, height, weight, foot, player_id)
    Dao.upsert_sofifa_player(param)
    print(param)

def parse_rating_data(player_id):
    url  = DOMAIN + "player/" + str(player_id) + "/changeLog"

    response = requests.get(url, headers = HEADERS)
    content = html.fromstring(response.text)

    # rating
    table = content.xpath('//table[@class="table"]')[0]
    rating = table.xpath('//td[@class="text-clip"]/span')[0].text_content() 

    today = time.strftime('%Y%m%d', time.localtime(time.time()))

    rating_record = {}
    rating_record[today] = rating

    # change_log
    index = 0
    change_log = content.xpath('//article[@class="column"]/dl')[0]
    dt = change_log.xpath('//dt')
    dd = change_log.xpath('//dd')
    for d in dd:
        if "Overall Rating" in d.text_content():
            date = dt[index].text_content()[10:22].strip()
            date = datetime.datetime.strptime(date, '%b %d, %Y')
            date = date.strftime('%Y%m%d')
            
            rating = d.text_content().split('Overall Rating ')[1]
            rating = rating.split('  ')[1].split(' ')[0]
            rating_record[date] = rating
        index += 1

    param = (player_id, json.dumps(rating_record), player_id)
    Dao.upsert_rating(param)
    print(param)

"""
Main
"""
if __name__ == "__main__":
    
    PLAYER_SET = [158023]

    Dao.init()
    Dao.create_sofifa_player()
    Dao.create_rating()

    for player_id in PLAYER_SET:
        parse_player_data(player_id)
        parse_rating_data(player_id)
