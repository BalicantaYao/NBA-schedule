import requests, json, csv
from bs4 import BeautifulSoup
import time
import os
import datetime

START_YEAR = "2014"
END_YEAR = "2015"

teams_file = open('../data/teams.json').read()
teams_json = json.loads(teams_file)
teams = teams_json['teams']

def find_team(location, nickname=''):
    # Los Angeles makes this tricky
    for team in teams:
        if nickname:
            if nickname in team.values():
                return team
        else:
            if location in team.values():
                return team

class EST(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(hours=4)
    def tzname(self, dt):
        return 'GMT -4'
    def dst(self, dt):
        return datetime.timedelta(0)

# Cool!: http://stackoverflow.com/questions/455580/json-datetime-between-python-and-javascript 
dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None

est = EST()

if __name__ == '__main__':
    for team in teams:
        team_url = 'http://espn.go.com/nba/team/schedule/_/name/{0}/{1}'.format(team['abbr'], team['full_name'])
        print team_url
        final_schedule = []

        r = requests.get(team_url)

        if r.status_code is 200:
            csv_file_name = '../data/'+ START_YEAR + '-' + END_YEAR + '/csv/' + team['full_name'] + '.csv'

            if not os.path.exists(os.path.dirname(csv_file_name)):
                os.makedirs(os.path.dirname(csv_file_name))

            csv_file = open(csv_file_name, 'w')

            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(['DATE','OPPONENT','ARENA','HOME'])

            soup = BeautifulSoup(r.text)
            schedule = soup.find_all('table')[0]
            rows = schedule.find_all('tr')
            for row in rows:
                if row['class'][0] == 'oddrow' or row['class'][0] == 'evenrow':
                    elements = row.find_all('td')
                    full_date = elements[0].contents[0]
                    day_of_week = full_date.split(',')[0]                   
                    month_abbr = full_date.split(',')[1].strip().split(' ')[0]
                    month = time.strptime(month_abbr, '%b').tm_mon
                    if month > 4:
                        year = START_YEAR
                    else:
                        year = END_YEAR
                    day = int(full_date.split(',')[1].strip().split(' ')[1])
                    full_date = '{0}-{1}-{2}'.format(month, day, year)
                    home_away = row.find_all('li', 'game-status')[0]
                    if home_away.contents[0] == 'vs':
                        isHome = True
                    else:
                        isHome = False
                    opponent_location = row.find('li', 'team-name').a.contents[0]
                    opponent_nickname = ''
                    if opponent_location == 'Los Angeles':
                        url = row.find('li', 'team-name').a['href']
                        if 'lakers' in url:
                            opponent_nickname = 'Lakers'
                        elif 'clipper' in url:
                            opponent_nickname = 'Clippers'
                    if opponent_location == 'NY Knicks':
                        opponent_location = 'New York'

                    tv = elements[3].contents[0]

                    tv_chan = tv.find('a')
                    if tv_chan is None:
                        tv = 'ABC'
                    else:
                        try:                            
                            tv = tv['alt']
                        except:
                            tv = tv
                    
                    if isHome:
                        place = find_team(team['location'])
                    else:
                        try:
                            place = find_team(opponent_location, opponent_nickname)
                        except:
                            place = find_team(opponent_location)
                        
                    where = {
                        'city': place['city'],
                        'arena': place['arena'],
                        'lat': place['lat'],
                        'lon': place['lon']
                    }

                    try:
                        opponent_info = find_team(opponent_location, opponent_nickname)
                    except:
                        opponent_info = find_team(opponent_location)

                    broadcast = {}
                    if not tv.strip():
                        broadcast['national'] = False
                        
                    else:
                        broadcast['national'] = True
                        broadcast['network'] = tv  

                    game = {
                        'when': {
                            'fullDate': full_date,
                            'monthAbbr': month_abbr,
                            'month': month,
                            'dayOfWeek': day_of_week,
                            'day': day
                        },
                        'isHomeGame': isHome,
                        'where': where,
                        'opponent' : opponent_info,
                        'tv': broadcast
                    }
                    final_schedule.append(game)
                    writer.writerow([full_date,
                                     game['opponent']['location'] + ' ' + game['opponent']['nickname'],
                                     place['arena'],
                                     isHome])
            json_file_name = '../data/' + START_YEAR + '-' + END_YEAR + '/json/' + team['full_name'] + '.json'

            if not os.path.exists(os.path.dirname(json_file_name)):
                os.makedirs(os.path.dirname(json_file_name))

            json_file = open(json_file_name, 'w')

            team_data = { 'team' : find_team(team['location']),
                          'schedule' : final_schedule }
            final_json = json.dumps(team_data, sort_keys=True, indent=2, default=dthandler)
            json_file.write(final_json)
            print '{0} {1} completed...'.format(team['location'], team['nickname'])
            json_file.close()
            csv_file.close()
            time.sleep(5)

        else:
            print 'Unable to get schedule for the {0} {1}'.format(team['city'], team['nickname'])
