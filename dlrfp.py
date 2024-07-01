#!/usr/bin/env python3

import re
from urllib.request import urlopen
from urllib.error import URLError, HTTPError
from time import gmtime, strftime
import xml.etree.ElementTree as ET

def get_each_programme_page(programme_link):
	"""
	Crawl through each page of a programme and put each of them in a list
	"""
	page = 1
	programme = programme_link
	programme_pages = []

	try:
		urlopen(programme)
	except URLError as e:
		print(e.reason) 
	except URLError as e:
		print(e.reason)
	else:
		while True:
			with urlopen(f'{programme}?p={page}') as response:
				# Check if there is a redirection if a given page doesn't exist
				# ?=1 exist but is apparently redirected directly
				if response.url == programme and page != 1: 
					break
				html = response.read()
				# Now it seems there is no more redirection but an 'Aucun résultat' page
				if re.search(r'Aucun r\\xc3\\xa9sultat', f'{html}') != None:
					break
				
				programme_pages.append(f'{programme}?p={page}')
				print(f'Page {page} done: {response.url}')
			page += 1
	return programme_pages
	
def get_each_episode_page(programme_pages_list):
	"""
	Get all episodes of programme pages in a list
	"""
	programme_pages = programme_pages_list
	all_episodes = []

	for page in programme_pages:
		with urlopen(f'{page}') as response:
			html = response.read()
			episode_path = re.findall(r'variant:\"\S+\",href:\"(\S+)\",brandName:', f'{html}')
			
			for ep in episode_path:
				all_episodes.append(f'https://www.radiofrance.fr{ep}')
				
			print(f'All episodes added from {page}')

	return all_episodes
	
def get_episode_info(episode_page_link):
	"""
	Get all information from an episode's link
	"""	
	episode_link = episode_page_link
	
	all_info = {}

	with urlopen(f'{episode_link}') as response:
		html = f'{response.read()}'
		#with open('ep_link.txt', 'w') as html_to_dump:
		#	html_to_dump.writelines(f'{html}')

		episode_info = re.findall(r'content:\{(.+]),selections', html)[0]
		#print(episode_info)

		title = re.findall(r'id:\"\S{36}\",title:\"(.+)\",conceptTitle:', episode_info)[0]

		title = prettify(title)
		all_info['title'] = title
		#print(title)
		
		no_audio = re.search('manifestations:\[]', html)
		if no_audio != None:
			# If no audio available
			all_info['audio'] = ''
		else:
			# Test if there is a spaces in the URL
			audio_link_with_space = re.search(r'model:\"ManifestationAudio\",id:\"\S{36}\",url:"(\S+)",duration:', html)
			
			if audio_link_with_space !=None:
				audio_link = re.findall(r'model:\"ManifestationAudio\",id:\"\S{36}\",url:"(\S+)",duration:', html)[0]
				all_info['audio'] = audio_link
				#print(audio_link)
			else:
				# If yes, replace them with %20 for a valid URL
				audio_spaced= re.findall(r'model:\"ManifestationAudio\",id:\"\S{36}\",url:"(.+)",duration:', html)[0]
				audio_link = audio_spaced.replace(' ', '%20')
				all_info['audio'] = audio_link
		
		site_url = re.findall(r'siteUrl:"(\S+)",maSaisonRadio:', html)[0]
		#print(site_url)		
		
		ep_path_part = re.findall(r',path:\"(\S+/podcasts/\S+/\S+)\",migrated:', episode_info)[0]
		path = f'{site_url}/{ep_path_part}'
		all_info['path'] = path
		#print(path)		
		
		# Get publication time in epoch
		published_date_epoch = re.findall(r'publishedDate:(\d+),brandEnums:', episode_info)[0]
		
		# Convert it in a time.struct_time object
		published_date = gmtime(int(published_date_epoch))
		# RFC822 expected for an RSS feeed
		final_date = strftime("%a, %d %b %Y %H:%M:%S +0000", published_date)
		all_info['published_date'] = final_date
		#print(final_date)
		
		ressources_unescaped = re.findall(r'value:"(.+?)"', episode_info)
		
		# Make them a bit prettier
		ressources = []		
		for info in ressources_unescaped:
			info = prettify(info)
			ressources.append(info)
			
		all_info['ressources'] = ressources
		
	return all_info
	
def add_episode_to_rss(episode_info_dic, podcast_title, podcast_link, podcast_descr):
	"""
	Create an RSS XML file from a dictionary of episodes information
	"""	
	episode_info = episode_info_dic
	rss_file = 'rssfeed.xml'
	title = podcast_title
	link = podcast_link
	description = podcast_descr
	
	# If the xml file doesn't exist, create it
	try:
		with open(rss_file, 'r'):
			pass
	except FileNotFoundError:
		with open(rss_file, 'wb') as xml_file:
			# Create the RSS file base
			root = ET.Element("rss")
			root.set("version", "2.0")
			
			channel = ET.Element("channel")
			root.append(channel)
			
			node1 = ET.SubElement(channel, "title")
			node1.text = title
						
			node2= ET.SubElement(channel, "link")
			node2.text = link

			node3= ET.SubElement(channel, "description")
			node3.text = description
			
			tree = ET.ElementTree(root)			
			tree.write(xml_file, encoding = "UTF-8", xml_declaration = True)
			
	# Add episode informations to the existing file
	
	# First parse the existing XML file
	
	# Create element tree object 
	tree = ET.parse(rss_file) 
	
	# Get root element 
	root = tree.getroot()
	# Find channel element
	channel = root.find("./channel")
	# Add all the episode info in an item element
	item= ET.Element("item")
	channel.append(item)
	
	item_title = ET.SubElement(item, "title")
	item_title.text = episode_info['title']
	
	item_date = ET.SubElement(item, "pubDate")
	item_date.text = episode_info['published_date']

	item_link = ET.SubElement(item, "link")
	item_link.text = episode_info['path']
	
	# If no audio available
	if episode_info['audio'] != '':
		item_enclosure = ET.SubElement(item, 'enclosure')
		item_enclosure.set("url", episode_info['audio'])
		item_enclosure.set("length", '0')
		item_enclosure.set("type", "audio/mpeg")
	
	item_description = ET.SubElement(item, "description")
	
	# All ressources from the list to a single string
	ressources = ""
	for info in episode_info['ressources']:
		ressources += f'\n{info}'
	
	item_description.text = ressources
	
	with open(rss_file, 'wb') as xml_file:
		tree_to_write = ET.ElementTree(root)
		tree_to_write.write(xml_file)

def prettify(string):
	"""
	Replace some escaped characters in a given string
	"""
	string_base = string
	string_base = string_base.replace('\\\\u003C/strong>', '')
	string_base = string_base.replace('\\\\u003Cstrong>', '')
	string_base = string_base.replace('\\\\u003C/em>', '')
	string_base = string_base.replace('\\\\u003Cem>', '')
	string_base = string_base.replace('\\\\u003Cbr>', '')
	string_base = string_base.replace('\\\\u003C/br>', '')
	string_base = string_base.replace("\\'","'")
	string_base = string_base.replace("\'","'")
	string_base = string_base.replace('\\xc3\\xa9', 'é')
	string_base = string_base.replace('\xc3\xa9', 'é')
	string_base = string_base.replace('\\xc3\\xa8', 'è')
	string_base = string_base.replace('\xc3\xa8', 'è')	
	string_base = string_base.replace('\\xe2\\x80\\x99', "'")
	string_base = string_base.replace('\xe2\x80\x99', "'")
	string_base = string_base.replace('\\xe2\\x80\\x98', "'")
	string_base = string_base.replace('\xe2\x80\x98', "'")
	string_base = string_base.replace('\\xc2\\xb0', '°')
	string_base = string_base.replace('\xc2\xb0', '°')
	string_base = string_base.replace('\\xc2\\xab', '«')
	string_base = string_base.replace('\xc2\xab', '«')
	string_base = string_base.replace('\\xc2\\xbb', '»')
	string_base = string_base.replace('\xc2\xbb', '»')
	string_base = string_base.replace('\\xc3\\xa0', 'à')
	string_base = string_base.replace('\xc3\xa0', 'à')
	string_base = string_base.replace('\\xc3\\xaa', 'ê')
	string_base = string_base.replace('\xc3\xaa', 'ê')
	string_base = string_base.replace('\\xc3\\xab', 'ë')
	string_base = string_base.replace('\xc3\xab', 'ë')
	string_base = string_base.replace('\\xc3\\xb4', 'ô')
	string_base = string_base.replace('\xc3\xb4', 'ô')
	string_base = string_base.replace('\\xc3\\xa7', 'ç')
	string_base = string_base.replace('\xc3\xa7', 'ç')
	string_base = string_base.replace('\\xc3\\xb9', 'ù')
	string_base = string_base.replace('\xc3\xb9', 'ù')
	string_base = string_base.replace('\\xc3\\xbb', 'û')
	string_base = string_base.replace('\xc3\xbb', 'û')
	string_base = string_base.replace('\\xc5\\x93', 'œ')
	string_base = string_base.replace('\xc5\x93', 'œ')
	string_base = string_base.replace('\\xc3\\xae', 'î')
	string_base = string_base.replace('\xc3\xae', 'î')
	string_base = string_base.replace('\\xe2\\x80\\xa6', '…')
	string_base = string_base.replace('\xe2\x80\xa6', '…')
	string_base = string_base.replace('\\xe2\\x80\\x93', '–')
	string_base = string_base.replace('\xe2\x80\x93', '–')
	string_base = string_base.replace('\\xc2\\xa0', ' ')
	string_base = string_base.replace('\xc2\xa0', ' ')
	
	return string_base
	
if __name__ == '__main__':
	# Get all page link of the programme in a list
	programme_pages_list = get_each_programme_page("https://www.radiofrance.fr/franceinter/podcasts/sur-les-epaules-de-darwin")
	# Get all the episode of each page in a list
	episodes_pages_list = get_each_episode_page(programme_pages_list)

	# Put the list in a file if wanted
	"""
	with open('episode_list.txt', 'a') as file_to_write:
		for ep in episodes_pages_list:
			file_to_write.write(f'{ep}\n')

	print(f'File gathering episode links written in: episode_list.txt')
	"""
	# Get the episode from a file, after manual curating for example
	"""
	episodes_pages_list = []
	with open('episode_links_curated.txt', 'r') as reader:
		# Read the file line by line
		line = reader.readline()
		while line != '':  # The EOF char is an empty string
			line = line.replace('\n','')
			episodes_pages_list.append(line)
			line = reader.readline()	
	"""
	
	# Prepare descriptive elements necessary to the RSS feed
	podcast_title = "Sur les épaules de Darwin"
	podcast_link = 'https://www.radiofrance.fr/franceinter/podcasts/sur-les-epaules-de-darwin/'
	podcast_descr = 'Un voyage avec ses escales dans la recherche, la culture et la vie sociale, accompagné par des textes et voix d’écrivains, de scientifiques et de poètes.'

	# From each episode link, get the info and add them to the feed
	for ep in episodes_pages_list:
		ep_info_dic = get_episode_info(ep)
		add_episode_to_rss(ep_info_dic, podcast_title, podcast_link, podcast_descr)
		print(f'Episode added: {ep}')
	
	print("Feed created in: rssfeed.xml")

