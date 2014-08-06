Craiglist Checker
=================
Send a text when there's a new "For Sale" post for a given keyword or phrase.
The script sends an SMS message to a given phone number using GMail's SMTP protocol, so you'll need to add your GMail username and password to the config file.
An SMS message will only be sent if a new post appears (based on the full URL).
You will also receive an email with all new selected postings.
You can give a maximum price and maximum distance from your home (in kilometers). For the latter option, you also need to add your GPS coordinates into a config file.
gmail => myconfig_gmail.py
GPS => myposition.py

Setup
-----
Install the required libraries via pip:

    pip install -r requirements.txt

Usage
-----
    python craigslist-checker.py <search-term> <phone-number> <email-address> (<max-price>) (<max-dist>)

It's useful to setup a cronjob that will run the script every N minutes.
