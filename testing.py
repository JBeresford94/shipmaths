from calculations import convert_degrees_to_decimals, parallel_sailing, plane_sailing,\
     great_circle_sailing, composite_great_circle_sailing
import random

minutes = [i / 10 for i in range(600)]
valid_latitudes = (range(-89,90),minutes)
valid_longitudes = (range(-179,180),minutes)

def check_positional_ranges(valid_latitudes,valid_longitudes):
    # Check degree ranges
    assert min(list(valid_longitudes[0])) == -179 and max(list(valid_longitudes[0])) == 179
    assert min(list(valid_latitudes[0])) == -89 and max(valid_latitudes[0]) == 89
    # Check minute ranges
    assert min(valid_latitudes[1]) == 0.0 and max(valid_latitudes[1]) == 59.9 
    assert min(valid_longitudes[1]) == 0.0 and max(valid_longitudes[1]) == 59.9

# test ranges, no need to test all combinations
test_latitudes = list(range(valid_latitudes[0].start, valid_latitudes[0].stop, 10))
test_longitudes = list(range(valid_longitudes[0].start, valid_longitudes[0].stop, 20))

def get_random_start_end(parallel=False):
    start_lat = random.choice(test_latitudes),random.choice(minutes), 
    start_long = random.choice(test_longitudes),random.choice(minutes)
    end_lat = random.choice(test_latitudes),random.choice(minutes)
    end_long = random.choice(test_longitudes),random.choice(minutes)
    return (start_lat,start_long,end_lat,end_long) \
    if not parallel else (start_lat,start_long,end_long)

def test_parallel():
    """parallel_sailing() returns 3 values:
     1) distance, 2) course, 3) valid_sailing (True/False depending on length, as \
     rhumb-line sailing ceases to be accurate > 600nm)
    This function confirms correctness and outcomes from several randomised examples"""

    # 10 mins of longitude along the equator should be 10nm
    assert parallel_sailing((0,0.0), (0,0.0), (0,10.0))[0] == 10
    # 10 mins (or any distance) along a pole should be 0nm
    assert parallel_sailing((90,0.0), (0,0.0), (0,10.0))[0] == 0
    # the 'short way' will be taken across 0W/0E and ~180E/~180W
    assert parallel_sailing((0,0.0), (1,0.0), (-1,0.0))[0:2] == (120,270)
    assert parallel_sailing((0,0.0), (179,30.0), (-179,30.0))[0:2] == (60,90)
    # should return a warning rather than distance/course
    assert type(parallel_sailing((0,0.0), (0,0.0), (10,0.1))) == str
    # but 600nm exactly is fine
    assert type(parallel_sailing((0,0.0), (0,0.0), (10,0.0))) != str

def test_plane():
    go_north = plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(10,0.0), longitude_b=(0,0.0))
    go_south = plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(-10,0.0), longitude_b=(0,0.0))
    go_north_east =  plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(5,0.0), longitude_b=(5,0.0))
    go_south_west = plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(-5,0.0), longitude_b=(-5,0.0))
    go_too_far = plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(-40,0.0), longitude_b=(-160,0.0))

    assert go_north == (600,0) # north is 0, 10 degrees of latitude == 10*60
    assert go_south == (600,180) # south is 180, 10 degrees of latitude == 10*60 
    assert go_north_east[1] == 45 # equal degrees n/e should mean a course of 45
    assert go_south_west[1] == 225 # equal degrees s/w should mean a course of 225 
    assert type(go_too_far) == str # should return a warning rather than distance/course


def test_great_circle():
    start_lat,start_long,end_lat,end_long = get_random_start_end()
    print(f"{start_lat},{start_long} to {end_lat},{end_long} = \
    {great_circle_sailing(start_lat,start_long,end_lat,end_long)}")

def test_composite_great_circle():
    pass

def get_ETA():
    "distance, speed, departure_time"
    pass

def get_speed_for_ETA():
    "distance, departure_time, arrival_time"
    pass
