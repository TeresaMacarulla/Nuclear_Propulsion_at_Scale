import glob
from pathlib import Path
import re
import copy
import csv
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import searoute as sr
from utilities import init_country_from_file, init_ship_from_file


COUNTRY_INPUT_DIR = Path("inputs") / "country"
SHIP_INPUT_DIR = Path("inputs") / "ship"
ROUTE_CONNECTION_FILE = Path("inputs") / "port_connection_proposals2.txt"
ROUTE_SUMMARY_TABLE = Path("outputs") / "maritime" / "route_network_summary_by_year.txt"
ROUTE_ALLOCATION_TABLE = Path("outputs") / "maritime" / "route_network_allocation_by_year.txt"

OUTPUT_MAP_DIR = Path("outputs") / "maritime" / "all_routes"
OUTPUT_ROUTE_DIR = Path("outputs") / "maritime" / "routes_by_segment"
MAP_IMAGE = OUTPUT_MAP_DIR / "world_map_equirectangular.jpg"

# LOADING INPUTS

def load_port_connection_proposals(route_file=ROUTE_CONNECTION_FILE):
    """
    Read the final port-connection proposal file with corrected route distances.
    """

    routes = []

    with open(route_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")

        for row in reader:
            row["start_port_available_from_year"] = int(row["start_port_available_from_year"])
            row["end_port_available_from_year"] = int(row["end_port_available_from_year"])
            row["distance_km_estimate"] = float(row["distance_km_estimate"])
            row["proposed_operation_year"] = int(row["proposed_operation_year"])
            row["route_preference_score"] = float(row["route_preference_score"])

            row["ship_segments"] = row["ship_segments"].split("|")

            routes.append(row)

    return routes

def load_all_countries(input_dir=COUNTRY_INPUT_DIR):
    """Read all country_*.txt files from the input country folder."""
    country_files = sorted(glob.glob(str(input_dir / "country_*.txt")))

    if not country_files:
        raise FileNotFoundError(f"No country_*.txt files found in {input_dir}")

    countries = []

    for filename in country_files:
        country = init_country_from_file(filename)
        countries.append(country)

    return countries

def load_ship_segments(input_dir=SHIP_INPUT_DIR):
    """Read all ship_*.txt files from the input ship folder."""
    ship_files = sorted(glob.glob(str(input_dir / "ship_*.txt")))

    if not ship_files:
        raise FileNotFoundError(f"No ship_*.txt files found in {input_dir}")
    
    ships = []

    for filename in ship_files:
        ship = init_ship_from_file(filename)
        ships.append(ship)

    return ships

# CALL FOR OPERATING PORTS

def ensure_list(value):
    """Ensure that a scalar value is treated as a list."""
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]

def get_operating_ports(countries, year):
    """Return all ports that are active in the selected year."""
    active_ports = []

    for country in countries:
        if not country.operation:
            continue

        port_names = ensure_list(country.port_names)
        latitudes = ensure_list(country.latitude)
        longitudes = ensure_list(country.longitude)
        available_years = ensure_list(country.available_from_year)

        if not (
            len(port_names)
            == len(latitudes)
            == len(longitudes)
            == len(available_years)
            == country.ports
        ):
            raise ValueError(
                f"Inconsistent port data for {country.name}: "
                f"{len(port_names)} names, "
                f"{len(latitudes)} latitudes, "
                f"{len(longitudes)} longitudes, "
                f"{len(available_years)} start years, "
                f"but ports={country.ports}"
            )

        for port_name, lat, lon, start_year in zip(
            port_names, latitudes, longitudes, available_years
        ):
            if year >= start_year:
                active_ports.append(
                    {
                        "country": country.name,
                        "iso3": country.iso3,
                        "port_name": port_name,
                        "latitude": float(lat),
                        "longitude": float(lon),
                        "start_year": float(start_year),
                    }
                )

    return active_ports

# CALCULATE DISTANCES 

def normalize_longitude(lon):
    """Normalize longitude to the range [-180, 180]."""
    return ((float(lon) + 180.0) % 360.0) - 180.0

def route_distance(port_a, port_b):
    """
    Compute a sea-route distance between two ports using the searoute package.

    The searoute package returns a route that follows maritime paths and avoids
    land.
    """

    origin = [float(port_a["longitude"]), float(port_a["latitude"])]
    destination = [float(port_b["longitude"]), float(port_b["latitude"])]

    feature = sr.searoute(origin, destination, units="km")

    coordinates = feature["geometry"]["coordinates"]

    coordinates = [
        [normalize_longitude(point[0]), float(point[1])]
        for point in coordinates
    ]

    properties = feature.get("properties", {})
    distance_km = properties.get("length", None)

    return distance_km, coordinates

def haversine_distance_km(point_a, point_b):
    """
    Calculate great-circle distance between two points.

    Inputs
    ------
    point_a, point_b:
        dictionaries with:
            "longitude"
            "latitude"

    Output
    ------
    Distance in km.
    """

    radius_earth_km = 6371.0

    lon1 = math.radians(float(point_a["longitude"]))
    lat1 = math.radians(float(point_a["latitude"]))
    lon2 = math.radians(float(point_b["longitude"]))
    lat2 = math.radians(float(point_b["latitude"]))

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Correct for dateline crossing
    if delta_lon > math.pi:
        delta_lon -= 2.0 * math.pi
    elif delta_lon < -math.pi:
        delta_lon += 2.0 * math.pi

    a = (
        math.sin(delta_lat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2.0) ** 2
    )

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return radius_earth_km * c

def route_distance_from_waypoints(waypoints):
    """
    Calculate total distance along a list of waypoints.
    """

    total_distance_km = 0.0
    coordinates = []

    for point in waypoints:
        coordinates.append(
            [
                normalize_longitude(point["longitude"]),
                float(point["latitude"]),
            ]
        )

    for i in range(len(waypoints) - 1):
        total_distance_km += haversine_distance_km(
            waypoints[i],
            waypoints[i + 1],
        )

    return total_distance_km, coordinates

NSR_WAYPOINTS_WEST_TO_EAST = [
    {
        "port_name": "Kara Strait",
        "longitude": 60.0,
        "latitude": 70.5,
    },
    {
        "port_name": "Vilkitsky Strait",
        "longitude": 100.5,
        "latitude": 77.5,
    },
    {
        "port_name": "Laptev Sea",
        "longitude": 130.0,
        "latitude": 73.5,
    },
    {
        "port_name": "East Siberian Sea",
        "longitude": 160.0,
        "latitude": 70.5,
    },
    {   
        "port_name": "Proliv Longa",
        "longitude": 178.800941,
        "latitude": 69.802411, 
    },
    {
        "port_name": "Bering Strait",
        "longitude": -169.5,
        "latitude": 65.8,
    },
]

def route_distance_model(port_a, port_b, route_type):
    """
    Calculate route distance depending on route type.

    Normal routes use searoute.
    Arctic NSR routes use predefined Arctic waypoints.
    """

    if route_type == "arctic_nsr":
        waypoints = [port_a] + NSR_WAYPOINTS_WEST_TO_EAST + [port_b]
        return route_distance_from_waypoints(waypoints)

    else:
        return route_distance(port_a, port_b)

# PLOT ROUTES IN A MAP

def safe_filename(text):
    """Create a safe filename."""
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

def split_route_at_dateline(coordinates):
    """
    Split a route into segments if it crosses the international dateline.

    This prevents matplotlib from drawing a wrong horizontal line across
    the whole map.
    """

    if not coordinates:
        return []

    segments = [[coordinates[0]]]

    for point in coordinates[1:]:
        previous_lon = segments[-1][-1][0]
        current_lon = point[0]

        if abs(current_lon - previous_lon) > 180:
            segments.append([point])
        else:
            segments[-1].append(point)

    return [segment for segment in segments if len(segment) >= 2]

# COMPUTE THE FLEET CAPACITY IN KM AND PORT CALLS

KNOT_TO_KM_H = 1.852

def add_distance_to_ships(ships):
    """
    Add annual sailing distance to each ship segment.
    Input:
        ships: list returned by load_ship_segments()
    Output:
        list of ship objects with an additional attribute:
            ship.distance
    The distance is calculated as:
        distance [km/year] = avg_speed [knots] * 1.852 * op_time [h/year]
    """

    ships_with_distance = []

    for ship in ships:
        ship_with_distance = copy.copy(ship)

        avg_speed_knots = ship.avg_speed
        operating_hours = ship.op_time

        annual_distance_km = avg_speed_knots * KNOT_TO_KM_H * operating_hours

        ship_with_distance.distance = annual_distance_km
        ships_with_distance.append(ship_with_distance)

    return ships_with_distance

def total_distance_year(ships, file, plot, start_year=2035, output_file=Path("outputs") / "maritime"):
    """
    Calculate total annual fleet sailing distance by year.

    Inputs
    ------
    ships:
        Output of add_distance_to_ships(ships).
        Each ship object must have:
            ship.distance  [km/year per ship]

    file:
        Path to deployment_baseline.txt.

    start_year:
        First year represented by the first data row in the deployment file.

    Output
    ------
    List of dictionaries:
        [
            {"year": 2035, "total_distance_km": ...},
            {"year": 2036, "total_distance_km": ...},
            ...
        ]
    """

    # Map ship segment name -> distance per ship per year
    ship_distance = {}

    for ship in ships:
        ship_name = ship.shipname
        ship_distance[ship_name] = float(ship.distance)

    total_distances = []

    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        raise ValueError("Deployment file is empty.")

    # First line contains the deployment segment names
    deployment_segment_order = lines[0].strip().split()

    if plot:
        years = []
        distance_by_segment = {}
        for segment_name in deployment_segment_order:
            distance_by_segment[segment_name] = []
        total_distance = []
    
    data_lines = lines[1:]
    data_row_index = 0

    for line_number, line in enumerate(data_lines, start=2):
        line = line.strip()

        if not line:
            continue

        ship_numbers = [float(value) for value in line.split()]

        year = start_year + data_row_index
        
        if plot:
            years.append(year)
            yearly_total_distance = 0.0
        
        total_distance_km = 0.0

        for segment_name, number_of_ships in zip(
            deployment_segment_order,
            ship_numbers,
        ):
            if segment_name not in ship_distance:
                raise ValueError(
                    f"Ship segment '{segment_name}' is present in the deployment file "
                    "but was not found in the loaded ship objects.\n"
                    f"Available ship segments are: {list(ship_distance.keys())}"
                )
            
            if plot:
                segment_distance = number_of_ships * ship_distance[segment_name]
                distance_by_segment[segment_name].append(segment_distance)
                yearly_total_distance += segment_distance
            
            total_distance_km += number_of_ships * ship_distance[segment_name]
        
        if plot:
            total_distance.append(yearly_total_distance)
        
        total_distances.append(
            {
                "year": year,
                "total_distance_km": total_distance_km,
            }
        )

        data_row_index += 1
    
    if plot:
        # Plot only once, after all years have been processed
        fig, ax = plt.subplots(figsize=(14, 8))

        # Plot each ship segment
        for segment_name, distances in distance_by_segment.items():
            ax.plot(
                years,
                [distance / 1e6 for distance in distances],
                linewidth=2.2,
                alpha=0.75,
                label=segment_name.replace("_", " "),
            )

        # Plot total fleet distance
        ax.plot(
            years,
            [distance / 1e6 for distance in total_distance],
            linewidth=4.0,
            color="black",
            label="Total fleet",
        )

        ax.set_xlabel("Year", fontsize=20)
        ax.set_ylabel("Annual sailing distance [million km/year]", fontsize=20)
        ax.tick_params(axis="both", labelsize=20)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=18, ncol=2)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.show()
        print(f"Fleet distance plot saved to: {output_file}")
    
    return total_distances

def total_port_calls_year(ships, file, plot, start_year=2035, output_file=Path("outputs") / "maritime"):
    """
    Calculate total annual fleet port calls by year.

    Inputs
    ------
    ships:
        Each ship object must have:
            ship.portcalls [calls/year per ship]

    file:
        Path to deployment_baseline.txt.

    start_year:
        First year represented by the first data row in the deployment file.

    Output
    ------
    List of dictionaries:
        [
            {"year": 2035, "total_portcalls": ...},
            {"year": 2036, "total_portcalls": ...},
            ...
        ]
    """

    # Map ship segment name -> distance per ship per year
    ship_portcalls = {}

    for ship in ships:
        ship_name = ship.shipname
        ship_portcalls[ship_name] = float(ship.portcalls)

    total_portcalls = []

    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if not lines:
        raise ValueError("Deployment file is empty.")

    # First line contains the deployment segment names
    deployment_segment_order = lines[0].strip().split()

    if plot:
        years = []
        portcalls_by_segment = {}
        for segment_name in deployment_segment_order:
            portcalls_by_segment[segment_name] = []
        total_portcall = []

    data_lines = lines[1:]
    data_row_index = 0

    for line_number, line in enumerate(data_lines, start=2):
        line = line.strip()

        if not line:
            continue

        ship_numbers = [float(value) for value in line.split()]

        year = start_year + data_row_index

        if plot:
            years.append(year)
            yearly_total_portcall = 0.0

        total_portcal_n = 0.0

        for segment_name, number_of_ships in zip(
            deployment_segment_order,
            ship_numbers,
        ):
            if segment_name not in ship_portcalls:
                raise ValueError(
                    f"Ship segment '{segment_name}' is present in the deployment file "
                    "but was not found in the loaded ship objects.\n"
                    f"Available ship segments are: {list(ship_portcalls.keys())}"
                )

            if plot:
                segment_portcall = number_of_ships * ship_portcalls[segment_name]
                portcalls_by_segment[segment_name].append(segment_portcall)
                yearly_total_portcall += segment_portcall
            
            total_portcal_n += number_of_ships * ship_portcalls[segment_name]

        if plot:
            total_portcall.append(yearly_total_portcall)

        total_portcalls.append(
            {
                "year": year,
                "total_portcal_n": total_portcal_n,
            }
        )

        data_row_index += 1

    if plot:
        # Plot only once, after all years have been processed
        fig, ax = plt.subplots(figsize=(14, 8))

        # Plot each ship segment
        for segment_name, calls in portcalls_by_segment.items():
            ax.plot(
                years,
                [call / 1.0 for call in calls],
                linewidth=2.2,
                alpha=0.75,
                label=segment_name.replace("_", " "),
            )

        # Plot total fleet distance
        ax.plot(
            years,
            [call / 1.0 for call in total_portcall],
            linewidth=4.0,
            color="black",
            label="Total fleet",
        )

        ax.set_xlabel("Year", fontsize=20)
        ax.set_ylabel("Annual portcalls per year", fontsize=20)
        ax.tick_params(axis="both", labelsize=20)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=18, ncol=2)

        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        plt.show()
        print(f"Fleet portcalls plot saved to: {output_file}")

    return total_portcalls

# DEFINE ROUTES FOR EACH YEAR FOR EACH SHIP SEGMENT

def get_ship_numbers_for_year(
    deployment_file,
    year,
    start_year=2035,
):
    """
    Read deployment_baseline.txt and return the number of ships
    of each segment in the selected year.
    """

    with open(deployment_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    segment_names = lines[0].strip().split()
    row_index = year - start_year
    selected_line = lines[row_index + 1].strip()
    ship_numbers = [float(value) for value in selected_line.split()]
    ships_by_segment = {}

    for segment_name, number_of_ships in zip(segment_names, ship_numbers):
        ships_by_segment[segment_name] = number_of_ships

    return ships_by_segment

def build_ship_lookup(ships):
    """
    Create a dictionary:
        ship segment name -> ship object
    """
    ship_lookup = {}

    for ship in ships:
        ship_lookup[ship.shipname] = ship

    return ship_lookup

def find_value_for_year(rows, year, possible_keys):
    """
    Find a value in a list of dictionaries returned by total_distance_year()
    or total_port_calls_year().
    """

    for row in rows:
        if row["year"] == year:
            for key in possible_keys:
                if key in row:
                    return row[key]

    raise ValueError(f"Year {year} was not found.")

def get_segment_capacities_for_year(
    ships,
    deployment_file,
    year,
    start_year=2035,
):
    """
    Calculate, for each ship segment and one selected year:
        - number of ships
        - annual sailing distance capacity
        - annual port-call capacity

    This function also calls total_distance_year() and total_port_calls_year()
    to keep consistency with the already existing code.
    """

    ships_by_segment = get_ship_numbers_for_year(
        deployment_file,
        year,
        start_year=start_year,
    )

    ship_lookup = build_ship_lookup(ships)

    total_distances = total_distance_year(
        ships,
        deployment_file,
        False,
        start_year,
    )

    total_portcalls = total_port_calls_year(
        ships,
        deployment_file,
        False,
        start_year,
    )

    fleet_distance_km = find_value_for_year(
        total_distances,
        year,
        ["total_distance_km"],
    )

    fleet_portcalls = find_value_for_year(
        total_portcalls,
        year,
        ["total_portcalls", "total_portcal_n"],
    )

    segment_capacities = {}

    for segment_name, number_of_ships in ships_by_segment.items():
        if segment_name not in ship_lookup:
            raise ValueError(
                f"Ship segment '{segment_name}' is present in the deployment file "
                "but was not found in the loaded ship objects."
            )

        ship = ship_lookup[segment_name]

        segment_distance_km = number_of_ships * float(ship.distance)
        segment_portcalls = number_of_ships * float(ship.portcalls)

        segment_capacities[segment_name] = {
            "ship_segment": segment_name,
            "number_of_ships": number_of_ships,
            "distance_capacity_km": segment_distance_km,
            "portcall_capacity": segment_portcalls,
        }

    return segment_capacities, fleet_distance_km, fleet_portcalls

def route_is_available_for_segment(route, segment_name, year):
    """
    Decide whether a route can be used by a ship segment in a given year.
    """

    if route["proposed_operation_year"] > year:
        return False

    if route["start_port_available_from_year"] > year:
        return False

    if route["end_port_available_from_year"] > year:
        return False

    if segment_name not in route["ship_segments"]:
        return False

    return True

def allocate_routes_for_segment(
    segment_name,
    segment_capacity,
    routes,
    year,
    previous_route_ids=None,
):
    """
    Allocate route travels for one ship segment in one year.

    Interpretation:
        One route travel means one bidirectional route service.
        It consumes:
            - 2 port calls
            - 2 * one-way route distance

    This is consistent with the assumption that one go-return service
    involves two port calls.
    """

    distance_capacity_km = segment_capacity["distance_capacity_km"]
    portcall_capacity = segment_capacity["portcall_capacity"]

    if segment_capacity["number_of_ships"] <= 0:
        return [], {
            "ship_segment": segment_name,
            "target_distance_km": 0.0,
            "allocated_distance_km": 0.0,
            "distance_difference_km": 0.0,
            "target_portcalls": 0.0,
            "allocated_portcalls": 0.0,
            "portcall_difference": 0.0,
        }

    candidate_routes = []

    for route in routes:
        if route_is_available_for_segment(route, segment_name, year):
            candidate_routes.append(route)

    if not candidate_routes:
        print(
            f"No available routes for {segment_name} in {year}."
        )

        return [], {
            "ship_segment": segment_name,
            "target_distance_km": distance_capacity_km,
            "allocated_distance_km": 0.0,
            "distance_difference_km": distance_capacity_km,
            "target_portcalls": portcall_capacity,
            "allocated_portcalls": 0.0,
            "portcall_difference": portcall_capacity,
        }

    # One route travel consumes 2 port calls.
    number_of_route_travels = int(round(portcall_capacity / 2.0))

    if number_of_route_travels <= 0:
        return [], {
            "ship_segment": segment_name,
            "target_distance_km": distance_capacity_km,
            "allocated_distance_km": 0.0,
            "distance_difference_km": distance_capacity_km,
            "target_portcalls": portcall_capacity,
            "allocated_portcalls": 0.0,
            "portcall_difference": portcall_capacity,
        }

    route_counts = {}

    for i in range(len(candidate_routes)):
        route_counts[i] = 0

    remaining_distance_km = distance_capacity_km
    remaining_route_travels = number_of_route_travels

    if previous_route_ids is None:
        previous_route_ids = set()

    # Keep previously selected routes active, if they are still available.
    previous_candidate_indices = []

    for i, route in enumerate(candidate_routes):
        if route["route_id"] in previous_route_ids:
            previous_candidate_indices.append(i)

    # If there are more previous routes than available route travels,
    # keep the highest-preference previous routes first.
    previous_candidate_indices.sort(
        key=lambda i: candidate_routes[i]["route_preference_score"],
        reverse=True,
    )

    for i in previous_candidate_indices:
        if remaining_route_travels <= 0:
            break

        route = candidate_routes[i]
        distance_per_travel_km = 2.0 * route["distance_km_estimate"]

        route_counts[i] += 1
        remaining_distance_km -= distance_per_travel_km
        remaining_route_travels -= 1

    while remaining_route_travels > 0:
        target_distance_per_travel = (
            remaining_distance_km / remaining_route_travels
        )

        best_route_index = None
        best_score = None

        for i, route in enumerate(candidate_routes):
            one_way_distance_km = route["distance_km_estimate"]

            distance_per_travel_km = 2.0 * one_way_distance_km
            distance_error = abs(
                distance_per_travel_km - target_distance_per_travel
            )

            distance_penalty = distance_error / max(
                target_distance_per_travel,
                1.0,
            )

            preference_score = route["route_preference_score"] / 100.0

            score = (
                2.0 * preference_score
                - distance_penalty
            )

            if best_score is None or score > best_score:
                best_score = score
                best_route_index = i

        selected_route = candidate_routes[best_route_index]
        selected_distance_km = 2.0 * selected_route["distance_km_estimate"]

        route_counts[best_route_index] += 1
        remaining_distance_km -= selected_distance_km
        remaining_route_travels -= 1

    allocation_rows = []

    allocated_distance_km = 0.0
    allocated_portcalls = 0.0

    for i, route_travels in route_counts.items():
        if route_travels == 0:
            continue

        route = candidate_routes[i]

        one_way_distance_km = route["distance_km_estimate"]
        distance_per_travel_km = 2.0 * one_way_distance_km

        route_distance_total_km = route_travels * distance_per_travel_km
        route_portcalls_total = route_travels * 2.0

        allocated_distance_km += route_distance_total_km
        allocated_portcalls += route_portcalls_total

        allocation_rows.append(
            {
                "year": year,
                "ship_segment": segment_name,
                "route_id": route["route_id"],
                "start_port": route["start_port"],
                "start_iso3": route["start_iso3"],
                "end_port": route["end_port"],
                "end_iso3": route["end_iso3"],
                "route_type": route["route_type"],
                "route_preference_score": route["route_preference_score"],
                "one_way_distance_km": one_way_distance_km,
                "distance_per_route_travel_km": distance_per_travel_km,
                "route_travels": route_travels,
                "allocated_distance_km": route_distance_total_km,
                "allocated_portcalls": route_portcalls_total,
            }
        )

    summary = {
        "ship_segment": segment_name,
        "target_distance_km": distance_capacity_km,
        "allocated_distance_km": allocated_distance_km,
        "distance_difference_km": distance_capacity_km - allocated_distance_km,
        "target_portcalls": portcall_capacity,
        "allocated_portcalls": allocated_portcalls,
        "portcall_difference": portcall_capacity - allocated_portcalls,
    }

    return allocation_rows, summary

def normalize_port_key(port_name, iso3):
    """
    Create a matching key for a port using port name and iso3.
    """

    text = str(port_name).strip().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = text.strip()

    iso3 = str(iso3).strip()

    return iso3, text

def build_active_port_lookup(countries, year):
    """
    Build a dictionary:
        (iso3, normalized port name) -> port dictionary

    This is needed to recover coordinates for plotting.
    """

    active_ports = get_operating_ports(countries, year)

    port_lookup = {}

    for port in active_ports:
        key = normalize_port_key(
            port["port_name"],
            port["iso3"],
        )

        port_lookup[key] = port

    return port_lookup

def get_route_ports_from_lookup(route_row, port_lookup):
    """
    Recover the start and end port dictionaries for one route allocation row.
    """

    start_key = normalize_port_key(
        route_row["start_port"],
        route_row["start_iso3"],
    )

    end_key = normalize_port_key(
        route_row["end_port"],
        route_row["end_iso3"],
    )

    if start_key not in port_lookup:
        raise ValueError(
            f"Start port not found: "
            f"{route_row['start_port']} ({route_row['start_iso3']})"
        )

    if end_key not in port_lookup:
        raise ValueError(
            f"End port not found: "
            f"{route_row['end_port']} ({route_row['end_iso3']})"
        )

    return port_lookup[start_key], port_lookup[end_key]

def plot_routes_for_segment_year(
    allocation_rows,
    countries,
    year,
    segment_name,
    output_dir=OUTPUT_ROUTE_DIR,
):
    """
    Plot all routes used by one ship segment in one selected year.
    """
    segment_rows = []

    for row in allocation_rows:
        if row["ship_segment"] == segment_name and row["route_travels"] > 0:
            segment_rows.append(row)

    if not segment_rows:
        print(f"No routes to plot for {segment_name} in {year}.")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    port_lookup = build_active_port_lookup(countries, year)

    img = mpimg.imread(MAP_IMAGE)

    fig, ax = plt.subplots(figsize=(16, 8))

    ax.imshow(
        img,
        extent=[-180, 180, -90, 90],
        origin="upper",
        zorder=0,
    )

    max_route_travels = max(
        row["route_travels"]
        for row in segment_rows
    )

    plotted_ports = {}

    for row in segment_rows:
        port_a, port_b = get_route_ports_from_lookup(row, port_lookup)

        distance_km, coordinates = route_distance_model(
            port_a,
            port_b,
            row["route_type"],
        )

        for route_segment in split_route_at_dateline(coordinates):
            lons = [point[0] for point in route_segment]
            lats = [point[1] for point in route_segment]

            ax.plot(
                lons,
                lats,
                linewidth=1.6,
                alpha=0.65,
                zorder=3,
            )

        plotted_ports[
            (
                port_a["port_name"],
                port_a["longitude"],
                port_a["latitude"],
            )
        ] = port_a

        plotted_ports[
            (
                port_b["port_name"],
                port_b["longitude"],
                port_b["latitude"],
            )
        ] = port_b

    for port in plotted_ports.values():
        ax.scatter(
            port["longitude"],
            port["latitude"],
            s=55,
            edgecolor="black",
            linewidth=0.6,
            zorder=5,
        )

        ax.text(
            port["longitude"] + 1.2,
            port["latitude"] + 0.8,
            port["port_name"],
            fontsize=7,
            zorder=6,
        )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(
        f"{segment_name.replace('_', ' ')} routes in {year}"
    )

    output_file = (
        output_dir
        / f"routes_{safe_filename(segment_name)}_{year}.pdf"
    )

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()

    print(f"Route map saved to: {output_file}")

    return output_file

def write_table(rows, output_file, fieldnames):
    """
    Write a list of dictionaries to a semicolon-separated table file.
    """

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            delimiter=";",
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Table saved to: {output_file}")

def plot_all_routes_for_year(
    allocation_rows,
    countries,
    year,
    output_dir=OUTPUT_MAP_DIR,
):
    """
    Plot all active routes for all ship segments in one selected year.

    If the same route is used by several ship segments, the route is plotted
    only once, and the linewidth is proportional to the total number of
    route travels across all segments.
    """

    year_rows = []

    for row in allocation_rows:
        if row["year"] == year and row["route_travels"] > 0:
            year_rows.append(row)

    if not year_rows:
        print(f"No active routes to plot in {year}.")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)

    # Aggregate repeated routes across ship segments.
    routes_by_id = {}

    for row in year_rows:
        route_id = row["route_id"]

        if route_id not in routes_by_id:
            routes_by_id[route_id] = {
                "year": row["year"],
                "route_id": row["route_id"],
                "start_port": row["start_port"],
                "start_iso3": row["start_iso3"],
                "end_port": row["end_port"],
                "end_iso3": row["end_iso3"],
                "route_type": row["route_type"],
                "total_route_travels": 0.0,
                "ship_segments": set(),
            }

        routes_by_id[route_id]["total_route_travels"] += row["route_travels"]
        routes_by_id[route_id]["ship_segments"].add(row["ship_segment"])

    aggregated_routes = list(routes_by_id.values())

    port_lookup = build_active_port_lookup(countries, year)

    img = mpimg.imread(MAP_IMAGE)

    fig, ax = plt.subplots(figsize=(16, 8))

    ax.imshow(
        img,
        extent=[-180, 180, -90, 90],
        origin="upper",
        zorder=0,
    )

    max_route_travels = max(
        row["total_route_travels"]
        for row in aggregated_routes
    )

    plotted_ports = {}

    for row in aggregated_routes:
        port_a, port_b = get_route_ports_from_lookup(row, port_lookup)

        distance_km, coordinates = route_distance_model(
            port_a,
            port_b,
            row["route_type"],
        )

        for route_segment in split_route_at_dateline(coordinates):
            lons = [point[0] for point in route_segment]
            lats = [point[1] for point in route_segment]

            ax.plot(
                lons,
                lats,
                linewidth=1.6,
                alpha=0.65,
                zorder=3,
            )

        plotted_ports[
            (
                port_a["port_name"],
                port_a["longitude"],
                port_a["latitude"],
            )
        ] = port_a

        plotted_ports[
            (
                port_b["port_name"],
                port_b["longitude"],
                port_b["latitude"],
            )
        ] = port_b

    for port in plotted_ports.values():
        ax.scatter(
            port["longitude"],
            port["latitude"],
            s=55,
            edgecolor="black",
            linewidth=0.6,
            zorder=5,
        )

        ax.text(
            port["longitude"] + 1.2,
            port["latitude"] + 0.8,
            port["port_name"],
            fontsize=7,
            zorder=6,
        )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"All active routes in {year}")

    output_file = output_dir / f"routes_all_segments_{year}.pdf"

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()

    print(f"All-segment route map saved to: {output_file}")

    return output_file

def build_route_network_over_time(
    ships,
    countries,
    deployment_file="outputs/deployment_baseline.txt",
    route_file=ROUTE_CONNECTION_FILE,
    start_year=2035,
    end_year=2060,
    plot_years=None,
    plot_segments=None,
    plot_all_route_years=None,
    summary_output_file=ROUTE_SUMMARY_TABLE,
    route_output_file=ROUTE_ALLOCATION_TABLE,
):
    """
    Build the route network consecutively from start_year to end_year.

    Once a route is selected for a ship segment, it is kept active
    in all following years, as long as the segment still has capacity.

    This function writes:
        1. a summary table by year and ship segment
        2. a route-allocation table by year, segment and route
    """

    routes = load_port_connection_proposals(route_file)

    if not all(hasattr(ship, "distance") for ship in ships):
        ships = add_distance_to_ships(ships)

    selected_route_ids_by_segment = {}

    all_network_rows = []
    all_summaries = []
    summary_table_rows = []

    if plot_years is None:
        plot_years = []

    if plot_all_route_years is None:
        plot_all_route_years = []

    if plot_segments is not None:
        plot_segments = set(plot_segments)

    for year in range(start_year, end_year + 1):

        segment_capacities, fleet_distance_km, fleet_portcalls = (
            get_segment_capacities_for_year(
                ships,
                deployment_file,
                year,
                start_year=start_year,
            )
        )

        year_network_rows = []
        year_summaries = []

        for segment_name, segment_capacity in segment_capacities.items():

            previous_route_ids = selected_route_ids_by_segment.get(
                segment_name,
                set(),
            )

            allocation_rows, summary = allocate_routes_for_segment(
                segment_name,
                segment_capacity,
                routes,
                year,
                previous_route_ids=previous_route_ids,
            )

            year_network_rows.extend(allocation_rows)

            summary["year"] = year
            year_summaries.append(summary)

            # Update persistent route set for this segment.
            current_route_ids = set()

            for row in allocation_rows:
                if row["route_travels"] > 0:
                    current_route_ids.add(row["route_id"])

            selected_route_ids_by_segment[segment_name] = (
                previous_route_ids | current_route_ids
            )

        # Store yearly summary information instead of printing it.
        for summary in year_summaries:
            summary_table_rows.append(
                {
                    "year": year,
                    "fleet_distance_capacity_km": fleet_distance_km,
                    "fleet_portcall_capacity": fleet_portcalls,
                    "ship_segment": summary["ship_segment"],
                    "target_distance_km": summary["target_distance_km"],
                    "allocated_distance_km": summary["allocated_distance_km"],
                    "distance_difference_km": summary["distance_difference_km"],
                    "target_portcalls": summary["target_portcalls"],
                    "allocated_portcalls": summary["allocated_portcalls"],
                    "portcall_difference": summary["portcall_difference"],
                }
            )

        if year in plot_years:
            for segment_name in segment_capacities.keys():

                if plot_segments is not None and segment_name not in plot_segments:
                    continue

                plot_routes_for_segment_year(
                    year_network_rows,
                    countries,
                    year,
                    segment_name,
                )

        if year in plot_all_route_years:
            plot_all_routes_for_year(
                year_network_rows,
                countries,
                year,
            )

        all_network_rows.extend(year_network_rows)
        all_summaries.extend(year_summaries)

    summary_fieldnames = [
        "year",
        "fleet_distance_capacity_km",
        "fleet_portcall_capacity",
        "ship_segment",
        "target_distance_km",
        "allocated_distance_km",
        "distance_difference_km",
        "target_portcalls",
        "allocated_portcalls",
        "portcall_difference",
    ]

    route_fieldnames = [
        "year",
        "ship_segment",
        "route_id",
        "start_port",
        "start_iso3",
        "end_port",
        "end_iso3",
        "route_type",
        "route_preference_score",
        "one_way_distance_km",
        "distance_per_route_travel_km",
        "route_travels",
        "allocated_distance_km",
        "allocated_portcalls",
    ]

    write_table(
        summary_table_rows,
        summary_output_file,
        summary_fieldnames,
    )

    write_table(
        all_network_rows,
        route_output_file,
        route_fieldnames,
    )

    return all_network_rows, all_summaries

def main():

    countries = load_all_countries()
    ships = load_ship_segments()
    ships = add_distance_to_ships(ships)

    network_rows, summaries = build_route_network_over_time(
        ships=ships,
        countries=countries,
        deployment_file="outputs/deployment_baseline.txt",
        route_file="inputs/port_connection_proposals2.txt",
        start_year=2035,
        end_year=2060,
        plot_years=[2035, 2040, 2045, 2050, 2055, 2060],
        plot_segments=["Bulk_carrier","Panamax_container","Large_container","Ultra_large_container",
                       "Offshore_vessel","Oil_tanker Medium_Icebreaker","Large_Icebreaker",
                       "Fishing_vessels","Large_cruise Passenger_ferry"],
        plot_all_route_years=[2035, 2040, 2045, 2050, 2055, 2060],
        summary_output_file=ROUTE_SUMMARY_TABLE,
        route_output_file=ROUTE_ALLOCATION_TABLE,
    )

if __name__ == "__main__":
    main()