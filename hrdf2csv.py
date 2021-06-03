import re
import sys


class Station:
    def __init__(self, station_id, station_name):
        self.station_id = station_id
        self.station_name = station_name
        self.metabhfs = []  # list of (related station_id, transfer_time in minutes)
        self.mobihub_stop_count = 0
        self.journeys = []
        self.coordinates = (None, None, None)
        self.platforms = set()
        self.mobihub_id = None


    def set_platforms(self, gleise):
        self.platforms = gleise

    def get_platforms_count(self):
        return len(self.platforms)

    def add_coordinates(self, coordinates):
        self.coordinates = coordinates

    def get_lat(self):
        return self.coordinates[0]

    def get_long(self):
        return self.coordinates[1]

    def add_metabhf(self, metabhf):
        self.metabhfs = metabhf

    def get_metabhf(self, consider_none=True, max_transfer_time=sys.maxsize): #sys.maxsize
        return list(filter(lambda x: consider_none if x[1] is None else int(x[1]) <= max_transfer_time, self.metabhfs))

    def get_metabhf_count(self):
        return len(self.get_metabhf())

    def add_journey(self, journey):
        self.journeys.append(journey)

    def get_id(self):
        return self.station_id

    def get_vehicle_types_numbers(self):
        result = {}
        for j in self.journeys:
            vt = j.vehicle_type
            if vt in result.keys():
                result[vt] += 1
            else:
                result[vt] = 1
        return result

    def set_vehicle_categories_numbers(self, vehicle_categories):
        self.vehicle_categories = vehicle_categories

    def get_stop_count(self):
        return len(self.journeys)

    def get_mobihub_stop_count(self):
       return self.mobihub_stop_count

    def get_start_count(self):
        return len(list(filter(lambda x: x.has_start_stop(self.station_id), self.journeys)))

    def get_end_count(self):
        return len(list(filter(lambda x: x.has_end_stop(self.station_id), self.journeys)))



class Stop:
    def __init__(self, line):
        self.station_id = line[:7]
        # self.station_id, self.arrival, self.departure = line[:7], line[30:35], line[37:42]

    def get_id(self):
        return self.station_id


class Journey:

    def __init__(self, line):
        self.journey_id, self.admin_id = line[3:9], line[10:16]
        self.line_id = None
        self.stops = []

    def set_vehicle(self, line):
        self.vehicle_type, self.start_stop, self.end_stop = line[3:6].strip(), line[7:14], line[15:22]

    def set_direction(self, line):
        self.direction = line[3:4]

    def set_line(self, line):
        self.line_id = line[3:11].strip()

    def add_stop(self, station_id):
        self.stops.append(station_id)

    def has_stop(self, stop_id):
        return stop_id in self.stops

    def has_intermediate_stop(self, stop_id):
        return stop_id in self.stops[1:-1]

    def has_start_stop(self, stop_id):
        return stop_id == self.stops[0]

    def get_start_stop(self):
        return self.stops[0]

    def has_end_stop(self, stop_id):
        return stop_id == self.stops[-1]

    def get_end_stop(self):
        return self.stops[-1]


hrdf_directory = 'data'


def get_bahnhof():
    result = {}
    with open('{}/BAHNHOF'.format(hrdf_directory), 'r', encoding='UTF-8') as f:
        lines = f.readlines()
        for s in lines:
            nummer = s[:7]
            name = s[12:][:s[12:].find('$')]
            result[nummer] = name
    return result


bahnhof = get_bahnhof()


def get_metabhf():
    s = re.compile(r'^\*A\s')
    r = re.compile(r'^\d{7}\s')
    r2 = re.compile(r'^\d{7}\:\s\s(\d{7}.+)')

    with open('{}/METABHF'.format(hrdf_directory), 'r', encoding='UTF-8') as f:
        lines = f.readlines()

    result = {}
    sign = None
    for line in lines:
        if s.match(line):
            sign = line[3:4]
            continue

        if r.match(line):
            sttn = line[:7]
            rel = line[8:15]
            zt = line[16:19]
            if sttn in result.keys():
                result[sttn].append((rel, zt))
            else:
                result[sttn] = [(rel, zt)]
            continue

        if r2.match(line):
            sttn = line[:7]
            rel = line[10:].split()
            if sttn in rel:
                rel.remove(sttn)
            if sttn in result.keys():
                for i in rel:
                    if i not in list(zip(*result[sttn]))[0]:
                        result[sttn].append((i, 0))
            else:
                result[sttn] = list(zip(rel, [0] * len(rel)))

    return result


metabhf = get_metabhf()

all_metabhf_ids = set()
all_bahnhof_ids = set()

for mbhf in metabhf.keys():
    all_metabhf_ids.add(mbhf)

for bhf in bahnhof.keys():
    all_bahnhof_ids.add(bhf)

exclude_set = all_metabhf_ids - all_bahnhof_ids


def get_bfkoord():
    result = {}
    with open('{}/BFKOORD_WGS'.format(hrdf_directory), 'r', encoding='UTF-8') as f:
        lines = f.readlines()

    for line in lines:
        result[line[0:7]] = (line[19:29].strip(), line[8:18].strip(), line[30:36].strip())

    return result


bfkoord = get_bfkoord()


def get_platforms():
    rows = None
    with open('{}/GLEIS'.format(hrdf_directory), 'r', encoding='UTF-8') as f:
        rows = f.readlines()

    result = {}

    g = re.compile(r'^\d{7}\s\d{6}\s.{6}\s.+')

    for row in rows:
        if g.match(row):
            station_id = row[0:7]
            journey_id = row[8:14]
            admin_id = row[15:21]
            gleis_id = row[23:30].strip()

            if station_id not in result.keys():
                result[station_id] = set()

            result[station_id].add(gleis_id)

    return result


platforms = get_platforms()


def get_zugart():
    rows = None
    with open('{}/ZUGART'.format(hrdf_directory), 'r', encoding='UTF-8') as f:
        rows = f.readlines()

    categories = {}
    a = re.compile(r'^\w{1,3}\s+\d{1,2}\s.+$')
    for row in rows:
        if a.match(row):
            splt = row.split()
            vehicle_type = splt[0]
            category_nr = splt[-1][1:]
            categories[category_nr] = vehicle_type
            continue

    names = {}
    b = re.compile(r'^category\d{3}\s.+$')
    e = re.compile(r'<Englisch>')
    for row in rows:
        if b.match(row):
            splt = row.split()
            category_alias = splt[0][-3:]
            category_name = splt[1]
            names[category_alias] = category_name
            continue

        if e.match(row):
            break

    result = {}
    for k, v in categories.items():
        result[v] = names[k]

    return result


zugart = get_zugart()

vm_categories = {
    'Zug': ['AG', 'EC', 'EXT', 'IC', 'ICE', 'IR', 'IRE', 'MAT', 'NJ', 'NZ', 'PB', 'PE', 'R', 'RB', 'RE', 'RJX', 'S',
            'SN', 'TER', 'TGV', 'UUU'],
    'Bergbahn': ['CC', 'FUN', 'GB', 'SL'],
    'Bus': ['B', 'BN', 'BP', 'CAR', 'EV', 'EXB', 'RUB'],
    'Tram': ['T'],
    'Taxi': ['TX'],
    'Schiff': ['BAT', 'FAE'],
    'Metro': ['M'],
    'Aufzug': ['ASC']
}
[item for sublist in vm_categories.values() for item in sublist]
pass


def get_vm_category(vehicle_type):
    for k, v in vm_categories.items():
        if vehicle_type in v:
            return k


get_vm_category('BAT')


def get_journeys():
    z = re.compile(r'^\*[Z,T]\s(\d{6})\s(.{6})\s{3}.*')
    g = re.compile(r'^\*G\s(\w{1,3})\s+(\d{7})\s(\d{7}).+$')
    s = re.compile(r'^(\d{7})\s.*(?=\d{5})?\s')
    l = re.compile(r'^\*L\s(\d+)')
    r = re.compile(r'^\*R\s([H,R])')

    result = []
    journey = None
    with open('{}/FPLAN'.format(hrdf_directory), 'r', encoding='UTF-8') as f:
        while True:
            row = f.readline()
            if not row:
                break

            if z.match(row):
                if journey:
                    result.append(journey)
                journey = Journey(row)
                continue

            if l.match(row):
                journey.set_line(row)
                continue

            if r.match(row):
                journey.set_direction(row)
                continue

            if g.match(row):
                journey.set_vehicle(row)
                continue

            if s.match(row):
                stop = Stop(row)
                journey.add_stop(stop.get_id())

        result.append(journey)
    return result


journeys = get_journeys()

vehicle_types = set()
for jrn in journeys:
    vehicle_types.add(jrn.vehicle_type)

print(vehicle_types)

sttns = {}

for station_id in bahnhof.keys():
    s = Station(station_id, bahnhof[station_id])

    if station_id in bfkoord.keys():
        s.add_coordinates(bfkoord[station_id])

    if station_id in platforms.keys():
        s.set_platforms(platforms[station_id])

    if station_id in metabhf.keys():
        s.add_metabhf(metabhf[station_id])

    sttns[station_id] = s

for journey in journeys:
    for station_id in journey.stops:
        sttns[station_id].add_journey(journey)

for sttn in sttns.values():
    vehicle_categories_numbers = {}
    for j in sttn.journeys:
        vmctgr = get_vm_category(j.vehicle_type)
        if vmctgr in vehicle_categories_numbers.keys():
            vehicle_categories_numbers[vmctgr] += 1
        else:
            vehicle_categories_numbers[vmctgr] = 1
    sttn.set_vehicle_categories_numbers(vehicle_categories_numbers)

    # mobihub_as_start_count = sttn.get_start_count()
    # mobihub_as_end_count = sttn.get_end_count()
    # for mbhf_id in sttn.get_metabhf():
    #     if mbhf_id[0] not in exclude_set:  # EXCLUSION LIST !!!!
    #         mbhf_sttn = sttns[mbhf_id[0]]
    #         mobihub_as_start_count += mbhf_sttn.get_start_count()
    #         mobihub_as_end_count += mbhf_sttn.get_end_count()
    # sttn.set_mobihub_as_start_count(mobihub_as_start_count)
    # sttn.set_mobihub_as_end_count(mobihub_as_end_count)

    mtbhfs = sttn.get_metabhf()
    if len(mtbhfs) > 0:
        for mtb in list(zip(*mtbhfs))[0]:
            try:
                if sttns[mtb].mobihub_id is None:
                    sttns[mtb].mobihub_id = sttn.station_id
            except KeyError as e:
                #print('\t', 'KEY ERROR:', mtb)
                pass

        if sttn.mobihub_id is None:
            sttn.mobihub_id = sttn.station_id


for sttn in sttns.values():
    mobihub_stop_count = sttn.get_stop_count()
    for station_id, transfer_time in sttn.get_metabhf():
        try:
            mobihub_stop_count += sttns[station_id].get_stop_count()
        except KeyError as e:
            pass
    sttn.mobihub_stop_count = mobihub_stop_count


import codecs
output_filename = 'data/csv_from_hrdf.csv'

with codecs.open(output_filename, 'w+b', encoding='UTF-8') as f:
    f.write(u'\ufeff')
    # vehicle_types_str = (';{}' * len(vehicle_types)).format(*vehicle_types)
    vehicle_categories_str = (';{}' * len(vm_categories)).format(*vm_categories)

    station_str = '{};{}'.format('station_id', 'station_name')
    platforms_count_str = ';{}'.format('platforms_count')
    metabhf_count_str = ';{}'.format('metabhf_count')
    metabhf_str = ';{}'.format('metabhf_relations')
    coords_str = ';{};{}'.format('lat', 'long')
    start_end_count_str = ';{};{}'.format('as_start_count', 'as_end_count')
    mobihub_str = ';{}'.format('mobihub_id')

    f.write(
        station_str +
        mobihub_str +
        # vehicle_types_str +
        vehicle_categories_str +
        metabhf_count_str +
        metabhf_str +
        platforms_count_str +
        start_end_count_str +
        coords_str + '\n')

with codecs.open(output_filename, 'a+b', encoding='UTF-8') as f:
    for station_id in sttns.keys():
        station_str = '{};{}'.format(station_id, sttns[station_id].station_name)

        ctgrs = [0] * len(vm_categories)
        vtnrs = sttns[station_id].vehicle_categories
        for vctgr in vtnrs:
            index = list(vm_categories.keys()).index(vctgr)
            ctgrs[index] += vtnrs[vctgr]
        vehicle_categories_str = (';{}' * len(vm_categories)).format(*ctgrs)

        metabhf_count_str = ';{}'.format(len(sttns[station_id].get_metabhf()))

        metabhf_str = ';{}'.format(' '.join(
            ['-'.join([str(mtb[0]), '-' if mtb[1] is None else '(' + str(int(mtb[1]))]) + 'min)' for mtb in
             sttns[station_id].get_metabhf()]))

        start_end_count_str = ';{};{}'.format(sttns[station_id].get_start_count(), sttns[station_id].get_end_count())

        coords_str = ';{};{}'.format(sttns[station_id].get_lat(), sttns[station_id].get_long())

        if station_id in platforms.keys():
            platforms_count_str = ';{}'.format(sttns[station_id].get_platforms_count())
        else:
            platforms_count_str = ';{}'.format(0)

        mobihub_str = ';{}'.format(sttns[station_id].mobihub_id)

        f.write(
            station_str +
            mobihub_str +
            vehicle_categories_str +
            metabhf_count_str +
            metabhf_str +
            platforms_count_str +
            start_end_count_str +
            coords_str + '\n')
