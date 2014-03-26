import json
from copy import deepcopy

def spagedi_tree():

    analysis_level = {
        "1": "individual",
        "2": "population",
        "3": "population",
        "4": "population",
    }

    # Import levels of the Spagedi decision tree from JSON files
    with open('level_of_analyses.json') as datafile:
        LEVEL_OF_ANALYSES = json.load(datafile)
    with open('statistics.json') as datafile:
        STATISTICS = json.load(datafile)
    with open('computational_options.json') as datafile:
        COMPUTATIONAL_OPTIONS = json.load(datafile)
    with open('output_options.json') as datafile:
        OUTPUT_OPTIONS = json.load(datafile)

    # Connect them up
    for key in COMPUTATIONAL_OPTIONS:
        COMPUTATIONAL_OPTIONS[key]["next"] = OUTPUT_OPTIONS
    for key in STATISTICS["individual"]:
        STATISTICS["individual"][key]["next"] = COMPUTATIONAL_OPTIONS["individual"]
    for key in STATISTICS["population"]:
        STATISTICS["population"][key]["next"] = COMPUTATIONAL_OPTIONS["population"]
    for key in LEVEL_OF_ANALYSES:
        LEVEL_OF_ANALYSES[key]["next"] = STATISTICS[analysis_level[key]]

    return LEVEL_OF_ANALYSES

if __name__ == '__main__':
    TREE = spagedi_tree()
    print json.dumps(TREE, indent=2)