import os, json 
from collections import OrderedDict
from bunch import bunchify, unbunchify

def spagedi_tree():
    level = {'1': 'individual', '2': 'population', '3': 'population', '4': 'population'}

    # Import levels of the Spagedi decision tree from JSON files
    layers = (
        'level_of_analyses',
        'statistics',
        'statistics_sublayer', # new (simple)
        'computational_options',
        'computational_sublayer', # new (subtree)
        'output_options',
    )
    tree = OrderedDict()
    for lyr in layers:
        json_path = 'json' + os.sep + lyr + '.json'
        with open(json_path) as datafile:
            tree[lyr] = json.load(datafile, object_pairs_hook=OrderedDict)

    # Connect them up and build the decision tree
    tree = bunchify(tree)
    for group, subtree in tree.computational_options.items():
        for key in subtree:
            if key != 'headline':
                subtree[key].next = tree.output_options
    for key in tree.statistics.individual:
        if key != 'headline':
            tree.statistics.individual[key].next = tree.computational_options.individual
    for key in tree.statistics.population:
        if key != 'headline':
            tree.statistics.population[key].next = tree.computational_options.population
    for key in tree.level_of_analyses:
        if key != 'headline':   
            tree.level_of_analyses[key].next = tree.statistics[level[key]]

    return tree['level_of_analyses']

if __name__ == '__main__':
    tree = unbunchify(spagedi_tree())
    print json.dumps(tree, indent=3, sort_keys=True)