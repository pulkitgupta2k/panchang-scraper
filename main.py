import enum
from os import O_APPEND
import requests
from bs4 import BeautifulSoup
import json
from pprint import pprint
import datetime
import calendar
from monthdelta import monthdelta
import time
import random
from pathlib import Path


week = {
    "Sun": "Sunday",
    "Mon": "Monday",
    "Tue": "Tuesday",
    "Wed": "Wednesday",
    "Thu": "Thursday",
    "Fri": "Friday",
    "Sat": "Saturday",
    "Sun": "Sunday"
}

def getSoup(link):
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0",
               "Content-Type": "text/html;charset=UTF-8"}
    # proxy_index = random.randint(0, len(ip_addresses) - 1)
    # proxy = {"http": ip_addresses[proxy_index], "https": ip_addresses[proxy_index]}
    req = requests.get(link, headers=headers)
    html = req.content
    soup = BeautifulSoup(html, 'html.parser')
    return soup


def lang(link_en, link_lang):
    with open("lang.json", encoding='utf-8') as f:
        pairs = json.load(f)
    soup_en = getSoup(link_en)
    soup_lang = getSoup(link_lang)
    table = soup_en.find("div", {"class": "dpTableCardWrapper"})
    cards = table.findAll("div", {"class": "dpTableCard"})
    row_keys = []
    row_values = []
    for card in cards[:10]:
        for row in card.findAll("div", {"class": "dpTableRow"}):
            row_keys.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableKey"})])
            row_values.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableValue"})])

        for i, key in enumerate(row_keys):
            if key.strip() == "" and row_values[i].strip() != "":
                row_keys[i] = row_keys[i-2]
    
    table = soup_lang.find("div", {"class": "dpTableCardWrapper"})
    cards = table.findAll("div", {"class": "dpTableCard"})
    row_keys_lang = []
    row_values = []
    for card in cards[:10]:
        for row in card.findAll("div", {"class": "dpTableRow"}):
            row_keys_lang.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableKey"})])
            row_values.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableValue"})])

        for i, key in enumerate(row_keys_lang):
            if key.strip() == "" and row_values[i].strip() != "":
                row_keys_lang[i] = row_keys_lang[i-2]


    for i in range(len(row_keys)):
        if row_keys[i] == '\xa0':
            continue
        pairs[row_keys_lang[i]] = row_keys[i]

    with open("lang.json", "w", encoding='utf-8') as f:
        json.dump(pairs, f)
    

def dayDetails(soup):
    pairs = {}
    # print(soup.find("div", {"class": "dpPHeaderRightContent"}))
    date = " ".join([x.text for x in soup.find(
        "div", {"class": "dpPHeaderRightContent"}).contents]).replace("  ", " ")
    pairs["date"] = date
    location = soup.find(
        "div", {"class": "dpPHeaderLeftWrapper"}).findAll("div")[-1]
    pairs["location"] = location.text.strip()
    table = soup.find("div", {"class": "dpTableCardWrapper"})
    cards = table.findAll("div", {"class": "dpTableCard"})
    row_keys = []
    row_values = []
    for card in cards[:10]:
        for row in card.findAll("div", {"class": "dpTableRow"}):
            row_keys.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableKey"})])
            row_values.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableValue"})])

        for i, key in enumerate(row_keys):
            if key.strip() == "" and row_values[i].strip() != "":
                row_keys[i] = row_keys[i-2]
    for i in range(len(row_keys)):
        if row_keys[i] == '\xa0':
            continue
        if row_keys[i] not in pairs.keys():
            pairs[row_keys[i]] = []
        pairs[row_keys[i]].append(row_values[i].strip("ⓘ'"))

    chandrabalam_tarabalam_soup = cards[10].find(
        "div", {"class": "dpTableRow"}).findAll("div", {"class": "dpTableCell"})
    pairs['Chandrabalam'] = []

    for chandrabalam in chandrabalam_tarabalam_soup[0].findAll("div", {"class": "dpStrengthGroup"}):
        upto = chandrabalam.find(
            "div", {"class": "dpMuhurtaTitle dpTitle"}).text.strip()
        values = [x.text.strip() for x in chandrabalam.findAll(
            "span", {"class": "dpRashiCell"})]
        pairs['Chandrabalam'].append({"upto": upto, "values": values})

    pairs['Tarabalam'] = []

    for tarabalam in chandrabalam_tarabalam_soup[1].findAll("div", {"class": "dpStrengthGroup"}):
        upto = tarabalam.find(
            "div", {"class": "dpMuhurtaTitle dpTitle"}).text.strip()
        values = [x.text.strip()
                  for x in tarabalam.findAll("span", {"class": "dpRashiCell"})]
        pairs['Tarabalam'].append({"upto": upto, "values": values})

    panchaka_lagna_soup = cards[11].find("div", {"class": "dpTableRow"}).findAll(
        "div", {"class": "dpTableCell dpTableValue"})

    panchaka = panchaka_lagna_soup[0]
    upto = panchaka.find("div", {"class": "dpTitle"}).text.strip()
    values = [x.text.strip() for x in panchaka.findAll(
        "div", {"class": "dpPanchangMuhurtaCell"})]
    pairs['Panchaka'] = [{"upto": upto, "values": values}]

    lagna = panchaka_lagna_soup[1]
    upto = lagna.find("div", {"class": "dpTitle"}).text.strip()
    values = [x.text.strip() for x in lagna.findAll(
        "div", {"class": "dpPanchangMuhurtaCell"})]
    pairs['lagna'] = [{"upto": upto, "values": values}]

    if len(cards) >= 13:
        festivals = [x.text.strip()
                     for x in cards[12].findAll("div", {"class": "dpEventName"})]
    else:
        festivals = ["NA"]

    pairs['festivals'] = festivals

    return pairs


def monthDetails(soup, month):
    pairs = {}
    days = soup.find_all(lambda tag: tag.name ==
                         'div' and tag.get('class') == ['dpMonthGridCell'])
    days.extend(soup.findAll("div", {"class": "dpHoliday dpMonthGridCell"}))
    days.extend(soup.findAll("div", {"class": "dpFocusedDay dpMonthGridCell"}))
    days.extend(soup.findAll("div", {"class": "dpCurrentDay dpMonthGridCell"}))
    days.extend(soup.findAll("div", {"class": "dpFocusedDay dpHolidayCellForPDFOnly dpMonthGridCell"}))

    for day in days:
        date = day.find("span", {"class": "dpBigDate"}).contents
        d = week[date[2].text]
        date = date[0]
        if len(date) == 1:
            date = "0"+date
        key = date + " " + month + " " + d
        local_date = day.find("span", {"class": "dpSmallDate"}).text.split(",")
        data = {"local_date": local_date}
        pairs[key] = data

    return pairs


def getMuhurat(year, location, location_name):
    data = {}
    links = [f"https://www.drikpanchang.com/shubh-dates/shubh-marriage-dates-with-muhurat.html?geoname-id={location}&year={year}",
             f"https://www.drikpanchang.com/shubh-dates/property-registration-auspicious-dates.html?geoname-id={location}&year={year}",
             f"https://www.drikpanchang.com/shubh-dates/vehicle-buying-auspicious-dates-with-muhurat.html?geoname-id={location}&year={year}",
             f"https://www.drikpanchang.com/shubh-dates/griha-pravesh-dates-with-muhurat.html?geoname-id={location}&year={year}"]
    cats = ["Vivah", "Property", "Vehicle", "GrihaPravesh"]
    for i, link in enumerate(links):
        cat = cats[i]
        soup = getSoup(link)
        months = soup.findAll("div", {"class": "dpCard"})
        for month in months:
            mahurat = month.find("div", {"class": "dpMuhurtaBlock"})
            for row in mahurat.findAll("div", {"class": "dpSingleBlock"}):
                if row.find('img')['alt'] == 'Inauspicious':
                    continue
                date_list = row.find(
                    "div", {"class": "dpMuhurtaBlockTitle"}).text.split(",")
                d = date_list[0].split(" ")[1]
                if len(d) != 2:
                    d = "0"+d
                date = d + " " + \
                    date_list[0].split(" ")[0] + date_list[1] + \
                    " " + date_list[2].strip()
                details = row.find("div", {"class": "dpCardMuhurtaDetail"}).findAll(
                    "div", {"class": "dpFlex"})
                muhurat = details[0].find(
                    "div", {"class": "dpValue dpFlexEqual"}).text.strip()
                nakshatra = details[1].find(
                    "div", {"class": "dpValue dpFlexEqual"}).text.strip()
                tithi = details[2].find(
                    "div", {"class": "dpValue dpFlexEqual"}).text.strip()
                if date not in data.keys():
                    data[date] = {}
                data[date].update(
                    {cats[i]: [{"Muhurat": [muhurat], "Nakshatra": [nakshatra], "Tithi": [tithi]}]})
                # print([date, muhurat, nakshatra, tithi])
    with open(f"muhurats/muhurats_{location_name}_{year}.json", "w") as f:
        json.dump(data, f)

def getMonth(link_day, link_month, month, year, location, location_name):
    num_days = calendar.monthrange(year, month)[1]
    days = [datetime.date(year, month, day) for day in range(1, num_days+1)]
    data = {}
    for day in days:
        time.sleep(0.5)
        day = day.strftime("%d/%m/%Y")
        print(day)
        link = f"{link_day}?geoname-id={location}&date={day}"
        pairs = dayDetails(getSoup(link))
        data[pairs['date']] = pairs
    day = days[0].strftime("%d/%m/%Y")
    link = f"{link_month}?date={day}"
    mon = " ".join(list(data.keys())[0].split()[1:3])
    add_pairs = monthDetails(getSoup(link), mon)
    for key, values in add_pairs.items():
        data[key].update(values)
        data[key]["Property"] = [{"Muhurat": ["NA"],
                            "Nakshatra": ["NA"], "Tithi": ["NA"]}]
        data[key]["Vivah"] = [{"Muhurat": ["NA"],
                         "Nakshatra": ["NA"], "Tithi": ["NA"]}]
        data[key]["Vehicle"] = [{"Muhurat": ["NA"],
                           "Nakshatra": ["NA"], "Tithi": ["NA"]}]
        data[key]["GrihaPravesh"] = [{"Muhurat": ["NA"],
                                "Nakshatra": ["NA"], "Tithi": ["NA"]}]

    with open(f"data/{location_name}_Month_{month}_Year_{year}_Language_en.json", "w") as f:
        json.dump(data, f)

def merge_muhurat(location_name, year, month, lang):
    with open(f"data/{location_name}_Month_{month}_Year_{year}_Language_{lang}.json") as f:
        data = json.load(f)
    with open(f"muhurats/muhurats_{location_name}_{year}.json") as f:
        muhurats = json.load(f)
    
    for key, value in muhurats.items():
        if key in data.keys():
            data[key].update(value)
    with open(f"data/{location_name}_Month_{month}_Year_{year}_Language_{lang}.json", "w") as f:
        json.dump(data, f)

def dayDetails_lang(soup):
    with open("lang.json", encoding='utf-8') as f:
        lang = json.load(f)
    pairs = {}
    # print(soup.find("div", {"class": "dpPHeaderRightContent"}))
    date = " ".join([x.text for x in soup.find(
        "div", {"class": "dpPHeaderRightContent"}).contents]).replace("  ", " ")
    pairs["date"] = date
    location = soup.find(
        "div", {"class": "dpPHeaderLeftWrapper"}).findAll("div")[-1]
    pairs["location"] = location.text.strip()
    table = soup.find("div", {"class": "dpTableCardWrapper"})
    cards = table.findAll("div", {"class": "dpTableCard"})
    row_keys = []
    row_values = []
    for card in cards[:10]:
        for row in card.findAll("div", {"class": "dpTableRow"}):
            row_keys.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableKey"})])
            row_values.extend([x.text for x in row.findAll(
                "div", {"class": "dpTableValue"})])

        for i, key in enumerate(row_keys):
            if key.strip() == "" and row_values[i].strip() != "":
                row_keys[i] = row_keys[i-2]
    for i in range(len(row_keys)):
        if row_keys[i] == '\xa0':
            continue
        if row_keys[i] not in lang.keys():
            break
        if lang[row_keys[i]] not in pairs.keys():
            try:
                pairs[lang[row_keys[i]]] = []
            except:
                break
        pairs[lang[row_keys[i]]].append(row_values[i].strip("ⓘ'"))

    chandrabalam_tarabalam_soup = cards[10].find(
        "div", {"class": "dpTableRow"}).findAll("div", {"class": "dpTableCell"})
    pairs['Chandrabalam'] = []

    for chandrabalam in chandrabalam_tarabalam_soup[0].findAll("div", {"class": "dpStrengthGroup"}):
        upto = chandrabalam.find(
            "div", {"class": "dpMuhurtaTitle dpTitle"}).text.strip()
        values = [x.text.strip() for x in chandrabalam.findAll(
            "span", {"class": "dpRashiCell"})]
        pairs['Chandrabalam'].append({"upto": upto, "values": values})

    pairs['Tarabalam'] = []

    for tarabalam in chandrabalam_tarabalam_soup[1].findAll("div", {"class": "dpStrengthGroup"}):
        upto = tarabalam.find(
            "div", {"class": "dpMuhurtaTitle dpTitle"}).text.strip()
        values = [x.text.strip()
                  for x in tarabalam.findAll("span", {"class": "dpRashiCell"})]
        pairs['Tarabalam'].append({"upto": upto, "values": values})

    panchaka_lagna_soup = cards[11].find("div", {"class": "dpTableRow"}).findAll(
        "div", {"class": "dpTableCell dpTableValue"})

    panchaka = panchaka_lagna_soup[0]
    upto = panchaka.find("div", {"class": "dpTitle"}).text.strip()
    values = [x.text.strip() for x in panchaka.findAll(
        "div", {"class": "dpPanchangMuhurtaCell"})]
    pairs['Panchaka'] = [{"upto": upto, "values": values}]

    lagna = panchaka_lagna_soup[1]
    upto = lagna.find("div", {"class": "dpTitle"}).text.strip()
    values = [x.text.strip() for x in lagna.findAll(
        "div", {"class": "dpPanchangMuhurtaCell"})]
    pairs['lagna'] = [{"upto": upto, "values": values}]

    if len(cards) >= 13:
        festivals = [x.text.strip()
                     for x in cards[12].findAll("div", {"class": "dpEventName"})]
    else:
        festivals = ["NA"]

    pairs['festivals'] = festivals
    return pairs

def getMonth_lang(link_day, link_month, month, year, location, location_name, lang):
    num_days = calendar.monthrange(year, month)[1]
    days = [datetime.date(year, month, day) for day in range(1, num_days+1)]
    data = {}
    for day in days:
        time.sleep(0.5)
        day_c = day.strftime("%d/%m/%Y")
        print(day_c)
        link = f"{link_day}?geoname-id={location}&date={day_c}&lang={lang}"
        pairs = dayDetails_lang(getSoup(link))
        data[day.strftime("%d %B %Y %A")] = pairs
    day = days[0].strftime("%d/%m/%Y")
    link = f"{link_month}?date={day}&lang=en"
    mon = " ".join(list(data.keys())[0].split()[1:3])
    add_pairs = monthDetails(getSoup(link), mon)
    for key, values in add_pairs.items():
        data[key].update(values)
        data[key]["Property"] = [{"Muhurat": ["NA"],
                            "Nakshatra": ["NA"], "Tithi": ["NA"]}]
        data[key]["Vivah"] = [{"Muhurat": ["NA"],
                         "Nakshatra": ["NA"], "Tithi": ["NA"]}]
        data[key]["Vehicle"] = [{"Muhurat": ["NA"],
                           "Nakshatra": ["NA"], "Tithi": ["NA"]}]
        data[key]["GrihaPravesh"] = [{"Muhurat": ["NA"],
                                "Nakshatra": ["NA"], "Tithi": ["NA"]}]

    with open(f"data/{location_name}_Month_{month}_Year_{year}_Language_{lang}.json", "w") as f:
        json.dump(data, f)

def clean():
    pathlist = Path("data/").rglob('*.json')
    for path in pathlist:
        path_in_str = str(path)
        with open(path_in_str, encoding='utf-8') as f:
            data = json.load(f)
        for key, value in data.items():
            if type(value) == list:
                continue
            data[key] = [value]
        with open(path_in_str, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

def location_driver(link_day, link_month, location_name, location, lang):
    start_date = datetime.date(2023, 1, 1)
    end_date = datetime.date(2025, 12, 1)
    days = []

    while start_date <= end_date:
        days.append(start_date)
        start_date += monthdelta(1)
    
    # getMuhurat(2021, location, location_name)
    # getMuhurat(2022, location, location_name)
    # getMuhurat(2023, location, location_name)
    # getMuhurat(2024, location, location_name)
    # getMuhurat(2025, location, location_name)

    for day in days:
        month = int(day.strftime("%m"))
        year = int(day.strftime("%Y"))
        getMonth(link_day, link_month, month, year, location, location_name)
        getMonth_lang(link_day, link_month, month, year, location, location_name, lang)
        merge_muhurat(location_name, year, month, "en")
        merge_muhurat(location_name, year, month, lang)
        time.sleep(5)

def clean_utf():
    pathlist = Path("data/").rglob('*.json')
    for path in pathlist:
        path_in_str = str(path)
        with open(path_in_str, "r", encoding='utf8') as f:
            data = json.load(f)
        with open(path_in_str, "w", encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False)
    

if __name__ == "__main__":
    # clean()
    
    link_day = "https://www.drikpanchang.com/marathi/panchang/marathi-day-panchang.html"
    link_month = "https://www.drikpanchang.com/marathi/panchang/marathi-month-panchang.html"
    location_driver(link_day, link_month, "Mumbai", "1275339", "mr")
    