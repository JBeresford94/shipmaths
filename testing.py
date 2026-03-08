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
    """
    assert statements against textbook answers 
    (distance within 1nm, course 1degree either side where available
    https://oic-nwreviewer.blogspot.com/2014/03/great-circle-sailing.html for test 1
    https://marinegyaan.com/chapter-13-great-circle-sailing/ for tests 2+3
    """

    test_1 = calcs.great_circle_sailing(latitude_a=(35,27.0), longitude_a=(139,39.0), \
    latitude_b=(37,48.5), longitude_b=(-122,24.0))[0]
    assert test_1 < 4474 and test_1 > 4472

    test_2 = calcs.great_circle_sailing(latitude_a=(-33,50.0), longitude_a=(23,12.0), \
    latitude_b=(-20,10.0), longitude_b=(104,0.0))
    test_2_distance, test_2_initial_course, test_2_final_course = test_2
    assert test_2_distance < 4293.5 and test_2_distance > 4291.5
    assert test_2_initial_course in range(101,103)
    assert test_2_final_course in range(59,61)

    test_3 = calcs.great_circle_sailing(latitude_a=(-10,25.0), longitude_a=(90,12.0), \
    latitude_b=(39,27.0), longitude_b=(55,10.0))
    test_3_distance, test_3_initial_course, test_3_final_course = test_3
    assert test_3_distance < 3573 and test_3_distance > 3571
    assert test_3_initial_course in range(328,330)
    assert test_3_final_course in range(318,320)

def test_composite_great_circle():
    """
    Test distances within 1nm of Textbook q and a in:
    https://www.scribd.com/document/816477581/Composite-Great-Circle-Sailing for test 1
    https://www.scribd.com/document/749028534/1-GC-Composite-Practice-Qus-merged for test 2 and 3
    """

    test_1 = calcs.composite_great_circle_sailing(latitude_a=(35,40.0),longitude_a=(141,00.0),latitude_b=(37,48.0),\
    longitude_b=(-122,40.0),limiting_latitude=(45,0.0))
    assert test_1[0] < 4417.3 and test_1[0] > 4415.3    

    test_2 = calcs.composite_great_circle_sailing(latitude_a=(-42,53.0),longitude_a=(147,20.0),latitude_b=(-52,43.0),\
    longitude_b=(-72,43.0),limiting_latitude=(-52,43.0))
    assert test_2[0] < 5324.4 and test_2[0] > 5322.4

    test_3 = calcs.composite_great_circle_sailing(latitude_a=(37,0.0),longitude_a=(-123,12.0),latitude_b=(36,0.0),\
    longitude_b=(141,30.0),limiting_latitude=(45,0.0))
    assert test_3[0] < 4385.5 and test_3[0] > 4383.5
    
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
test_composite_great_circle()

#ETAs/Speed
test_get_ETA()
test_get_speed_for_ETA()

