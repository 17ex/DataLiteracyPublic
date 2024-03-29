import os
import sys
import pandas as pd
REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                          os.pardir,
                                          os.pardir))
sys.path.insert(1, os.path.join(REPO_ROOT, 'src'))
import analysis
import data_io

station_subset = data_io.load_station_subset()
incoming, outgoing = data_io.load_incoming_outgoing_conns()
excluded_pairs = data_io.load_excluded_pairs()
gain_vals = data_io.load_gain_values('average')

directions = data_io.load_directions()
unique_stations_in, unique_stations_out, _ = data_io.load_unique_station_names()

for origin in unique_stations_in:
    if origin not in station_subset:
        continue
    # do some pre-calculations for the incoming list
    incoming_from_origin = incoming[incoming['origin'].apply(lambda x: any(origin == value for value in x))]
    incoming_from_origin['origin_idx'] = incoming_from_origin['origin'].apply(lambda x: x.index(origin))
    incoming_from_origin['departure_origin'] = incoming_from_origin.apply(lambda row: row['departure'][row['origin_idx']], axis=1)
    incoming_from_origin['arrival_fra'] = incoming_from_origin['arrival'] + pd.to_timedelta(incoming_from_origin['delay'], unit='m')
    delay_all = {}
    reachable_all = {}
    print(origin)
    for destination in unique_stations_out:
        if (
                destination not in station_subset
                or origin == destination
                or (origin, destination) in excluded_pairs
           ):
            continue
        org_direction = None
        dest_direction = None
        for key, value_list in directions.items():
            if origin in value_list:
                org_direction = key
                break
        if org_direction:
            for key, value_list in directions.items():
                if destination in value_list:
                    dest_direction = key
                    break
            if dest_direction and org_direction == dest_direction:
                # Maybe skip also if directions could not be determined,
                # and log it. Should not get called for that case though.
                continue
        print(destination)
        delay = analysis.reachable_transfers(incoming_from_origin, outgoing, origin, destination, gains=gain_vals)
        delay_all[destination] = delay
    data_io.write_json(delay_all,
                       f'delay_005_{data_io.filename_escape(origin)}.json',
                       'results', 'exp_005', 'delay')
