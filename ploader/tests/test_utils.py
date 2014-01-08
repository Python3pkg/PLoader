from unittest import TestCase

import ploader.utils as utils


class TestUtils(TestCase):
	def test_size_formatting(self):
		self.assertEqual(utils.sizeof_fmt(-1), '-1.0bytes')
		self.assertEqual(utils.sizeof_fmt(0), '0.0bytes')
		self.assertEqual(utils.sizeof_fmt(1000000), '976.6KB')
		self.assertEqual(utils.sizeof_fmt(1000000000000000), '909.5TB')

	def test_url_filename_conversion(self):
		self.assertEqual(utils.url_to_filename('http://www.catb.org/jargon/html/S/schroedinbug.html'), 'schroedinbug.html')
		self.assertEqual(utils.url_to_filename('http://www.catb.org/jargon/html/S/'), '')

	def test_link_extractor(self):
		self.assertEqual(utils.clean_links('http://www.catb.org/jargon/html/S/schroedinbug.html\n'), ['http://www.catb.org/jargon/html/S/schroedinbug.html'])
		self.assertEqual(utils.clean_links('catb.org/jargon/html/S/schroedinbug.html'), [])
		self.assertEqual(utils.clean_links('http:// catb.org/jargon/html/S/schroedinbug.html'), [])
		self.assertEqual(utils.clean_links('http://www.catb.org/jargon/html/S/schroedinbug.html\nhttp://www.catb.org'), ['http://www.catb.org/jargon/html/S/schroedinbug.html', 'http://www.catb.org'])
		self.assertEqual(utils.clean_links('http://www.catb.org/jargon/html/S/schroedinbug.html http://www.catb.org'), ['http://www.catb.org/jargon/html/S/schroedinbug.html', 'http://www.catb.org'])
		self.assertEqual(utils.clean_links('http://www.catb.org/jargon/html/S/schroedinbug.html-http://www.catb.org'), ['http://www.catb.org/jargon/html/S/schroedinbug.html-http://www.catb.org'])