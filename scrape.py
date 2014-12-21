#!/usr/bin/env python

'''
Scrape MixesDB

pip install beautifulsoup4, requests
'''

import sys
import cPickle as pickle
from bs4 import BeautifulSoup
import requests
from multiprocessing import Pool

url = r'http://www.mixesdb.com'
nthreads = 16

def artists_from_soup(soup):
    page_artists_list = soup.find('ul', id='catSubcatsList')
    artists = {artist.a.text: artist.a['href']
        for artist in page_artists_list.find_all('li')}
    return artists

def mixes_for_artist(artist_link):
    print "Getting mixes for %s" % artist_link
    page = requests.get(url+artist_link, timeout=30)
    print "Parsing soup for %s" % artist_link
    soup = BeautifulSoup(page.text)
    mix_list = soup.find('ul', id='catMixesList')
    mix_links = {mix.a.text: mix.a['href'] 
        for mix in mix_list.find_all('li')}
    return mix_links
    
def mix_from_link(link):
    print "Getting tracklist for %s" % artist_link
    page = requests.get(url+link, timeout=5)
    print "Parsing soup for %s" % artist_link
    soup = BeautifulSoup(page.text)
    categories = soup.find(id='mw-normal-catlinks')
    categories = {li.a.text: li.a['href']
        for li in categories.ul.find_all('li')}
    tracklist = soup.find(class_='list')
    if tracklist: 
        tracklist = tracklist.p
        if tracklist:
            tracklist = tracklist.text
    return (categories, tracklist)

def get_all_artists():
    try: return pickle.load(open('artists.pkl'))
    except: pass
    
    all_artists = {}
    link = r'/w/Category:Artist'
    while link is not None:
        print len(all_artists)
        page = requests.get(url+link)
        soup = BeautifulSoup(page.text)
        progress = soup.find(class_='catCount')
        all_artists.update(artists_from_soup(soup))
    
        link = soup.find('a', text='next 200')
        if link: link = link['href']
    print "Scraped %d artists" % len(all_artists)
    
    print "Saving list of artists"
    with open('artists.pkl', 'w') as fd:
        pickle.dump(all_artists, fd)
    
    return all_artists

def get_artist_mixes(all_artists):
    try: artist_mixes = pickle.load(open('mix_links.pkl'))
    except: artist_mixes = {}
    
    to_process = dict(all_artists)
    for artist in artist_mixes.keys():
        to_process.pop(artist, None)
    if len(to_process) == 0: return artist_mixes
    print "Getting mixes for %d artists" % len(to_process)
    
    pool = Pool(nthreads)
    new_artist_mixes = {}
    for artist_name, artist_link in to_process.items():
        new_artist_mixes[artist_name] = pool.apply_async(mixes_for_artist, (artist_link,))
    print "Waiting for all scrape tasks to complete"
    nartists = 0
    nmixes = 0
    for artist_name, async_result in new_artist_mixes.items():
        try:
            mixes = async_result.get()
            artist_mixes[artist_name] = mixes
            nartists += 1
            nmixes += len(mixes)
            print '%d - %s (%d mixes)' % (nartists, artist_name, len(mixes))
        except Exception, e:
            artist_mixes.pop(artist_name)
            print >>sys.stderr, e
    print "Found %d mixes" % nmixes
    
    print "Saving mix links"
    with open('mix_links.pkl', 'w') as fd:
        pickle.dump(artist_mixes, fd)
        
    pool.close()
    return artist_mixes
    
def get_tracklists(artist_mixes):
    try: all_mixes = pickle.load(open('mixes.pkl'))
    except: all_mixes = {}
    
    to_process = dict()
    for mixes in artist_mixes.values():
        to_process.update(mixes)
    for mix_name in all_mixes.keys():
        to_process.pop(mix_name, None)
    if len(to_process) == 0: return all_mixes
    print "Getting tracklists for %d mixes" % len(to_process)
    
    pool = Pool(nthreads)
    new_mixes = {}
    for mix_name, mix_link in to_process.items():
        new_mixes[mix_name] = pool.apply_async(mix_from_link, (mix_link,))
    print "Waiting for all scrape tasks to complete"
    ncompleted = 0
    for mix_name, async_result in new_mixes.items():
        try:
            result = async_result.get()
            all_mixes[mix_name] = result
            ncompleted += 1
        except Exception, e:
            all_mixes.pop(mix_name)
            print >>sys.stderr, e
    print "Scraped %d mixes" % ncompleted
        
    with open('mixes.pkl', 'w') as fd:
        pickle.dump(mixes, fd)
        
    pool.close()
    return all_mixes

if __name__ == '__main__':
    print "Getting all artists"
    all_artists = get_all_artists()
    print "Found %d artists" % len(all_artists)

    print "Getting mixes for each artist"
    artist_mixes = get_artist_mixes(all_artists)
    
    print "Getting tracklists for each mix"
    all_mixes = get_tracklists(artist_mixes)