import math
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

    return decimal_to_degrees(dlong_or_dlat_decimal)

def parallel_sailing(latitude, longitude_a, longitude_b):

    # get dlong, convert to minutes
    dlong = get_dlong_or_dlat(longitude_a, longitude_b)
    dlong_minutes = abs(dlong[0])*60 + dlong[1]

    # Course determined by +ve or -ve dlong
    course = 90 if dlong[0] > 0 else 270

    # departure = dlong * cos(lat). Note - lat must be radians
    lat_decimal = degrees_to_decimals(latitude)
    lat = math.radians(lat_decimal)
    departure = round(dlong_minutes * math.cos(lat),1)

    if departure > 600:
        return departure, course, 'Plane sailing starts to become inaccurate over 600nm due to curvature\
 of the earth, suggest using Great Circle formula'
    return departure,course

def plane_sailing(latitude_a, longitude_a, latitude_b, longitude_b):
    
    # get dlong, dlat and convert to minutes
    dlat = get_dlong_or_dlat(latitude_a, latitude_b)
    dlong = get_dlong_or_dlat(longitude_a, longitude_b)
    dlat_minutes = dlat[0]*60 + dlat[1]
    dlong_minutes = dlong[0]*60 + dlong[1]
    
    # Mean latitude
    mean_lat_decimal = degrees_to_decimals(latitude_a) + degrees_to_decimals(latitude_b) / 2

    # Departure (distance at parallel of latitude) = dlong * cos(lat)
    departure = dlong_minutes * math.cos(math.radians(mean_lat_decimal))
   
    # get course ( tan(course) == departure/dlat )
    course_rad = math.atan2(departure, dlat_minutes)
    
    # Distance = dlat / cos(course)
    distance = dlat_minutes / math.cos(course_rad)

    # Reformat and return
    distance,course = abs(round(distance,1)), round(math.degrees(course_rad),1)
    if course < 0:
        course += 360
    if distance > 600:
        return distance, course, 'Plane sailing starts to become inaccurate over 600nm due to curvature\
 of the earth, suggest using Great Circle formula'
    return distance,course

def great_circle_sailing(latitude_a, longitude_a, latitude_b, longitude_b):
    # to refactor more closely along lines of OOW methods, but it works for now...
    # https://www.youtube.com/watch?v=6tzQRI_OZ6Q

    # Convert to decimal degrees
    latitude_a_dec,longitude_a_dec,latitude_b_dec,longitude_b_dec = \
    convert_degrees_to_decimals((latitude_a,longitude_a,latitude_b,longitude_b))

    # Convert decimals to radians
    latitude_a_rad = math.radians(latitude_a_dec)
    longitude_a_rad = math.radians(longitude_a_dec)
    latitude_b_rad = math.radians(latitude_b_dec)
    longitude_b_rad = math.radians(longitude_b_dec)

    # Difference in longitude (delta)
    delta_longitude = longitude_b_rad - longitude_a_rad

    # Ensure shortest route
    if delta_longitude > math.pi:
        delta_longitude -= 2 * math.pi
    elif delta_longitude < -math.pi:
        delta_longitude += 2 * math.pi

    # Calculate angular distance
    cosine_angular_distance = (
        math.sin(latitude_a_rad) * math.sin(latitude_b_rad)
        + math.cos(latitude_a_rad)
        * math.cos(latitude_b_rad)
        * math.cos(delta_longitude)
    )

    # Guard against floating point rounding errors
    cosine_angular_distance = max(-1, min(1, cosine_angular_distance))

    angular_distance = math.acos(cosine_angular_distance)

    # Convert to nautical miles
    distance_nm = 3439 * angular_distance

    if distance_nm < 600:
        return False

    # Initial course
    y_component = math.sin(delta_longitude) * math.cos(latitude_b_rad)

    x_component = (
        math.cos(latitude_a_rad) * math.sin(latitude_b_rad)
        - math.sin(latitude_a_rad)
        * math.cos(latitude_b_rad)
        * math.cos(delta_longitude)
    )

    initial_course_rad = math.atan2(y_component, x_component)
    initial_course = math.degrees(initial_course_rad)

    if initial_course < 0:
        initial_course += 360

    # Final course
    y_component_final = math.sin(-delta_longitude) * math.cos(latitude_a_rad)

    x_component_final = (
        math.cos(latitude_b_rad) * math.sin(latitude_a_rad)
        - math.sin(latitude_b_rad)
        * math.cos(latitude_a_rad)
        * math.cos(-delta_longitude)
    )

    final_course_rad = math.atan2(y_component_final, x_component_final)
    final_course = math.degrees(final_course_rad)

    if final_course < 0:
        final_course += 360

    return round(initial_course, 1), round(final_course, 1), round(distance_nm, 1)

def composite_great_circle_sailing(latitude_a,
                                   longitude_a,
                                   latitude_b,
                                   longitude_b,
                                   limiting_latitude):
    pass
    # to rewrite entirely

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
