import os, json 
from collections import OrderedDict
from bunch import Bunch, bunchify
import ipdb

class TreeMaker(object):

    def fasten(self, tree, next):
        if type(tree) == Bunch:
            for node in tree:
                if node not in ('headline', 'default'):
                    tree[node].next = next
        return tree

    def descend(self, current, bottom):
        if 'next' in current:
            self.descend(current.next, bottom)
        if 'user_input' in current:
            current.next = bottom
        else:
            for key in current.keys():
                if key not in ('headline', 'default'):
                    if 'next' in current[key]:
                        self.descend(current[key].next, bottom)
                    else:
                        ipdb.set_trace()
                        current[key].next = bottom
        return current

    def buildtree(self, tree, ordering):
        '''Build the decision tree by connecting the layers'''
        below = ordering[0]
        for lyr in ordering[1:-1]:
            subtree = tree.pop(below, None)
            if 'individual' in subtree:
                tree[lyr].individual = self.fasten(tree[lyr].individual,
                                                   subtree.pop('individual'))
                tree[lyr].population = self.fasten(tree[lyr].population,
                                                   subtree.pop('population'))
            else:
                tree[lyr].individual = self.fasten(tree[lyr].individual, subtree)
                tree[lyr].population = self.fasten(tree[lyr].population, subtree)
            below = lyr
        subtree = tree.pop(below, None)
        tree = tree.level_of_analyses
        grouping = {'1': 'individual', '2': 'population', '3': 'population', '4': 'population'}
        for node in tree:
            if node != 'headline':
                tree[node].next = subtree[grouping[node]]

        # Set up computational sublayer
        computational_sublayer_path = 'json' + os.sep + 'computational_sublayer' + '.json'
        with open(computational_sublayer_path) as datafile:
            computational_sublayer = bunchify(json.load(datafile, object_pairs_hook=OrderedDict))

        # Individual
        for k in tree['1'].next.keys():
            if k not in ('headline', 'next'):
                for j in computational_sublayer['individual'].keys():
                    if j == '5':
                        ipdb.set_trace()
                    temp = tree['1'].next[k].next[j].next
                    tree['1'].next[k].next[j].next = computational_sublayer['individual'][j]
                    tree['1'].next[k].next[j] = self.descend(
                        tree['1'].next[k].next[j].next, temp
                    )
        
        # Population
        for i in ('2', '3', '4'):
            for k in tree[i].next.keys():
                if k not in ('headline', 'next'):
                    for j in computational_sublayer['population'].keys():
                        temp = tree[i].next[k].next[j].next
                        tree[i].next[k].next[j].next = computational_sublayer['population'][j]
                        tree[i].next[k].next[j] = self.descend(
                            tree[i].next[k].next[j].next, temp
                        )
        
        # Set up statistics sublayer
        statistics_sublayer_path = 'json' + os.sep + 'statistics_sublayer' + '.json'
        with open(statistics_sublayer_path) as datafile:
            statistics_sublayer = bunchify(json.load(datafile, object_pairs_hook=OrderedDict))
        
        # Individual
        temp = tree['1'].next['N'].next
        tree['1'].next['N'].next = statistics_sublayer['individual']['N']
        tree['1'].next['N'].next.next = temp
        
        # Population
        for i in ('2', '3', '4'):
            for j in statistics_sublayer['population'].keys():
                temp = tree['2'].next[j].next
                tree['2'].next[j].next = statistics_sublayer['population'][j]
                tree['2'].next[j].next.next = temp
        return tree


def spagedi_tree():
    # Import layers of the Spagedi decision tree from JSON files
    layers = ['level_of_analyses', 'statistics', 'computational_options', 'output_options']
    tree = OrderedDict()
    for lyr in layers:
        json_path = 'json' + os.sep + lyr + '.json'
        with open(json_path) as datafile:
            tree[lyr] = json.load(datafile, object_pairs_hook=OrderedDict)
    tree = bunchify(tree)
    tm = TreeMaker()
    tree = tm.buildtree(tree, layers[::-1])
    return tree

def prp(o):
    print json.dumps(o, indent=3, sort_keys=True)

if __name__ == '__main__':
    prp(spagedi_tree())
