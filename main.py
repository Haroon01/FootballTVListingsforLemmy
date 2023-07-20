import requests
from bs4 import BeautifulSoup
import lxml
import time
from pythorhead import Lemmy
import os # for env file
from dotenv import load_dotenv

load_dotenv()

current_time = int(time.time() * 1000) # in milliseconds since 01/01/1970
twenty_four_hours = 86400000 # this many milliseconds in 24 hours
#twenty_four_hours = 864000000 # 10 days for testing purposes

base_url = "https://www.livesoccertv.com"
team_url = base_url + "/teams/england/arsenal/"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Referer": "https://www.livesoccertv.com/schedules/"
    }
response = requests.get(team_url, headers=headers)


def get_match_ref():
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "lxml")
        elements = soup.find("table", {"class": "schedules"})
        table_rows = elements.find_all("tr", {"class": "matchrow"})
        for tr in table_rows:
            table_data = tr.find_all("td")
            match_ref = table_data[4].find("a")["href"]
            match_title = table_data[4].find("a").text
            match_time = int(table_data[2].find("span", {"class": "ts"})["dv"])
            time_until_match = match_time - current_time
            if time_until_match < twenty_four_hours and time_until_match > 0: # if there is less than 24 hours until the match and the match isnt in the past
                return [match_ref, match_title]
    elif response.status_code == 429:
        print("Rate Limited. Sleeping...")
        time.sleep(60)

            
    else:
        print("Error getting match ref. Code: " + response.status_code)
        
        



def run():
    ref, match_title = get_match_ref()
    channels = {}
        
    match_page = requests.get(base_url + ref, headers=headers)
    if match_page.status_code == 200:
        
        match_soup = BeautifulSoup(match_page.content, "lxml")
        match_tab_cont = match_soup.find_all("div", {"class": "tab_container"})[1]
        match_sched_cont = match_tab_cont.find("div", {"id": "_schedules"})
        match_channel_cont = match_sched_cont.find("table", {"id": "wc_channels"})
        match_channel_rows = match_channel_cont.find_all("tr")[:-1]
        for row in match_channel_rows:
            #print(row.prettify())
            country_text = row.find("span").text
            channel_name = row.find("a").text
            if channel_name in channels:
                channels[channel_name].append(country_text)
            else:
                channels[channel_name] = [country_text]
        post_to_lemmy(*post_template(match_title, channels))
        
    else:
        print("Error accessing match page. Code: " + str(match_page.status_code))

def post_template(title, channels):
    txt = ""
    for chnl, countries in channels.items():
        txt += "\n### " + chnl + "\n"
        for country in countries:
            txt += "- " + country + "\n"

    return [title, txt]
        


def post_to_lemmy(title, body):
    #print(os.environ)
    lemmy = Lemmy(os.getenv("INSTANCE"))
    lemmy.log_in(os.getenv("USER"), os.getenv("PASS"))
    community_id = lemmy.discover_community(os.getenv("COMMUNITY"))
    print(os.getenv("INSTANCE"), os.getenv("USER"), os.getenv("PASS"), os.getenv("COMMUNITY"))
    post = lemmy.post.create(
        community_id, 
        "(Where to watch) " + title,
        body=body
        )
    if post:
        print("Successfully posted for " + title)
    else:
        print("Could not post for " + title)


while True:
    try:
        run()
        time.sleep(60)
    except TypeError:
        print("No match in the next 24 hours. Will try again tomorrow.")
        time.sleep(86400) # 24 hours


