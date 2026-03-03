import calcs

# for later validation and possible use in GUI (1/2)
minutes = [i / 10 for i in range(600)]
valid_latitudes = (range(-89,90),minutes)
valid_longitudes = (range(-179,180),minutes)
# (2/2)
def check_positional_ranges():
    # Check degree ranges
    assert min(list(valid_longitudes[0])) == -179 and max(list(valid_longitudes[0])) == 179
    assert min(list(valid_latitudes[0])) == -89 and max(valid_latitudes[0]) == 89
    # Check minute ranges
    assert min(valid_latitudes[1]) == 0.0 and max(valid_latitudes[1]) == 59.9 
    assert min(valid_longitudes[1]) == 0.0 and max(valid_longitudes[1]) == 59.9

# Start of function testing, all 'live' when testing.py is ran - see the bottom...

def test_get_dlong_or_dlat():
    # +ve to -ve, could mean either N --> S or E -->W
    assert calcs.get_dlong_or_dlat((75,17.0),(-25,22.0)) == (-100,39.0)
    # -ve to +ve, could mean either S --> N or W --> E. Answer should be the same as the other way round
    assert calcs.get_dlong_or_dlat((-25,22.0),(75,17.0)) == (100,39.0)
    # +ve to +ve, could mean either N --> N or E --> E. With decimal
    assert calcs.get_dlong_or_dlat((10,35.0),(8,56.6)) == (-1,38.4)
    # -ve to -ve, could mean either S --> S or W --> W
    assert calcs.get_dlong_or_dlat((-75,17.0),(-25,22.0)) == (49,55.0)
    # big range for dlong, testing if we go the short way around (160, not 200)
    assert calcs.get_dlong_or_dlat((120,0.0),(-80,0.0)) == (160,0.0)
    assert calcs.get_dlong_or_dlat((-170,0.0),(170,0.0)) == (-20,0.0)
    # some textbook examples https://cmgmaritime.com/wp-content/uploads/2018/10/Basic-Navigation-Calculus-2.pdf
    assert calcs.get_dlong_or_dlat((20,50.0),(45,55.0)) == (25,5.0)
    assert calcs.get_dlong_or_dlat((10,20.0),(-30,50.0)) == (-41,10.0)
    assert calcs.get_dlong_or_dlat((175,30.0),(-170,50.0)) == (13,40.0)
    assert calcs.get_dlong_or_dlat((165,30.0),(148,50.0)) == (-16,40.0)
    assert calcs.get_dlong_or_dlat((-156,45.0),(168,30.0)) == (-34,45.0)

def test_parallel():
    # 10 mins of longitude along the equator should be 10nm
    assert calcs.parallel_sailing((0,0.0), (0,0.0), (0,10.0))[0] == 10
    # 10 mins (or any distance) along a pole should be 0nm
    assert calcs.parallel_sailing((90,0.0), (0,0.0), (0,10.0))[0] == 0
    # the 'short way' will be taken across 0W/0E and ~180E/~180W
    assert calcs.parallel_sailing((0,0.0), (1,0.0), (-1,0.0))[0:2] == (120,270)
    assert calcs.parallel_sailing((0,0.0), (179,30.0), (-179,30.0))[0:2] == (60,90)
    # >600nm should return a warning in addition to distance, course
    assert type(calcs.parallel_sailing((0,0.0), (0,0.0), (10,0.1))[2]) == str

def test_plane():
    go_north = calcs.plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(10,0.0), longitude_b=(0,0.0))
    go_south = calcs.plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(-10,0.0), longitude_b=(0,0.0))
    go_north_east =  calcs.plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(5,0.0), longitude_b=(5,0.0))
    go_south_west = calcs.plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(-5,0.0), longitude_b=(-5,0.0))
    go_too_far = calcs.plane_sailing(latitude_a=(0,0.0), longitude_a=(0,0.0), \
    latitude_b=(-40,0.0), longitude_b=(-160,0.0))

    assert go_north == (600,0) # north is 0, 10 degrees of latitude == 10*60
    assert go_south == (600,180) # south is 180, 10 degrees of latitude == 10*60 
    assert go_north_east[1] == 45 # equal degrees n/e should mean a course of 45
    assert go_south_west[1] == 225 # equal degrees s/w should mean a course of 225 
    assert type(go_too_far[2]) == str # >600nm should return a warning in addition to distance, course

def test_great_circle():
    # assert statements for textbook answers (distance)

    # https://oic-nwreviewer.blogspot.com/2014/03/great-circle-sailing.html
    test_1 = calcs.great_circle_sailing(latitude_a=(35,27.0), longitude_a=(139,39.0), \
    latitude_b=(37,48.5), longitude_b=(-122,24.0))[0]
    assert test_1 < 4474 and test_1 > 4472

    test_2 = calcs.great_circle_sailing(latitude_a=(17,18.0), longitude_a=(-25,00.0), \
    latitude_b=(25,43.0), longitude_b=(-76,36.0))[0]
    assert test_2 < 2910 and test_2 > 2906

    # https://marinegyaan.com/chapter-13-great-circle-sailing/
    test_3 = calcs.great_circle_sailing(latitude_a=(-10,25.0), longitude_a=(90,12.0), \
    latitude_b=(39,27.0), longitude_b=(55,10.0))[0]
    assert test_3 < 3573 and test_3 > 3571
    
    test_4 = calcs.great_circle_sailing(latitude_a=(50,04.0), longitude_a=(-5,45.0), \
    latitude_b=(47,34.0), longitude_b=(-52,40.0))[0]
    assert test_4 < 1830 and test_4 > 1828

    test_5 = calcs.great_circle_sailing(latitude_a=(58,42.0), longitude_a=(-5,00.0), \
    latitude_b=(32,34.0), longitude_b=(-64,30.0))[0]
    assert test_5 < 2820.2 and test_5 > 2818.2

    test_6 = calcs.great_circle_sailing(latitude_a=(49,50.0), longitude_a=(-5,12.0), \
    latitude_b=(13,6.0), longitude_b=(-59,20.0))[0]
    assert test_6 < 3434.8 and test_6 > 3432.8

def test_composite_great_circle():
    """
    TBC, rewrite of function required.

    Textbook q and a in:
    https://www.scribd.com/document/749028534/1-GC-Composite-Practice-Qus-merged 
    """
    return None # prevent assertion error while function incomplete

    test_distance_1 = calcs.composite_great_circle_sailing(latitude_a=(35,40.0),longitude_a=(141,00.0),latitude_b=(37,48.0),\
    longitude_b=(-122,40.0),limiting_latitude=(45,0.0))
    assert test_distance_1 < 4418.3 and test_distance_1 > 4414.3    


def test_get_ETA():
    # Simple test - one 24 day of sailing 
    test_ETA_1 = calcs.get_ETA(distance=240, speed=10, departure_time=('010126',0,0))
    assert str(test_ETA_1) == '2026-01-02 00:00:00'
    # month wrap around working e.g. Feb to March
    test_ETA_2 = calcs.get_ETA(distance=240*3, speed=10, departure_time=('280226',0,0))
    assert str(test_ETA_2) == '2026-03-03 00:00:00'
    # leap year test, in 2028 ETA would be march 2nd not 3rd
    test_ETA_3 = calcs.get_ETA(distance=240*3, speed=10, departure_time=('280228',0,0))
    assert str(test_ETA_3) == '2028-03-02 00:00:00'

def test_get_speed_for_ETA():
    # Assert the parallel of test_get_ETA for now, make more tests later
    test_speed_1 = calcs.get_speed_for_ETA(distance=240, departure_time=('010126',0,0),arrival_time=('020126',0,0))
    assert test_speed_1 == 10

    test_speed_2 = calcs.get_speed_for_ETA(distance=240*3, departure_time=('280226',0,0),arrival_time=('030326',0,0))
    assert test_speed_2 == 10

    test_speed_3 = calcs.get_speed_for_ETA(distance=240*3, departure_time=('280228',0,0),arrival_time=('020328',0,0))
    assert test_speed_3 == 10

# Sailing formulae
test_parallel()
test_plane()
test_great_circle()
# test_composite_great_circle()

#ETAs/Speed
test_get_ETA()
test_get_speed_for_ETA()

