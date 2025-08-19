import csv
import datetime
import logging
logger = logging.getLogger()
logging.basicConfig(level=logging.DEBUG,format='%(message)s')
from collections import Counter
try: 
    import tomllib # Python v3.11+
except: 
    try:
        import tomli as tomllib
    except:
        logger.critical("Old version of python. Two options to fix: 1. install python 3.11+, OR 2. install tomli via pip/conda.")
        exit()
try:
    import networkx as nx
except:
    logger.critical("networkx missing. Please install it :)")
    exit()


#load the setup file
with open("setup.toml", "rb") as f:
    setup = tomllib.load(f)


#load the preferences file and extract preferences
excursions = {}
workshops = {}
with open(setup['general']['preferences'], 'r') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        name = f'{row[3]} {row[4][:2]}.'
        count = 2
        while True:
            if name in excursions:
                logging.warning(f'multiple persons with the name {name} detected. Adding one more letter to the surname abbreviation.')
                count += 1
                name = f'{row[3]} {row[4][:count]}.'
            else:
                break
        excursions[name] = [row[e] for e in setup['excursions']['columns']]
        workshops[name] = [row[w] for w in setup['workshops']['columns']]

#load capacity files
excursion_capacities = {}
with open(setup['excursions']['capacities'], 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        excursion_capacities[row[0]] = int(row[1])
workshop_capacities = {}
with open(setup['workshops']['capacities'], 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        workshop_capacities[row[0]] = int(row[1])

#get the costs
workshop_costs = [setup['workshops']['cost'][n] for n in ['first','second','third']]
excursion_costs = [setup['excursions']['cost'][n] for n in ['first','second','third']]

#create the graph
def create_graph(prefs,capacity,costs):
    G=nx.DiGraph()
    num_persons=len(prefs)
    G.add_node('dest',demand=num_persons)
    for person,projectlist in prefs.items():
        G.add_node(person,demand=-1)
        for i,project in enumerate(projectlist):
            cost = costs[i]
            G.add_edge(person,project,capacity=1,weight=cost) # Edge taken if person does this project

    for project,c in capacity.items():
            G.add_edge(project,'dest',capacity=c,weight=0)
    return G
    
#propose adjusting limits if it is not possible to allocate persons to either of their choices
def adjust_limits(G, prefs,capacity,costs, event):
    logger.critical(f'ERROR while trying to allocate {event}s:')
    logger.critical(f'No combination could be found that sorts all persons in either of their three {event} choices. An adjustment of the capacities is needed.')
    logger.critical('Consider one or a combination of the following:')
    logger.critical('\n')
    for p in capacity.keys():
        for i in range(1,100):
            capacity[p] += i
            G = create_graph(prefs,capacity,costs)
            capacity[p] -= i
            try:
                flowdict = nx.min_cost_flow(G)
            except:
                pass
            else:
                logger.critical(f'adding +{i} to {p} would work')
                break

    
#create the min-cost-flow from the Graph
def create_flow(prefs,capacity,costs,event):
    G = create_graph(prefs,capacity,costs)
    try:
        return nx.min_cost_flow(G)
    except:
        adjust_limits(G, prefs,capacity,costs,event)
        raise 
    
#apply flow
quitnow = False
try:
    event = 'excursion'
    flowdict_ex = create_flow(excursions,excursion_capacities,excursion_costs, event=event)
except:
    quitnow = True

try:
    event = 'workshop'
    flowdict_ws = create_flow(workshops,workshop_capacities,workshop_costs, event=event)
except:
    quitnow = True

if quitnow:
    logger.critical('\n')
    logger.critical('Program stops now. No output created.')
    exit()

#extract the chosen project
rows = []
choices_ex = []
choices_ws = []
list_ex = []
list_ws = []
for person in excursions.keys():
        for choice,(project,flow) in enumerate(flowdict_ex[person].items(), start=1):
            if flow:
                choices_ex.append(choice)
                pexcursion = project
                list_ex.append(project)
        for choice,(project,flow) in enumerate(flowdict_ws[person].items(), start=1):
            if flow:
                choices_ws.append(choice)
                pworkshop = project
                list_ws.append(project)
        rows.append({'name':person, 'excursion':pexcursion, 'workshop':pworkshop})

#write the results to a CSV file
fieldnames = ['name','excursion','workshop']
with open(setup['general']['results'], 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

logger.info(f"Results successfully written to {setup['general']['results']}")
logger.info(f"Please review the stats at {setup['general']['stats']}")

#provide infos
with open(setup['general']['stats'], 'w') as f:
    print('created:',datetime.datetime.now(), file=f)
    print('',file=f)
    print('## The folling cost value were used ##',file=f)
    print('workshops: '+', '.join([f"{k} {v}" for k, v in setup['workshops']['cost'].items()]),file=f)
    print('excursions: '+', '.join([f"{k} {v}" for k, v in setup['excursions']['cost'].items()]),file=f)

    print('',file=f)
    print('## Allocated number of participents for excursions (allocated/capacity) ##',file=f)
    for ex,n in Counter(list_ex).items():
        print(f'{ex}: {n}/{excursion_capacities[ex]}',file=f)

    print('',file=f)
    print('## Allocated number of participents for workshops (allocated/capacity) ##',file=f)
    for ws,n in Counter(list_ws).items():
        print(f'{ws}: {n}/{workshop_capacities[ws]}',file=f)


    print('',file=f)
    print('## Occurences of choices ##',file=f)
    print(f'excursion: {Counter(choices_ex)[1]}x first {Counter(choices_ex)[2]}x second {Counter(choices_ex)[3]}x third',file=f)
    print(f'workshop: {Counter(choices_ws)[1]}x first {Counter(choices_ws)[2]}x second {Counter(choices_ws)[3]}x third',file=f)

