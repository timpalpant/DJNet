#!/usr/bin/env python

'''
Print edges in the DJ network
(DJ, artist, remixer, date)
'''

import sys, re, csv
from datetime import datetime
import cPickle as pickle

prefix_pattern = re.compile(r'\[.*\] ')
remix_pattern = re.compile(r'\(.*\)')
mix_pattern = re.compile(r'ix')

def get_mix_date(mix_name):
    date_string = mix_name.split(' - ', 1)[0]
    return date_string

def get_track_artists(line):
    artist, title = line.strip().split(' - ', 1)
    try: _, artist = prefix_pattern.split(artist, 1)
    except: pass
    artist = artist.replace('+ ', '')
    remixer = remix_pattern.search(title)
    if remixer:
        remixer = remixer.string[remixer.start(0)+1:remixer.end(0)-1]
        remixer = remixer.replace(' Remix', '').replace(' Mix', '')
        remixer = remixer.strip()
    return artist, remixer

if __name__ == '__main__':
    print >>sys.stderr, "Loading artists and mixes"
    djs = pickle.load(open('mix_links.pkl'))
    mixes = pickle.load(open('mixes.pkl'))
    print >>sys.stderr, "Loaded %d DJs and %d mixes" \
        % (len(djs), len(mixes))
    
    print '# DJ, Track Artist, Track Remixer, Mix Date'
    writer = csv.writer(sys.stdout)
    for dj, dj_mixes in djs.items():
        for mix in dj_mixes.keys():
            try: mix_date = get_mix_date(mix)
            except: mix_date = 'unknown'
            
            try: 
                categories, tracklist = mixes[mix]
                if not isinstance(tracklist, list):
                    tracklist = tracklist.split('\n')
            except Exception, e: 
                #print >>sys.stderr, e
                continue    
                
            if tracklist is None: continue
            for track in tracklist:
                try:
                    track_artist, track_remixer = get_track_artists(track)
                    writer.writerow((dj, track_artist, track_remixer, mix_date))
                except Exception, e: 
                    #print >>sys.stderr, track
                    #print >>sys.stderr, e
                    continue