from bs4 import BeautifulSoup
from urllib2 import urlopen
from datetime import datetime
import numpy as np
import sys
import smtplib
import myconfig_gmail		# store gmail account credentials
import myposition			# store GPS coordinates

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

	myrowtime = soup.find('div', 'postinginfos').findAll('time')
	rowtime = myrowtime[-1]
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


def print_datetime(mydatetime, myfile):
	myfile.write('{0} {1} {2} {3} {4} {5} {6}\n'.format(
	mydatetime.year, mydatetime.month, mydatetime.day, mydatetime.hour,
	mydatetime.minute, mydatetime.second, mydatetime.microsecond))


def read_datetimefile(filename):
	myfile = open(filename, 'r')
	mydatetime = myfile.readline().split()

	return datetime(int(mydatetime[0]), int(mydatetime[1]), int(mydatetime[2]),
	int(mydatetime[3]), int(mydatetime[4]), int(mydatetime[5]), int(mydatetime[6]))


EARTH_RADIUS = 6371.	# this is expressed in kilometers
def distance_longlat(coord1, coord2):
# Compute distance (in km) between 2 points
# where coordinates are given in (latitude, longitude)
# and both are expressed in degrees (e.g (30.12312, -97.12312))
	try:
		D1 = (coord1[0] - coord2[0])*np.pi/180.
		D2 = (coord1[1] - coord2[1])*np.pi/180.
	except:
		print 'Usage: coordinates must have 2 entries for ' \
		'latitude and longitude.'
		sys.exit(1)

	mydist = EARTH_RADIUS*np.sqrt(D1**2 + D2**2)
	return mydist


def send_text(phone_number, term):
    fromaddr = "Python Bot (Ben)"
    toaddrs = phone_number + "@txt.att.net"
    msg = ('New items were found in category {0}.\nPlease check your email.'.format(term))
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()	# used for encryption
    server.login(myconfig_gmail.email['username'], myconfig_gmail.email['password'])
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()


def send_email(myemail, term, maxprice, CL_posts):
	fromaddr = "Python Bot (Ben)"
	msg = 'Subject: New CL results in "{0}"\n'.format(term)
	msg = msg + 'Below are new results in "{0}" with maximum price of {1}$:\n\n'.format(term, maxprice)
	for myline in CL_posts:
		msg = msg + myline + '\n'
	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()	# used for encryption
	server.login(myconfig_gmail.email['username'], myconfig_gmail.email['password'])
	server.sendmail(fromaddr, myemail, msg)
	server.quit()


if __name__ == '__main__':
	try:
		term = sys.argv[1]
		PHONE_NUMBER = sys.argv[2].strip().replace('-', '')
		EMAIL_ADDRESS = sys.argv[3]
	except:
		print 'Usage: {0} <search_term> <phone_nb> <email_add> (<max_price>) (<max_dist>)'.format(sys.argv[0])
		sys.exit(1)

	try:
		maxprice = sys.argv[4]
		CLresults = parse_results(term, maxprice)
	except:
		maxprice = 'N/A'
		CLresults = parse_results(term)

	mycoord = myposition.longlatcoord
	try:
		maxdist = float(sys.argv[5])
	except:
		maxdist = []
	
	#print term, PHONE_NUMBER, EMAIL_ADDRESS, maxprice, maxdist

	lastcheck_file = 'lastcheck-{0}.dat'.format(term.replace('|','').replace(' ',''))
	logfile = '{0}.log'.format(term.replace('|','').replace(' ',''))
    
	new_posts = []
	new_posts_counter = 0
	lastcheck = read_datetimefile(lastcheck_file)
	len(CLresults)
	for myresult in CLresults:
		#print myresult
		post_url = myresult['url']

		datepost, longitude, latitude = get_timeandlocation_posting(post_url)
		#print datepost, longitude, latitude
		datediff = datepost - lastcheck
		if datediff.total_seconds() < 0.:	break

		if maxdist == [] or longitude == [] or \
		distance_longlat(mycoord, (float(latitude), float(longitude))) < maxdist:
			new_posts.append(post_url)
			new_posts_counter += 1
		
	#print new_posts, new_posts_counter

	# Update time of lastcheck
	fchk = open(lastcheck_file, 'w')
	print_datetime(datetime.now(), fchk) 
	fchk.close()

	flog = open(logfile, 'a')
	print_datetime(datetime.now(), flog) 
	for myline in new_posts:	
		flog.write(myline + '\n')
	flog.write('\n')
	flog.close()

	# Send information if new items found
	if new_posts_counter > 0:
		send_text(PHONE_NUMBER, term)
		send_email(EMAIL_ADDRESS, term, maxprice, new_posts)
