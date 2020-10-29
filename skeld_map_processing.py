import pickle
import json

with open('normal_skeld.txt', 'r') as file:
    lines = file.readlines()
    normal_tiles = []
    for line in lines:
        normal_tiles.append([int(thing) for thing in line.strip().split()])

with open('skeld_map.pkl', 'wb') as pkl_file:
    pickle.dump(normal_tiles, pkl_file)

skeld_vents = {4: [17, 19], 9: [4, 17], 13: [15, 22],
               15: [13, 22], 17: [4, 9], 19: [23],
               22: [15, 13], 23: [19], 24: [25], 25: [24]}

with open('skeld_vents.pkl', 'wb') as pkl_file:
    pickle.dump(skeld_vents, pkl_file)

skeld_locations = ['Corridor'] * 28

with open('tiles_dict.txt', 'r') as file:
    lines = file.readlines()
    for line in lines:
        indices, name = tuple(line.split('-'))
        indices = eval(indices)
        name = name.strip()
        for index in indices:
            skeld_locations[index] = name

with open('skeld_locations.pkl', 'wb') as pkl_file:
    pickle.dump(skeld_locations, pkl_file)



