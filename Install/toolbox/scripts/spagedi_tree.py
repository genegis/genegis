import os, json 
from collections import OrderedDict
from bunch import Bunch, bunchify

def fasten(tree, next, skip=None, ignore_keys=('headline', 'default')):
    if type(tree) == Bunch:
        # If there is already a link to the next level, descend
        if 'next' in tree:
            tree = fasten(tree.next, next, skip)
        else:
            # If free-form user input is expected, 'next' is on the same level
            if 'user_input' in tree:
                tree.next = next
            # If a menu selection is expected, 'next' is one level down
            else:
                for node in tree:
                    if type(tree[node]) == Bunch and node not in ignore_keys:
                        if 'next' in tree[node]:
                            tree = fasten(tree[node], next, skip)
                        else:
                            tree[node].next = next
    return tree

def buildtree(tree, ordering):
    '''Build the decision tree by connecting the layers'''
    below = ordering[0]
    for lyr in ordering[1:-1]:
        subtree = tree.pop(below, None)
        if 'individual' in subtree:
            tree[lyr].individual = fasten(tree[lyr].individual, subtree.pop('individual'))
            # tree[lyr].population = fasten(tree[lyr].population, subtree.pop('population'))
        else:
            tree[lyr] = fasten(tree[lyr], subtree)
        below = lyr
    subtree = tree.pop(lyr, None)
    tree = tree.level_of_analyses
    grouping = {'1': 'individual', '2': 'population', '3': 'population', '4': 'population'}
    for node in tree:
        if node != 'headline':
            tree[node].next = subtree[grouping[node]]
    return tree

def spagedi_tree():
    # Import layers of the Spagedi decision tree from JSON files
    layers = ['level_of_analyses', 'statistics', 'statistics_sublayer',
              'computational_options', 'computational_sublayer',
              'output_options']
    tree = OrderedDict()
    for lyr in layers:
        json_path = 'json' + os.sep + lyr + '.json'
        with open(json_path) as datafile:
            tree[lyr] = json.load(datafile, object_pairs_hook=OrderedDict)
    tree = bunchify(tree)
    return buildtree(tree, layers[::-1])

def prp(o):
    print json.dumps(o, indent=3, sort_keys=True)

if __name__ == '__main__':
    prp(spagedi_tree())
