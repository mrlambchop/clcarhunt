#!/usr/bin/env python

import os, urllib, re
import time, sys, math, string
import xml.dom.minidom
from urlparse import urlparse

#global variables

'''
min price of the car
'''
minPrice = 14000

'''
keyPhrases list contains those key words or phrases that we want in search results
'''

keyPhrases = ['audi%20avant', 'audi%20wagon', 'audi%20a3', 'audi%20q5', 'audi%20a7', 'subaru%20outback', 'bmw%20wagon', 'ford%20edge', 'outback%20sport']

'''
postTypes list contains that types of Craigslist ads.  Eg, "web" signifies ads appearing in Craigslist's web developer/engineer ads
this value is part of the RSS feed url
'''

postTypes = ['cto']

'''
citiesFile contains a text list with a Craigslist city tags (e.g, "los angeles"), one per line
like the postTypes values, it is used to construct the respective RSS urls
'''

citiesFile = "clcities.txt"

'''
dataFile contains the repository of found links; this file is loaded and updated with each program execution
caution: once it exceeds 50,000 entries, it may be become cumbersome.  However, each entry has a time value, so a separate script
can periodically clean the list
'''

dataFile = "cldata.txt"

newOutput = []
dataContainer = []
pageContainer = []
urlContainer = []
items = []
entries = []

########################################################
def loadDataFile():
	
	global dataContainer
	global dataFile
	
	try:
		
		dataContainer += open(dataFile,"rU").readlines()
		
	except:
	
		pass
	
#######################################################
def saveDataFile():
	
	global dataContainer
	global newOutput
	global dataFile
		
	dataContainer.extend(newOutput)
	dataContainer.sort()
	data = ""
	
	for item in dataContainer:
		
		if len(item) > 10:
			data += item
	
	
	file = open(dataFile,"w")
	print >>file,data
	
########################################################
def readTheWebContent():
	
	'''
	reads the remote feeds and stores them in a list
	'''
		
	global pageContainer
	global urlContainer
	
	for thisURL in urlContainer:
		f = urllib.urlopen(thisURL)
		s = f.read()
		f.close()
		pageContainer.append(s)

########################################################
def parseFeeds():
	
	'''
	basic XML parse using minidom
	'''
	
	global pageContainer
	global entries
	global items
	
	for xmlData in pageContainer:
		
		try:
			dom = xml.dom.minidom.parseString(xmlData)
			x = 0
			for eNode in dom.getElementsByTagName('item'):
				if (len(eNode.getElementsByTagName('description')[0].firstChild.data) > 0):
					tl = eNode.getElementsByTagName('link')[0].firstChild.data
					tt = eNode.getElementsByTagName('title')[0].firstChild.data
					td = eNode.getElementsByTagName('description')[0].firstChild.data
                                        
					items.append({
						'link' : tl,
						'title' : tt,
						'description': td
						
					})
		except:
			pass
			

######################################################
def fetchFeedURLS():
	
	"""
	builds and puts the feed URLS into a list
	"""
	global urlContainer
	global citiesFile
	buf = []
	buf += open(citiesFile,"rU").readlines()
		
	for line in buf:
		
		for t in postTypes:

   		   for k in keyPhrases:

			#url = "http://" + line.rstrip() + ".craigslist.org/" + t +"/index.rss"
			url = "http://" + line.rstrip() + ".craigslist.org/search/" + t +"?minAsk=" + str(minPrice) + "&query=" + k + "&srchType=T&format=rss"
			urlContainer.append(url)

####################################################
def checkIfWanted(title,description):
	return True

	'''
	iterates through the list of keyPhrases. If one is found, the link is used
	'''
	
	global keyPhrases
	good = False
	
	for ph in keyPhrases:
		
		test = "\s" + ph + "\s"
		ck = re.compile(test, re.IGNORECASE)
		m1 = ck.findall(title)
		m2 = ck.findall(description)
		
		if len(m1) > 0:
			return True
		
		if len(m2) > 0:
			return True
		
	return good
		
########################################################
def searchLink(start,end,link):
	
	'''
	a very fast binary search of the sorted link array to check if link has already been found
	'''
	
	global dataContainer
	if end < start:
		return -1
	
	length = len(link)
	
	if length > 0:
		
		mid = start +((end-start)/2)
		d = dataContainer[mid].split(",")
		test = d[0]
		
		if test > link:
			return searchLink(start,mid-1,link)
		elif link > test:
			return searchLink(mid+1,end,link)
		else:
			return 1
	else:
		return -1
	
########################################################
def findLink(l):
	
	global dataContainer
	
	if len(dataContainer) > 1:
		return searchLink(0,len(dataContainer)-1,l)
	else:
		return -1
	

#######################################################
def processOutput():
	
	out = ""
	ind = 0
	global dataContainer
	global newOutput
	global items

        print "Found", len(items), "cars"
	
	for e in items:
		
		link = e['link']
		title = e['title']
		desc = e['description']
		
		passed = True #checkIfWanted(title,desc)
						
		if passed == True:
			
			newLink = findLink(link)
					
			if newLink == -1:
				
				ne = link + "," + str(time.time()) + "\n"
				newOutput.append(ne)
				out += title + "\n"
				out += link + "\n"
				
				commute = "telecommuting is ok"
				ck = re.compile(commute, re.IGNORECASE)
				tc = ck.findall(desc)
				if len(tc) > 0:
					out += "Telecommuting is ok\n"
					
				out += urlparse(link).netloc.split('.')[0] + "\n"
				out += "---------------------------\n"
					
	return out
#####################################################
#main

t1 = time.time()
loadDataFile()
fetchFeedURLS()
readTheWebContent()
t2 = time.time()
parseFeeds()
t3 = time.time()
out = processOutput().encode('utf-8')
saveDataFile()

'''
output is generated only if we have new entries.  If executed via a cron job, the output will be sent as a system email
the time values in the output are useful to gauge if the data file is becoming unwieldly.  

The run-time for this script is about 1.6 seconds per feed, and almost all of that is accessing the url. 
'''

if len(newOutput) > 0:
	
	print "After reading web content, clock is at " + str(t2 - t1) + " seconds"
	print "Found " + str(len(items)) + " items. clock is at  " + str(t3 - t1) + " seconds"
	print "Done.  Found " + str(len(newOutput))+ " new items.  Procedure took " + str(time.time() - t1) + " seconds\n"
	print out
	
sys.exit()
