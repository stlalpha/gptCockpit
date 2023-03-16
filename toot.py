import requests
import xml.etree.ElementTree as ET

url = "http://feeds.bbci.co.uk/news/world/rss.xml"
response = requests.get(url)

root = ET.fromstring(response.content)
headlines = []

for item in root.findall("./channel/item")[:10]:
    title = item.find("title").text
    headlines.append(title)

for index, headline in enumerate(headlines, start=1):
    print(f"{index}. {headline}")
