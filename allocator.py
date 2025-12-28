#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "networkx>=3.6.1",
# ]
# [tool.uv]
# exclude-newer = "2025-12-28T00:00:00Z"
# ///
'''
Author: Dominik Austen
Date: 28.12.2025
Description:
    Allocates participants of the StuMeTa to workshops and 
    excursions based on their preferences
'''
import csv
import datetime
import logging
from pathlib import Path
logger = logging.getLogger()
logging.basicConfig(level=logging.INFO,format='[%(levelname)s] %(message)s')
from collections import Counter
import tomllib
import networkx as nx
import sys

#load the setup file
try:
    with open("setup.toml", "rb") as f:
        setup = tomllib.load(f)
except:
    logger.critical(f"Could not find setup file. Please make sure there is a {Path('setup.toml')} file in the same directory as the script you just run")
    sys.exit(1)


#load the preferences file and extract preferences
excursions = {}
workshops = {}
surnames = {}
with open(Path(setup['general']['preferences']), 'r') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        first_name = row[setup['general']['column']['firstname']]
        surname = row[setup['general']['column']['surname']]
        city = row[setup['general']['column']['city']]
        name = f"{first_name} {surname[:1].capitalize()}. ({city})"
        count = 1
        while True:
            if name in excursions:
                if name == f"{first_name} {surname.capitalize()}. ({city})":
                    logger.critical(f"{name} is twice in the preferences file")
                    break
                logging.debug(f'multiple persons with the name {name} detected. Adding one more letter to the surname abbreviation.')
                count += 1
                excursions[f"{first_name} {surnames[name][:count].capitalize()}. ({city})"] = excursions[name]
                workshops[f"{first_name} {surnames[name][:count].capitalize()}. ({city})"] = workshops[name]
                surnames[f"{first_name} {surnames[name][:count].capitalize()}. ({city})"] = surnames[name]
                del workshops[name]
                del excursions[name]
                del surnames[name]

                name = f"{first_name} {surname[:count].capitalize()}. ({city})"
            else:
                break
        surnames[name] = surname
        excursions[name] = [row[e] for e in setup['excursions']['columns']]
        workshops[name] = [row[w] for w in setup['workshops']['columns']]
#load capacity files
excursion_capacities = {}
with open(Path(setup['excursions']['capacities']), 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
            excursion_capacities[row[0]] = int(row[1])
workshop_capacities = {}
with open(Path(setup['workshops']['capacities']), 'r') as f:
    reader = csv.reader(f)
    for row in reader:
        if row:
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
    logger.error(f'No combination could be found that sorts all persons in either of their three {event} choices. An adjustment of the capacities is needed.\n')
    logger.info('Consider one or a combination of the following:\n')
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
                logger.info(f'adding +{i} to {p} would work')
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
    print('')
    logger.info('No output created.')
    sys.exit(1)

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

#warning and tips if number of alloc is smaller than 'lowalloc_threshold'-option in setup.toml file
wsm_list = []
for ws,n in Counter(list_ws).items():
    if (n < setup['general']['lowalloc_threshold']) and (setup['general']['lowalloc_threshold'] <= workshop_capacities[ws]):
        wsm_list.append((n,ws))
for num,wsm in wsm_list:
    nlist = []
    for n,i in workshops.items():
        if wsm in i:
            nlist.append(n)
    if not len(nlist) > num:
        logger.warning(f"{wsm} has <{setup['general']['lowalloc_threshold']} participants in the current allocation. However, there is no way to increase that because everyone who has {wsm} in their choices already got allocated to {wsm}")
        sys.exit(0)
    logger.warning(f"{wsm} has <{setup['general']['lowalloc_threshold']} participants in the current allocation. Some people who have {wsm} as one of their choices did not get allocated to {wsm}. Instead, they got allocted to the following workshops. You can increase the number of participants in {wsm} by reducing the maximum capacity in {setup['workshops']['capacities']}. ")

    wlist = []
    for n in rows:
        if n['name'] in nlist:
            wlist.append(n['workshop'])
    for i in range(wlist.count(wsm)):
        wlist.remove(wsm)

    c = dict(sorted(Counter(wlist).items(), key=lambda item: item[1], reverse=True))
    for i,j in c.items():
        print(f"{j}x {i}")

exm_list = []
for ex,n in Counter(list_ex).items():
    if (n < setup['general']['lowalloc_threshold']) and (setup['general']['lowalloc_threshold'] <= excursion_capacities[ex]):
        exm_list.append((n,ex))
for num,exm in exm_list:
    print('')
    nlist = []
    for n,i in excursions.items():
        if exm in i:
            nlist.append(n)
    if not len(nlist) > num:
        logger.warning(f"{exm} has <{setup['general']['lowalloc_threshold']} participants in the current allocation. However, there is no way to increase that because everone who has {exm} in their choices already got allocated to {exm}")
        sys.exit(0)
    logger.warning(f"{exm} has <{setup['general']['lowalloc_threshold']} participants in the current allocation. Some people who have {exm} as one of their choices did not get allocated to {exm}. Instead, they got allocted to the following excursions. You can increase the number of participants in {exm} by reducing the maximum capacity in {setup['excursions']['capacities']}. ")

    exlist = []
    for n in rows:
        if n['name'] in nlist:
            exlist.append(n['excursion'])
    for i in range(exlist.count(exm)):
        exlist.remove(exm)

    c = dict(sorted(Counter(exlist).items(), key=lambda item: item[1], reverse=True))
    print('')
    for i,j in c.items():
        print(f"{j}x {i}")


#write the results to a CSV file
fieldnames = ['name','excursion','workshop']
results_file = Path(setup['general']['results'])
results_file.parent.mkdir(parents=True, exist_ok=True)
with open(results_file, 'w', encoding='UTF8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

logger.info(f"Results successfully written to {Path(setup['general']['results'])}")
logger.info(f"Please review the stats at {Path(setup['general']['stats'])}")

#provide infos
stats_file = Path(setup['general']['stats'])
stats_file.parent.mkdir(parents=True, exist_ok=True)
with open(stats_file, 'w') as f:
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

