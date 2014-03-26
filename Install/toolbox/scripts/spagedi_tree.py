import json

def spagedi_tree():

    level = {
        '1': 'individual',
        '2': 'population',
        '3': 'population',
        '4': 'population',
    }

    # Import levels of the Spagedi decision tree from JSON files
    layers = ('level_of_analyses', 'statistics',
              'computational_options', 'output_options')
    tree = {}
    for lyr in layers:
        with open(lyr + '.json') as datafile:
            tree[lyr] = json.load(datafile)

    # Connect them up and build the decision tree
    for key in tree['computational_options']:
        tree['computational_options'][key]['next'] = tree['output_options']
    for key in tree['statistics']['individual']:
        tree['statistics']['individual'][key]['next'] = tree['computational_options']['individual']
    for key in tree['statistics']['population']:
        tree['statistics']['population'][key]['next'] = tree['computational_options']['population']
    for key in tree['level_of_analyses']:
        tree['level_of_analyses'][key]['next'] = tree['statistics'][level[key]]

    return tree['level_of_analyses']

if __name__ == '__main__':
    print json.dumps(spagedi_tree(), indent=2, sort_keys=True)