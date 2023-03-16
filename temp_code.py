# Python snippet to determine today's date

import datetime 
today = datetime.date.today() 
print("Today's date:", today)

# Python snippet to scrape Google to find information about the most pressing global societal issue of the day

import requests 
from bs4 import BeautifulSoup 

# search term 
search_term = 'most pressing global societal issue'

# Get request
url = f"https://www.google.com/search?q={search_term}"
r = requests.get(url) 
soup = BeautifulSoup(r.text, 'html.parser') 

# Find results