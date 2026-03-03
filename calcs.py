from math import radians, cos, acos, sin, atan2, degrees
from datetime import datetime, timedelta

def degrees_to_decimals(position):
    """Convert tuple of positon tuples e.g. ((60,30.0),(170,0.0)) \
    to floats e.g. (60.5,170.0) for every latitude/longitude supplied"""

    if position[0] > 0:
        return position[0] + position[1] / 60
    else:
        return position[0] - position[1] / 60

def decimal_to_degrees(decimal):
    """Convert decimal position to degrees. 
    Decimal == float. E.g 50.5
    Returns tuple (DD,MM.M). E.g. (50,30.0)
    """
    whole = int(decimal)
    remainder = decimal - whole
    minutes = round(remainder * 60, 1)
    return whole,abs(minutes)

def get_dlong_or_dlat(pos_a, pos_b):
    
    # convert to decimal and subtract
    pos_a_decimal, pos_b_decimal = degrees_to_decimals(pos_a), degrees_to_decimals(pos_b)
    dlong_or_dlat_decimal = pos_b_decimal - pos_a_decimal

    # ensure 'short way round' for dlongs
    if dlong_or_dlat_decimal > 180:
        dlong_or_dlat_decimal -= 360
    elif dlong_or_dlat_decimal < -180:
        dlong_or_dlat_decimal += 360 

    return dlong_or_dlat_decimal

def parallel_sailing(latitude, longitude_a, longitude_b):

    # get dlong, convert to minutes
    dlong = get_dlong_or_dlat(longitude_a, longitude_b)
    dlong_minutes = abs(dlong)*60

    # Course determined by +ve or -ve dlong
    course = 90 if dlong > 0 else 270

    # departure = dlong * cos(lat). Note - lat must be radians
    lat_decimal = degrees_to_decimals(latitude)
    lat = radians(lat_decimal)
    departure = round(dlong_minutes * cos(lat),1)

    if departure > 600:
        return departure, course, 'Plane sailing starts to become inaccurate over 600nm due to curvature\
 of the earth, suggest using Great Circle formula'
    return departure,course

def plane_sailing(latitude_a, longitude_a, latitude_b, longitude_b):
    
    # get dlong, dlat and convert to minutes
    dlat = get_dlong_or_dlat(latitude_a, latitude_b)
    dlong = get_dlong_or_dlat(longitude_a, longitude_b)
    dlat_minutes = dlat * 60
    dlong_minutes = dlong * 60
    
    # Mean latitude
    mean_lat_decimal = degrees_to_decimals(latitude_a) + degrees_to_decimals(latitude_b) / 2

    # Departure (distance at parallel of latitude) = dlong * cos(lat)
    departure = dlong_minutes * cos(radians(mean_lat_decimal))
   
    # get course ( tan(course) == departure/dlat )
    course_rad = atan2(departure, dlat_minutes)
    
    # Distance = dlat / cos(course)
    distance = dlat_minutes / cos(course_rad)

    # Reformat and return
    distance,course = abs(round(distance,1)), round(degrees(course_rad),1)
    if course < 0:
        course += 360
    if distance > 600:
        return distance, course, 'Plane sailing starts to become inaccurate over 600nm due to curvature\
 of the earth, suggest using Great Circle formula'
    return distance,course

def great_circle_sailing(latitude_a, longitude_a, latitude_b, longitude_b):

    # get pole P to Latitude A/B for PA and PB in spherical triangle
    lat_a_decimal, lat_b_decimal = degrees_to_decimals(latitude_a),degrees_to_decimals(latitude_b)
    # if lats named the same, PA, PB are both subtractions from that pole 
    if lat_a_decimal > 0 and lat_b_decimal > 0 or lat_a_decimal < 0 and lat_b_decimal < 0:
        pa, pb = 90 - abs(lat_a_decimal), 90 - abs(lat_b_decimal)
    # otherwise, one is the other side of the equator and this lat must be added
    else:
        if abs(lat_a_decimal) > abs(lat_b_decimal):
            pa = 90 - abs(lat_a_decimal)
            pb = 90 + abs(lat_b_decimal)
        else:
            pa = 90 + abs(lat_a_decimal)
            pb = 90 - abs(lat_b_decimal)

    # get angle P in spherical triangle, which is dlong
    p = get_dlong_or_dlat(longitude_a, longitude_b)

    # Cosine rule to get AB, as we have 2 sides PA+PB and angle P (need radians first)
    p,pa,pb = radians(p),radians(pa),radians(pb)
    cos_ab = (cos(p) * sin(pa) * sin(pb)) + (cos(pa) * cos(pb))

    # convert to ab for angular distance
    ab_radians = acos(cos_ab)
    ab = degrees(ab_radians)
    # Multiply by 60 for the number of miles
    distance = round(ab * 60,1)

    # Initial course angle a - relative
    cos_a = (cos(pb) - cos(ab_radians) * cos(pa)) / (sin(ab_radians) * sin(pa))
    a_radians = acos(cos_a)
    a = degrees(a_radians)

    # Final course angle b - relative
    cos_b = (cos(pa) - cos(ab_radians) * cos(pb)) / (sin(ab_radians) * sin(pb))
    b_radians = acos(cos_b)
    b = degrees(b_radians)

    def get_true_course(relative_course):
        """Get true course angle angle by the quadrant (NE,SE,SW,NW), using booleans with dlat and dlong"""
        north,east = get_dlong_or_dlat(latitude_a, latitude_b) > 0, (get_dlong_or_dlat(longitude_a, longitude_b) > 0) 
        if north and east:
            true_course = relative_course
        if north and not east:
            true_course = 360 - relative_course
        if east and not north:
            true_course = 180 - relative_course
        else:
            true_course = 180 + relative_course

        return round(true_course)

    return distance, get_true_course(a), get_true_course(b)

def composite_great_circle_sailing(latitude_a,
                                   longitude_a,
                                   latitude_b,
                                   longitude_b,
                                   limiting_latitude):
    pass
    # to rewrite entirely
    #https://www.youtube.com/watch?v=7OoQDUudU30
    #https://www.youtube.com/watch?v=leUxaVpwOBY

def get_ETA(distance, speed, departure_time):
    """distance,speed = int or float
    departure_time =  tuple of 3 values:
    1 - string of 'DDMMYY' e.g. '010126'
    2 - integer hour from 1-23 
    3 - integer minute from 0 to 59
    returns timedelta object of new datetime + hours"""

    # Convert departure_time into datetime
    date_string, hour, minute = departure_time
    departure_datetime = datetime.strptime(date_string, "%d%m%y").replace(hour=hour, minute=minute)
    
    # Calculate duration in hours, convert to time delta
    duration_hours = timedelta(hours=distance / speed)

    # Add to start time for ETA
    return departure_datetime + duration_hours

def get_speed_for_ETA(distance, departure_time, arrival_time):

    # Convert departure_time into datetime
    date_string, hour, minute = departure_time
    departure_datetime = datetime.strptime(date_string, "%d%m%y").replace(hour=hour, minute=minute)
    # Convert arrival_time into datetime
    date_string, hour, minute = arrival_time
    arrival_datetime = datetime.strptime(date_string, "%d%m%y").replace(hour=hour, minute=minute)

    # get time for: speed = distance / time
    duration_timedelta = (arrival_datetime - departure_datetime)
    duration = duration_timedelta.total_seconds() / 3600
    return round(distance/duration,1)
