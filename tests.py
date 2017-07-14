import unittest
from racer import Racer
from racer import Link

WOLF = 'Gray Wolf'
CANADA = 'Canada'

class MyTest(unittest.TestCase):

	def setUp(self):
		self.forwardCache = {}
		self.backCache = {}
		self.backVisited = {}
		self.result = {}

		self.starter = Racer('start', 'forward', WOLF, self.forwardCache, self.backCache, self.backVisited, [], {'networkTime': 0})
		self.ender = Racer('end', 'back', CANADA, self.backCache, self.forwardCache, self.backVisited, [], {'networkTime': 0})

		self.starter.connect()
		self.ender.connect()

	def tearDown(self):

		self.starter.close()
		self.ender.close()


	'''
	get_titles
	'''
	def test_get_titles_one_title_request_one(self):

		self.assertEqual( self.starter.get_titles(1), WOLF)

	def test_get_titles_one_title_request_ten(self):

		self.assertEqual( self.starter.get_titles(10), WOLF)

	def test_get_titles_one_title_request_zero(self):

		self.assertEqual( self.starter.get_titles(0), '')


	def test_get_titles_five_titles_request_five(self):

		for i in range(4):
			self.starter.queue.append((0, Link(title=WOLF, parent='')))

		self.assertEqual( self.starter.get_titles(10), 'Gray Wolf|Gray Wolf|Gray Wolf|Gray Wolf|Gray Wolf')

	'''
	get_links
	'''
	def test_get_links_segment(self):
		titles = ['Circular segment', 'Division (disambiguation)', 'Fruit anatomy', 'Image segment', 
						'Line segment', 'Market segment', 'Network segment', 'Part (disambiguation)', 'Protocol data unit', 
						'Section (disambiguation)', 'Seg (disambiguation)', 'Segment (linguistics)', 'Segmentation (biology)', 
						'Segmentation (disambiguation)', 'Segmentation (memory)', 'Spherical segment', 'String (computer science)', 
						'Subdivision (disambiguation)', 'TCP segment', 'Television segment']

		links = list(map(lambda title: Link(title=title, parent='Segment'), titles))

		self.assertEqual( self.starter.get_links('Segment'), links )

	def test_get_links_jung_yong_jun(self):

		self.assertEqual( self.starter.get_links('Jung_Yong-jun'), [] )

	'''
	get_reversible_links
	'''
	def test_get_reversible_links_ice_cream_dessert(self):
		titles = ['Ice cream']
		links = list(map(lambda title: Link(title=title, parent='Dessert'), titles))

		self.ender.backVisited.update(links)

		self.assertEqual( self.ender.get_reversible_links(links), links )

	def test_get_reversible_links_ice_cream_camel(self):
		titles = ['Ice cream']
		links = list(map(lambda title: Link(title=title, parent='Camel'), titles))

		self.ender.backVisited.update(links)

		self.assertEqual( self.ender.get_reversible_links(links), [] )

	'''
	rank_link
	'''
	def test_rank_link_canada(self):
		rank = self.starter.rank_link(Link(title=CANADA, parent=''))

		self.assertEqual(rank, -10)

	def test_rank_link_wolf_related(self):
		self.starter.backVisited[WOLF] = 2
		rank = self.starter.rank_link(Link(title=WOLF, parent=''))

		self.assertEqual(rank, -5)

	def test_rank_link_wolf_parent_related(self):
		self.starter.backVisited[WOLF] = 2
		rank = self.starter.rank_link(Link(title='', parent=WOLF))

		self.assertEqual(rank, -2)

	def test_rank_link_canada_parent(self):
		rank = self.starter.rank_link(Link(title=WOLF, parent=CANADA))

		self.assertEqual(rank, -1)

	def test_rank_link_canada_and_related_and_parent_related(self):
		self.starter.backVisited[WOLF] = 2
		self.starter.backVisited[CANADA] = 2

		rank = self.starter.rank_link(Link(title=CANADA, parent=WOLF))

		self.assertEqual(rank, -17)

if __name__ == '__main__':
    unittest.main()