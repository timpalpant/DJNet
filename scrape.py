#!/usr/bin/env python

'''
Scrape MixesDB

pip install beautifulsoup4, requests
'''

import sys
import cPickle as pickle
from collections import OrderedDict
from bs4 import BeautifulSoup
import requests
from multiprocessing import Pool

url = r'http://www.mixesdb.com'
nthreads = 16
checkpoint = 500

def artists_from_soup(soup):
    page_artists_list = soup.find('ul', id='catSubcatsList')
    artists = {artist.a.text: artist.a['href']
        for artist in page_artists_list.find_all('li')}
    return artists

def mixes_for_artist(artist_link):
    #print "Getting mixes for %s" % artist_link
    page = requests.get(url+artist_link, timeout=30)
    #print "Parsing soup for %s" % artist_link
    soup = BeautifulSoup(page.text)
    mix_list = soup.find('ul', id='catMixesList')
    mix_links = {mix.a.text: mix.a['href'] 
        for mix in mix_list.find_all('li')}
    return mix_links
    
def mix_from_link(link):
    #print "Getting tracklist for %s" % link
    page = requests.get(url+link, timeout=5)
    #print "Parsing soup for %s" % link
    soup = BeautifulSoup(page.text)
    categories = soup.find(id='mw-normal-catlinks')
    categories = {li.a.text: li.a['href']
        for li in categories.ul.find_all('li')}
    tracklist = soup.find(class_='list')
    if tracklist: 
        tracklist = tracklist.p
        if tracklist:
            tracklist = tracklist.text
    else:
        tracklist = [li.text for ol in soup.find_all('ol')
                             for li in ol.find_all('li')]
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
        pickle.dump(all_artists, fd, 2)
    
    return all_artists

def get_artist_mixes(all_artists):
    try: artist_mixes = pickle.load(open('mix_links.pkl'))
    except: artist_mixes = {}
    
    to_process = OrderedDict(all_artists)
    for artist in artist_mixes.keys():
        to_process.pop(artist, None)
    if len(to_process) == 0: return artist_mixes
    print "Getting mixes for %d artists" % len(to_process)
    
    pool = Pool(nthreads)
    new_artist_mixes = OrderedDict()
    for artist_name, artist_link in to_process.items():
        new_artist_mixes[artist_name] = pool.apply_async(mixes_for_artist, (artist_link,))
    print "Waiting for all scrape tasks to complete"
    nartists = 0
    nmixes = 0
    for artist_name, async_result in new_artist_mixes.items():
        try:
            nartists += 1
            mixes = async_result.get()
            artist_mixes[artist_name] = mixes
            nmixes += len(mixes)
            print '%d - %s (%d mixes)' % (nartists, artist_name, len(mixes))
        except Exception, e:
            artist_mixes.pop(artist_name, None)
            print >>sys.stderr, e
            
        if nartists % checkpoint == 0:
            print "Checkpointing with %d artists" % nartists
            with open('mix_links.pkl', 'w') as fd:
                pickle.dump(artist_mixes, fd)
    print "Found %d mixes" % nmixes
    
    print "Saving mix links"
    with open('mix_links.pkl', 'w') as fd:
        pickle.dump(artist_mixes, fd, 2)
        
    pool.close()
    return artist_mixes
    
def get_tracklists(artist_mixes):
    try: all_mixes = pickle.load(open('mixes.pkl'))
    except: all_mixes = {}
    
    to_process = OrderedDict()
    for mixes in artist_mixes.values():
        to_process.update(mixes)
    for mix_name in all_mixes.keys():
        to_process.pop(mix_name, None)
    if len(to_process) == 0: return all_mixes
    print "Getting tracklists for %d mixes" % len(to_process)
    
    pool = Pool(nthreads)
    new_mixes = OrderedDict()
    for mix_name, mix_link in to_process.items():
        new_mixes[mix_name] = pool.apply_async(mix_from_link, (mix_link,))
    print "Waiting for all scrape tasks to complete"
    ncompleted = 0
    for mix_name, async_result in new_mixes.items():
        try:
            ncompleted += 1
            result = async_result.get()
            all_mixes[mix_name] = result
        except Exception, e:
            all_mixes.pop(mix_name, None)
            print >>sys.stderr, e
            
        if ncompleted % checkpoint == 0:
            print "Checkpointing with %d mixes" % ncompleted
            with open('mixes.pkl', 'w') as fd:
                pickle.dump(all_mixes, fd)
    print "Scraped %d mixes" % ncompleted
        
    with open('mixes.pkl', 'w') as fd:
        pickle.dump(all_mixes, fd, 2)
        
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