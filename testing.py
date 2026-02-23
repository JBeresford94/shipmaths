from calculations import parallel_sailing, plane_sailing,\
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

def test_parallel(test_latitudes,test_longitudes):
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
    # > 600nm distance returns False, but doesn't raise error
    assert parallel_sailing((0,0.0), (0,0.0), (10,0.1))[2] == False
    # but 600nm exactly is fine
    assert parallel_sailing((0,0.0), (0,0.0), (10,0.0))[2] == True

    for test_latitude in test_latitudes:
        parallel_of_latitude = test_latitude,random.choice(minutes) 
        start = random.choice(test_longitudes),random.choice(minutes)
        end = random.choice(test_longitudes), random.choice(minutes)
        print(f"{start} to {end} along {parallel_of_latitude} = {parallel_sailing(parallel_of_latitude, start, end)}")

def test_plane():
    
    pass

def test_great_circle():
    pass

def test_composite_great_circle():
    pass
