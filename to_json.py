#!/usr/bin/env python

'''
Convert list of edges to JSON format
'''

import sys, csv, json
from collections import defaultdict

def load_edges():
    '''return a dict of (dj1,dj2) -> n connections'''
    edges = defaultdict(int)
    with open('edges.csv') as fd:
        reader = csv.reader(fd)
        for row in reader:
            dj1 = row[0]
            dj2 = row[1]
            if dj1 is None or dj2 is None or dj1 == '?' or dj2 == '?': 
                continue
            edges[(dj1,dj2)] += 1
            dj3 = row[2]
            if dj3:
                edges[(dj1,dj3)] += 1
                edges[(dj3,dj2)] += 1
    return dict(edges)
    
def nplays(edges):
    count = defaultdict(int)
    for dj1, dj2 in edges.keys():
        #count[dj1] += 1
        count[dj2] += 1
    return dict(count)
    
def filter_edges(edges, min_nplays=1):
    '''Remove djs with total nplays < minimum'''
    count = nplays(edges)
    filtered = {(dj1, dj2): v for (dj1, dj2), v in edges.iteritems()
                if count.get(dj1, 0) > min_nplays and count.get(dj2, 0) > min_nplays}
    return filtered, count
    
def nodes_for_edges(edges):
    return nplays(edges).keys()

def to_json(edges, count):
    djs = nodes_for_edges(edges)
    nodes = [dict(name=name, group=1, value=count[name]) 
             for name in djs]
    djs_to_index = {name: i for i, name in enumerate(djs)}
    links = [dict(source=djs_to_index[dj1], target=djs_to_index[dj2], value=n)
         for (dj1, dj2), n in edges.iteritems()]
    data = dict(nodes=nodes, links=links)
    return data
    
def print_graph(edges, ostream=sys.stderr):
    nnodes = len(nodes_for_edges(edges))
    nedges = len(edges)
    nplays = sum(v for v in edges.itervalues())
    print >>ostream, "%d nodes with %d edges (%d plays)" \
        % (nnodes, nedges, nplays)

if __name__ == '__main__':
    print >>sys.stderr, "Loading edges"
    edges = load_edges()
    print_graph(edges)
        
    cutoff = 100
    print >>sys.stderr, "Removing nodes with < %d plays" % cutoff
    edges, count = filter_edges(edges, cutoff)
    print_graph(edges)
        
    print >>sys.stderr, "Converting to dict"
    data = to_json(edges, count)
    print >>sys.stderr, "Serializing to JSON"
    json.dump(data, sys.stdout, indent=2, separators=(',', ': '))