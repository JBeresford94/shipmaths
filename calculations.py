import math
from datetime import datetime, timedelta

def convert_degrees_to_decimals(position):

    # Convert degree tuple e.g. (60,30.0) to float e.g. 60.5
    return position[0] + position[1]/60 \
    if position[0] > 0 \
    else position[0] - position[1]/60

def parallel_sailing(latitude, longitude_a, longitude_b):

    # Convert to decimal degrees
    longitude_a = convert_degrees_to_decimals(longitude_a)
    longitude_b = convert_degrees_to_decimals(longitude_b)
    latitude = convert_degrees_to_decimals(latitude)

    # factor in E/W crossings and ensure dlong is the 'short way'
    dlong = longitude_b - longitude_a
    if dlong > 180:
        dlong -= 360
    elif dlong < -180:
        dlong += 360

    # Course determined by +ve or -ve dlong
    course = 90 if dlong > 0 else 270

    # Convert to minutes
    dlong_minutes = abs(dlong) * 60

    # Departure (lat must be radians)
    departure = round(dlong_minutes * math.cos(math.radians(latitude)),1)

    valid_sailing = departure <= 600
    return departure, course, valid_sailing


def plane_sailing(latitude_a, longitude_a, latitude_b, longitude_b):
    
    # Convert to decimal degrees
    latitude_b = convert_degrees_to_decimals(latitude_a)
    longitude_a = convert_degrees_to_decimals(longitude_a)
    latitude_b = convert_degrees_to_decimals(latitude_a)
    longitude_b = convert_degrees_to_decimals(longitude_b)

    # Calculate difference in Latitude and Longitude
    dlat, dlong = (latitude_b - latitude_a), (longitude_b - longitude_a)
    # factor in E/W crossings and ensure dlong is the 'short way'
    if dlong > 180:
        dlong -= 360
    elif dlong < -180:
        dlong += 360

    # dlong,dlat in minutes
    dlat_mins, dlong_mins = dlat*60, dlong*60
    
    # Mean latitude
    mean_lat = (latitude_a + latitude_b)/2

    # Departure (distance at parallel of latitude)
    departure = dlong_mins * math.cos(math.radians(mean_lat))
    
    # Course
    course_rad = math.atan2(departure, dlat_mins)
    
    # Using cosine right triangle rule, calculate Distance: 
    distance = dlat_mins / math.cos(course_rad)

    # Reformat and return
    course,distance = round(math.degrees(course_rad),1), abs(round(distance,1))
    if course < 0:
        course += 360
    return course,distance if distance < 600 else False


def great_circle_sailing(latitude_a, longitude_a, latitude_b, longitude_b):

    # Convert to decimal degrees
    latitude_b = convert_degrees_to_decimals(latitude_a)
    longitude_a = convert_degrees_to_decimals(longitude_a)
    latitude_b = convert_degrees_to_decimals(latitude_a)
    longitude_b = convert_degrees_to_decimals(longitude_b)

    # Convert decimals to radians
    latitude_a_rad = math.radians(latitude_a)
    latitude_b_rad = math.radians(latitude_b)
    longitude_a_rad = math.radians(longitude_a)
    longitude_b_rad = math.radians(longitude_b)

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
    distance_nm = 3440.065 * angular_distance

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

    # Convert limiting latitude to decimal
    limiting_latitude_decimal = limiting_latitude[0] + limiting_latitude[1] / 60

    # Get full great circle data
    initial_course, final_course, total_gc_distance = great_circle_sailing(
        latitude_a, longitude_a,
        latitude_b, longitude_b,
        radius_nm
    )

    # Estimate vertex latitude

    latitude_start_decimal = latitude_a[0] + latitude_a[1] / 60
    latitude_start_rad = math.radians(latitude_start_decimal)
    initial_course_rad = math.radians(initial_course)

    vertex_latitude_rad = math.acos(
        abs(math.cos(latitude_start_rad) * math.sin(initial_course_rad))
    )

    vertex_latitude = math.degrees(vertex_latitude_rad)

    # If vertex within limit, no composite needed
    if vertex_latitude <= limiting_latitude_decimal:
        return {
            "type": "Great Circle Only",
            "total_distance_nm": total_gc_distance,
            "initial_course": initial_course,
            "final_course": final_course
        }

    # Composite required
    # Find approximate intersection longitude shift
    # Using spherical interpolation

    latitude_limit_rad = math.radians(limiting_latitude_decimal)
    latitude_start_rad = math.radians(latitude_start_decimal)

    # Angular distance from start to limiting latitude
    angular_distance_to_limit = math.acos(
        math.sin(latitude_start_rad) * math.sin(latitude_limit_rad) +
        math.cos(latitude_start_rad) * math.cos(latitude_limit_rad)
    )

    distance_to_limit_nm = 3440.065 * angular_distance_to_limit

    # Approximate longitude shift using initial course
    delta_longitude_limit = math.degrees(
        math.atan2(
            math.sin(initial_course_rad) * math.sin(angular_distance_to_limit),
            math.cos(angular_distance_to_limit)
        )
    )

    # Intersection longitudes
    longitude_start_decimal = longitude_a[0] + longitude_a[1] / 60
    longitude_limit_1 = longitude_start_decimal + delta_longitude_limit

    longitude_end_decimal = longitude_b[0] + longitude_b[1] / 60
    longitude_limit_2 = longitude_end_decimal - delta_longitude_limit

    # Parallel leg
    parallel_distance_nm, parallel_course = parallel_sailing(
        limiting_latitude,
        (longitude_limit_1, 0),
        (longitude_limit_2, 0)
    )

    # Final GC leg - From second intersection to destination
    gc_leg_2 = great_circle_sailing(
        (limiting_latitude_decimal, 0),
        (longitude_limit_2, 0),
        latitude_b,
        longitude_b,
        radius_nm
    )

    total_distance = (
        distance_to_limit_nm +
        parallel_distance_nm +
        gc_leg_2[2]
    )

    if total_distance < 600:
        return False

    return {
        "type": "Composite Great Circle",
        "leg_1_gc_nm": round(distance_to_limit_nm, 1),
        "parallel_nm": round(parallel_distance_nm, 1),
        "leg_2_gc_nm": gc_leg_2[2],
        "total_distance_nm": round(total_distance, 1)
    }

def get_ETA(distance, speed, departure_time):

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
