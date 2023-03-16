import requests
from bs4 import BeautifulSoup

url = "https://www.nytimes.com/section/world"

# Fetches the HTML data from the URL
r = requests.get(url)

# Parses the HTML data into readable format
soup = BeautifulSoup(r.content, 'html.parser')

# Finds the most pressing global societal issue of the day
headlines = soup.find_all('h2', {'class': 'css-1cmu9py'})
result = []
for headline in headlines[:10]:
    article_title = headline.text
    article_summary = headline.find
