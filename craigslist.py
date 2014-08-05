from bs4 import BeautifulSoup
from urllib2 import urlopen
from datetime import datetime
import smtplib
import config

# Craigslist search URL
mycity = 'austin'
ROOT_URL_CL = 'http://{0}.craigslist.org'.format(mycity)
BASE_URL = (ROOT_URL_CL + '/search/{0}?maxAsk={1}&query={2}&sort=date')


def parse_results(search_term, maxprice="9999", category="sso"):
    results = []
    search_term = search_term.strip().replace(' ', '+')
    search_url = BASE_URL.format(category, maxprice, search_term)
    soup = BeautifulSoup(urlopen(search_url).read())
    rows = soup.find('div', 'content').find_all('p', 'row')
    for row in rows:
        url = ROOT_URL_CL + row.a['href']
        # price = row.find('span', 'price').get_text()
        create_date = row.find('span', 'date').get_text()
        title = row.find_all('a')[1].get_text()
        results.append({'url': url, 'create_date': create_date, 'title': title})
    return results


def convert_CLdatetimetoPythondatetime(date, time):
# Create datetime object from info extracted in CL post
# inputs date and time are assumed to be strings
	datepost = datetime(int(date[:4]), int(date[5:7]), int(date[8:10]), 
	int(time[:2]), int(time[3:5]), int(time[6:8]))

	return datepost


def get_timeandlocation_posting(post_url):
# Extract time of posting and location of seller from
# a complete CL url
	soup = BeautifulSoup(urlopen(post_url).read())

	rowtime = soup.find('div', 'postinginfos').find('time')
	date, time = rowtime.get('datetime').split('T')
	time = time[:8]

	rowmap = soup.find(id='map')
	try: 
		longitude = rowmap.get('data-longitude')
		latitude = rowmap.get('data-latitude')
	except:
		longitude = []
		latitude = []

	return convert_CLdatetimetoPythondatetime(date, time), longitude, latitude


def send_text(phone_number, msg):
    fromaddr = "Craigslist Checker"
    toaddrs = phone_number + "@txt.att.net"
    msg = ("From: {0}\r\nTo: {1}\r\n\r\n{2}").format(fromaddr, toaddrs, msg)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(config.email['username'], config.email['password'])
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()


if __name__ == '__main__':
	PHONE_NUMBER = '5126959876'

	term = 'fridge | chest freezer'
	maxprice = '50'

	datenow = datetime.now()
	CLresults = parse_results(term, maxprice)
    
	new_posts = []
	new_posts_counter = 0
	for myresult in CLresults:
		print myresult
		post_url = myresult['url']

		datepost, longitude, latitude = get_timeandlocation_posting(post_url)
		print datepost, longitude, latitude
		datediff = datenow - datepost
		if datediff.total_seconds()/60. > 3600.:	break

		new_posts.append(post_url)
		new_posts_counter += 1
		
	print new_posts, new_posts_counter

"""
    # Send the SMS message if there are new results
    if has_new_records(results):
        message = "Hey - there are new Craigslist posts for: {0}".format(TERM.strip())
        print "[{0}] There are new results - sending text message to {0}".format(get_current_time(), PHONE_NUMBER)
        send_text(PHONE_NUMBER, message)
        write_results(results)
    else:
        print "[{0}] No new results - will try again later".format(get_current_time())
"""
