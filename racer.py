import logging
import threading
import urllib
import heapq
import collections
import json
import time
import sys
import httplib
from urlparse import urlparse

'''
API information
'''
HEADERS = {
	'User-Agent' : 'Wikiracer User Agent', 
	'From' : 'scroboneya@yahoo.com'
}
HOST = 'en.wikipedia.org'
PATH = '/w/api.php'
PARAMETERS = {
	'action': 'query',
	'format': 'json',
	'prop': 'links',
	'pllimit': 500,
	'plnamespace': 0
}

'''
countries and highly connected pages to use a priority for breadth of search
'''
COUNTRIES = ['united states of america', 'united kingdom', 'great britain', 'united states', 'canada', 'germany', 'africa', 'japan', 'china', 'russia']
HIGHLY_CONNECTED = ['adolf hitler', '2007', '2006', '2004', '2005', '1967', '1990s', 'billy jean king', 'Deaths in 2004', 'star alliance destinations', 'list of accidents and incidents on commercial aircraft', 'list of town tramway systems in North America']

'''
structure to hold information about a wikipedia link
'''
Link = collections.namedtuple('Link', 'title parent')

'''
The Racer is used as half of a bidirectional BFS. Each Racer instance
checks the other's cache of collected links to find a match. If so, a 
path can connect the given pages.
'''
class Racer(threading.Thread):

	'''
	direction 	which way the racer is running (forward or back)
	page 		what page the racer is anchored at
	myCache		pages that connect to the racer's anchored page
	otherCache	pages that connect to the opposite racer's anchored page
	backVisited pages related, but not connected, to the back racer (used for ranking)
	queue		priority queue of links to crawl
	result		dict holding information about completion
	'''
	def __init__(self, name, direction, page, myCache, otherCache, backVisited, queue, result):
		self.direction = direction
		self.page = page
		self.myCache = myCache
		self.otherCache = otherCache
		self.backVisited = backVisited
		self.queue = queue
		self.result = result

		# initialize queue & cache with page
		if self.page not in self.myCache:
			self.myCache[self.page] = ''
			heapq.heappush(self.queue, (0, self.new_link(self.page, '')))

		threading.Thread.__init__(self, name = name)
		return

	'''
	Runs when process is started.
	'''
	def run(self):

		logging.info('Connecting to en.wikipedia.org')

		self.connect()

		logging.info('Starting with page: ' + self.page)

		while len(self.queue) > 0 and not self.result['isFound']:

			# take top 50 for batched request
			titles = self.get_titles(10)
			
			# get all links
			links = self.get_links(titles)

			# process the links depending on direction
			if self.direction is 'forward':
				self.check_forward(links)

			else:
				self.check_backward(links)

		# no path could be found
		if self.direction is 'forward' and len(self.queue) is 0:
			# THREADS TO FIX/ REMOVE
			#time.sleep(1)
			#self.run()
			#time.sleep(1)
			#if len(self.queue) > 0:
			#	self.run()

			if not self.result['isFound']:
				self.result['isFound'] = True
				self.result['path'] = 'No possible path.'

		# close connection before quitting
		self.close()

		logging.info('Closing Thread')

		return

	'''
	Gathers links for the forward running racer(s) and checks whether it 
	connects with the back running racer. Ranks links and adds them to queue.
	'''
	def check_forward(self, links):

		for link in links:

			# check my cache
			if link.title not in self.myCache:

				self.myCache[link.title] = link.parent

				# check other racer's cache
				if link.title in self.otherCache:

					self.result['isFound'] = True
					self.result['path'] = self.get_path(link.title)

					return

				rank = self.rank_link(link)

				# add link to queue
				heapq.heappush(self.queue, (rank, link))
	
	'''
	Gathers links for the back running racer(s) and confirms they are
	bidirectional (reversible). Any non-reversible links are still 
	added to the backVisited dictionary to help hone in forward
	searching racers.
	'''
	def check_backward(self, links):
		size = 50

		# batch together links to check for reversibility
		for i in range(0, len(links), size):

			# interupt if there is already a solution
			if self.result['isFound']:
				return

			batch = links[i: i + size]

			self.backVisited.update(batch)

			# weeds out which links are bidirectional
			batchLinks = self.get_reversible_links(batch)

			for link in batchLinks:

				if link.title not in self.myCache:
					self.myCache[link.title] = link.parent

					# check other racer's cache
					if link.title in self.otherCache:

						self.result['isFound'] = True
						self.result['path'] = self.get_path(link.title)

						return

					# add rank (not implemented)
					rank = 0

					# add link to queue
					heapq.heappush(self.queue, (rank, link))

	'''
	Collects all of the links associated with a group of pages. If the
	links are returned over several responses, they will all be collected.
	'''
	def get_links(self, titles):
		logging.info('(' + str(len(self.myCache)) + ') ' + titles)

		links = []
		isContinuing = True
		continueParam = ''
		plcontinueParam = ''

		while isContinuing:

			# build request string
			params = { 'titles': titles.encode('utf-8') }

			if continueParam != '':
				params['continue'] = continueParam.encode('utf-8')
				params['plcontinue'] = plcontinueParam.encode('utf-8')

			params.update(PARAMETERS)

			request = PATH + '?' + urllib.urlencode(params)

			# send request for links
			response = json.loads(self.get(request))

			# check if there are more links to get
			if 'continue' in response:
				continueParam = response['continue']['continue']
				plcontinueParam = response['continue']['plcontinue']

			else:
				isContinuing = False

			# check if page was entered not quite correct
			if 'normalized' in response['query']:
				normalized = response['query']['normalized'][0]
				self.myCache[normalized['to']] = normalized['from']

			# extract links from pages
			pages = response['query']['pages']

			for num, page in pages.iteritems():
				if 'links' in page:
					links.extend(list(map(lambda link: self.new_link(link['title'], page['title']), page['links'])))

		return links

	'''
	Filters a set of links by checking which are reversible,
	or bidirectional. That is the child can link to the parent 
	and the parent can link to the child.
	'''
	def get_reversible_links(self, links):

		titles = "|".join(list(map(lambda link: link.title, links)))
		parentTitles = "|".join(list(map(lambda link: link.parent, links)))

		logging.info('Checking for reversible: ' + titles)

		# built request
		params = { 
			'titles': titles.encode('utf-8'),
			'pltitles': parentTitles.encode('utf-8')
		}

		params.update(PARAMETERS)

		request = PATH + '?' + urllib.urlencode(params)

		# send request for reversible links
		response = json.loads(self.get(request))

		pages = response['query']['pages']

		reversibleLinks = []

		for num, page in pages.iteritems():

			# mark each page as visited & assign rank
			parent = self.backVisited[page['title']]
			self.backVisited[page['title']] = 2

			if 'links' in page:
				pageLinks = list(map(lambda link: link['title'], page['links']))

				# if parent is linked to in child page
				if parent in pageLinks:
					reversibleLinks.append(self.new_link(page['title'], parent))
					self.backVisited[page['title']] = 1

		return reversibleLinks

	'''
	Returns the rank value of a link.
	'''
	def rank_link(self, link):
		rank = 0

		# check link's parent country or highly connected
		if link.parent.lower() in COUNTRIES or link.parent.lower() in HIGHLY_CONNECTED:
			rank = rank - 1

		# if the link's parent is related to end pages
		if link.parent in self.backVisited:
			if isinstance(self.backVisited[link.parent], int):
				distance = self.backVisited[link.parent]
				rank = rank - (5 / distance)

		# if link is related to end pages
		if link.title in self.backVisited:
			if isinstance(self.backVisited[link.title], int):
				distance = self.backVisited[link.title]
				rank = rank - (10 / distance)

		# check for country or highly connected
		if link.title.lower() in COUNTRIES or link.title.lower() in HIGHLY_CONNECTED:
			rank = rank - 10

		return rank

	'''
	Combines the two halves of the recursive serach into a single path.
	'''
	def get_path(self, title):

		if self.direction is 'forward':
			path = self.get_path_rec(title, self.myCache, reverse=True)[:-1]
			path.extend(self.get_path_rec(title, self.otherCache)[1:])

		else:
			path = self.get_path_rec(title, self.otherCache, reverse=True)[:-1]
			path.extend(self.get_path_rec(title, self.myCache)[1:])

		return path

	'''
	Recursively builds a path of links by seraching through the cache.
	'''
	def get_path_rec(self, title, cache, reverse=False):
		parent = cache[title]

		if parent == '':
			return [[title]]

		else:
			if (reverse):
				result = self.get_path_rec(parent, cache, reverse)
				result[-1].append(title)
				result.append([title])
			else:
				result = self.get_path_rec(parent, cache, reverse)
				result[0].insert(0, title)
				result.insert(0, [title])


		return result

	'''
	Build titles string.
	'''
	def get_titles(self, count):
		titles = []

		for i in range(count):
			if len(self.queue) > 0:
				titles.append(heapq.heappop(self.queue)[1].title)

		return '|'.join(titles)

	'''
	Creates a new Link named tuple.
	'''
	def new_link(self, title, parent):
		return Link(title = title, parent = parent)

	'''
	Open an http connection with the host site.
	'''
	def connect(self):
		self.conn = httplib.HTTPSConnection(HOST)

	'''
	Send GET request to host.
	'''
	def get(self, request):
		start = time.time()

		self.conn.request("GET", request, headers = HEADERS)
		response = self.conn.getresponse()

		# track network time
		self.result['networkTime'] = self.result['networkTime'] + (time.time() - start)

		return response.read()

	'''
	Close the http connection.
	'''
	def close(self):
		self.conn.close()

