from math import radians, cos, acos, sin, asin, tan, atan2, sqrt, degrees
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def degrees_to_decimals(position):
    """Convert (DD, MM.M) to decimal degrees.

    The sign of DD carries the hemisphere: negative DD = S or W.
    e.g. (-45, 30.0) -> -45.5,  (170, 45.0) -> 170.75
    """
    d, m = position
    return d + (m / 60 if d >= 0 else -m / 60)


def decimal_to_degrees(decimal):
    """Convert decimal degrees to (DD, MM.M), e.g. 50.5 -> (50, 30.0)."""
    whole   = int(decimal)
    minutes = round(abs(decimal - whole) * 60, 1)
    return whole, minutes


def get_dlong_or_dlat(pos_a, pos_b):
    """Signed difference pos_b - pos_a in decimal degrees.

    Wraps longitudes to (-180, 180] so we always take the short way round.
    """
    diff = degrees_to_decimals(pos_b) - degrees_to_decimals(pos_a)
    if diff > 180:
        diff -= 360
    elif diff < -180:
        diff += 360
    return diff

# ---------------------------------------------------------------------------
# Plane / parallel sailing
# ---------------------------------------------------------------------------

_RHUMB_LIMIT   = 600  # nm
_RHUMB_WARNING = (
    "Plane sailing becomes inaccurate over 600 nm due to earth's curvature; "
    "consider using the Great Circle formula instead."
)


def parallel_sailing(latitude, longitude_a, longitude_b):
    """Departure (nm) and course (degT) along a parallel of latitude."""
    dlong      = get_dlong_or_dlat(longitude_a, longitude_b)
    dlong_mins = abs(dlong) * 60
    course     = 90 if dlong > 0 else 270
    departure  = round(dlong_mins * cos(radians(degrees_to_decimals(latitude))), 1)
    if departure > _RHUMB_LIMIT:
        return departure, course, _RHUMB_WARNING
    return departure, course


def plane_sailing(latitude_a, longitude_a, latitude_b, longitude_b):
    """Distance (nm) and course (degT) by plane sailing."""
    dlat       = get_dlong_or_dlat(latitude_a,  latitude_b)
    # Handle equal latitude edge case
    if dlat == 0:
        return parallel_sailing(latitude_a, longitude_a, longitude_b)

    dlong      = get_dlong_or_dlat(longitude_a, longitude_b)
    dlat_mins  = dlat  * 60
    dlong_mins = dlong * 60

    # Mean latitude — parentheses around the sum are essential
    mean_lat  = radians(
        (degrees_to_decimals(latitude_a) + degrees_to_decimals(latitude_b)) / 2
    )
    departure  = dlong_mins * cos(mean_lat)

    # Course angle and distance via atan2 + Pythagoras (handles dlat=0 safely)
    course_rad = atan2(departure, dlat_mins)
    distance   = dlat_mins / cos(course_rad)
    distance,course = abs(round(distance,1)), round(degrees(course_rad),1)

    if course < 0:
        course += 360

    if distance > _RHUMB_LIMIT:
        return distance, course, _RHUMB_WARNING
    return distance, course


# ---------------------------------------------------------------------------
# Great circle helpers
# ---------------------------------------------------------------------------

def _polar_distance(lat_decimal):
    """Angular distance from the elevated pole to a latitude (degrees, always +ve)."""
    return 90.0 - abs(lat_decimal)


def _gc_sides(latitude_a, latitude_b):
    """(PA, PB) — polar distances for the spherical triangle.

    The elevated pole is the one on the same side as point A.
    When B is in the opposite hemisphere, PB = 90 + |lat_b|.
    """
    lat_a = degrees_to_decimals(latitude_a)
    lat_b = degrees_to_decimals(latitude_b)
    pa    = _polar_distance(lat_a)
    pb    = (_polar_distance(lat_b) if (lat_a >= 0) == (lat_b >= 0)
             else 90.0 + abs(lat_b))
    return pa, pb


def _forward_bearing(lat_a_dec, lon_a_dec, lat_b_dec, lon_b_dec):
    """True bearing from A to B using the atan2 formula. Returns value in [0, 360)."""
    la, loa = radians(lat_a_dec), radians(lon_a_dec)
    lb, lob = radians(lat_b_dec), radians(lon_b_dec)
    dlon    = lob - loa
    x       = sin(dlon) * cos(lb)
    y       = cos(la) * sin(lb) - sin(la) * cos(lb) * cos(dlon)
    return round((degrees(atan2(x, y)) + 360) % 360)


# ---------------------------------------------------------------------------
# Great circle sailing
# ---------------------------------------------------------------------------

def great_circle_sailing(latitude_a, longitude_a, latitude_b, longitude_b):
    """Great circle distance (nm), initial course and final course (both degT).

    Distance is computed via the spherical cosine rule.
    Initial and final courses use the unambiguous atan2 forward-bearing formula.
    """
    lat_a = degrees_to_decimals(latitude_a)
    lon_a = degrees_to_decimals(longitude_a)
    lat_b = degrees_to_decimals(latitude_b)
    lon_b = degrees_to_decimals(longitude_b)

    pa, pb = _gc_sides(latitude_a, latitude_b)
    p      = get_dlong_or_dlat(longitude_a, longitude_b)   # angle at the pole

    p_r, pa_r, pb_r = radians(p), radians(pa), radians(pb)

    # Spherical cosine rule: cos(AB) = cos(P)·sin(PA)·sin(PB) + cos(PA)·cos(PB)
    cos_ab   = cos(p_r) * sin(pa_r) * sin(pb_r) + cos(pa_r) * cos(pb_r)
    distance = round(degrees(acos(cos_ab)) * 60, 1)

    initial_course = _forward_bearing(lat_a, lon_a, lat_b, lon_b)
    # Arriving bearing = back-bearing of reversed leg + 180
    final_course   = int((_forward_bearing(lat_b, lon_b, lat_a, lon_a) + 180) % 360)

    return distance, initial_course, final_course


# ---------------------------------------------------------------------------
# Composite great circle sailing
# ---------------------------------------------------------------------------

def _napier_right_triangle(pa_deg, pv_deg):
    """Solve the right-angled spherical triangle PAV using Napier's rules.

    Right angle is at V — the point where the GC track is tangent to the
    limiting parallel.  Given:
        PA = polar distance of the departure/arrival point (degrees)
        PV = polar distance of the limiting latitude       (degrees)

    Returns (p1, a_rel, av_nm) where:
        p1    = dlong at the pole between the point and the vertex (degrees)
        a_rel = course angle at the point, always positive 0-90 deg
        av_nm = GC arc length from the point to the vertex (nautical miles)

    Napier's rules with right angle at V, circular parts
    (90-A) | (90-PA) | PV | p1 | (90-AV):

        sin(A)  = sin(PV) / sin(PA)    [sin = product of sines of adjacents]
        cos(AV) = cos(PA) / cos(PV)    [cos of middle = product of cos of opposites]
        cos(p1) = tan(PV) / tan(PA)    [cos of middle = product of cos of opposites]
    """
    pa_r = radians(pa_deg)
    pv_r = radians(pv_deg)

    a_rel = degrees(asin(sin(pv_r) / sin(pa_r)))
    av_nm = round(degrees(acos(cos(pa_r) / cos(pv_r))) * 60, 1)
    p1    = degrees(acos(tan(pv_r) / tan(pa_r)))

    return p1, a_rel, av_nm


def composite_great_circle_sailing(latitude_a, longitude_a,
                                   latitude_b, longitude_b,
                                   limiting_latitude):
    """Total distance (nm) for a composite great circle passage.

    Route: A --(GC)--> V --(parallel sail)--> W --(GC)--> B
    V and W are the vertices of their GC arcs, both on the limiting parallel.

    Returns (total_nm, initial_course_degT, final_course_degT).

    Raises ValueError if:
    - the limiting latitude is not more extreme (closer to the pole) than
      both departure and destination, or
    - the two GC arcs overlap (limiting latitude too restrictive).

    References:
        https://www.youtube.com/watch?v=7OoQDUudU30
        https://www.youtube.com/watch?v=leUxaVpwOBY
    """
    lat_a   = degrees_to_decimals(latitude_a)
    lon_a   = degrees_to_decimals(longitude_a)
    lat_b   = degrees_to_decimals(latitude_b)
    lon_b   = degrees_to_decimals(longitude_b)
    lat_lim = degrees_to_decimals(limiting_latitude)

    pa = _polar_distance(lat_a)
    pb = _polar_distance(lat_b)
    pv = _polar_distance(lat_lim)

    # if pv >= pa or pv >= pb:
    #     raise ValueError(
    #         f"Limiting latitude ({lat_lim}°) must be more extreme (closer to the pole) "
    #         f"than both departure ({lat_a}°) and destination ({lat_b}°)."
    #     )

    p1, _a_rel, av = _napier_right_triangle(pa, pv)
    p2, _b_rel, bw = _napier_right_triangle(pb, pv)

    p_total = get_dlong_or_dlat(longitude_a, longitude_b)  # signed dlong A->B
    p3      = abs(p_total) - p1 - p2                        # dlong of parallel leg

    # if p3 < 0:
    #     raise ValueError(
    #         f"Limiting latitude {lat_lim}° is too restrictive — the two GC arcs "
    #         f"overlap (p3 = {p3:.2f}°). Use a less restrictive limiting latitude."
    #     )

    # Parallel leg: departure = dlong_minutes * cos(lat)
    vw = round(p3 * 60 * cos(radians(lat_lim)), 1)

    # Vertex positions for true-course calculation via atan2
    sign  = 1 if p_total >= 0 else -1
    lon_v = lon_a + sign * p1   # V is p1° from A in the direction of travel
    lon_w = lon_b - sign * p2   # W is p2° from B, coming from the parallel

    initial_course = _forward_bearing(lat_a,   lon_a,  lat_lim, lon_v)
    final_course   = _forward_bearing(lat_lim, lon_w,  lat_b,   lon_b)

    return round(av + vw + bw, 1), initial_course, final_course


# ---------------------------------------------------------------------------
# ETA helpers
# ---------------------------------------------------------------------------

def _parse_time(time_tuple):
    """Convert ('DDMMYY', hour, minute) to a datetime object."""
    date_string, hour, minute = time_tuple
    return datetime.strptime(date_string, "%d%m%y").replace(hour=hour, minute=minute)


def get_ETA(distance, speed, departure_time):
    """Return ETA as a datetime.

    Args:
        distance:       nautical miles (int or float)
        speed:          knots (int or float)
        departure_time: ('DDMMYY', hour, minute)
    """
    return _parse_time(departure_time) + timedelta(hours=distance / speed)


def get_speed_for_ETA(distance, departure_time, arrival_time):
    """Return the required speed (knots) to cover distance in the available time."""
    hours = (
        (_parse_time(arrival_time) - _parse_time(departure_time)).total_seconds() / 3600
    )
    return round(distance / hours, 1)
