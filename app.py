from flask import Flask, render_template, redirect
from datetime import datetime
from splinter import Browser
import lxml
import pymongo
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import time

app = Flask(__name__)


conn = 'mongodb://localhost:27017'
client = pymongo.MongoClient(conn)
db = client.mars
collection = db.scrape_results

 
def scrape():
	time_scraped = datetime.now()


	executable_path = {'executable_path': '/home/xanderroy/bin/chromedriver'}
	browser = Browser('chrome', **executable_path, headless=False)


	news_url = 'https://mars.nasa.gov/news/?page=0&per_page=40&order=publish_date+desc%2Ccreated_at+desc&search=&category=19%2C165%2C184%2C204&blank_scope=Latest'
	image_url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"
	weather_url = "https://twitter.com/marswxreport?lang=en"
	hemisphere_url = "https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars"
	facts_url = "https://space-facts.com/mars/"


	browser.visit(news_url)
	html = browser.html
	soup = BeautifulSoup(html, 'lxml-xml')

	featured_title =  soup.find('div', class_='content_title').a.text
	featured_teaser = soup.find('div', class_='article_teaser_body').text

	browser.click_link_by_partial_text(featured_title)
	html = browser.html
	soup = BeautifulSoup(html, 'lxml-xml')
	featured_story = soup.find('div', class_='wysiwyg_content').text


	browser.visit(image_url)
	html = browser.html
	soup = BeautifulSoup(html, 'lxml-xml')

	featured_image_url = str(soup.find('a', class_='fancybox').find(
		'div', class_="img").img).split('"')[5].replace(
		'-640x350', '_hires').replace('wallpaper', 'largesize')
	featured_image_url = "https://www.jpl.nasa.gov" + featured_image_url
	img_mouseover = soup.find('a', class_='fancybox').find_all(
		'div', class_="article_teaser_body")[1].text.strip()


	browser.visit(facts_url)
	html = browser.html
	soup = BeautifulSoup(html, 'lxml-xml')

	facts = pd.read_html(str(soup.find('table')), skiprows=0)[0]
	facts.columns=['Description','Values']
	facts.set_index('Description')
	facts = facts.to_html()


	browser.visit(hemisphere_url)
	html = browser.html
	soup = BeautifulSoup(html, 'lxml-xml')	

	hemisphere_image_urls = []
	hemispheres = soup.find_all('div', class_='item')
	for a in hemispheres:
		title = a.h3.text
		browser.click_link_by_partial_text(title)
		title.replace("Enhanced", "")
		html = browser.html
		soup = BeautifulSoup(html, 'lxml-xml')
		url = "https://astrogeology.usgs.gov" + soup.find('img', class_='wide-image')['src']
		hemisphere = {"Title" : title, "url": url}
		hemisphere_image_urls.append(hemisphere)
		browser.back()


	browser.visit(weather_url)
	html = browser.html
	soup = BeautifulSoup(html, 'lxml-xml')
	
	weather = soup.find("p", class_="TweetTextSize TweetTextSize--normal js-tweet-text tweet-text").text


	last_call = {
		'Time' : time_scraped,
		'Story_Title' : featured_title,
		'Story Teaser' : featured_teaser,
		'Story' : featured_story,
		'Img_url' : featured_image_url,
		'Img_Mouseover': img_mouseover,
		"Hemisphere_Imgs" : hemisphere_image_urls,
		'Weather' : weather,
		'facts' : facts

	}

	collection.insert_one(last_call)




@app.route("/")
def index():
	recent_scrape = collection.find().sort('Time', 1)
	for x in recent_scrape:
		Time = x['Time']
		Story_Title = x['Story_Title']
		Story_Teaser = x['Story Teaser']
		Story = x['Story']
		Img_url = x['Img_url']
		Img_Mouseover = x['Img_Mouseover']
		Hemisphere_Imgs = x['Hemisphere_Imgs']
		Weather = x['Weather']
		facts = x['facts']






	return render_template("index.html",Story_Title=Story_Title,
	 Story_Teaser=Story_Teaser, Story=Story, Img_url=Img_url,
	#   Time=Time,  
	 Img_Mouseover=Img_Mouseover, Hemisphere_Imgs=Hemisphere_Imgs,
	 Weather=Weather, facts=facts)

@app.route("/scrape")
def scraper():
	scrape()
	return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
