import glob
from pathlib import Path
import re
import copy
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import searoute as sr
from utilities import init_country_from_file, init_ship_from_file


COUNTRY_INPUT_DIR = Path("inputs") / "country"
SHIP_INPUT_DIR = Path("inputs") / "ship"
OUTPUT_MAP_DIR = Path("outputs") / "maps"
MAP_IMAGE = OUTPUT_MAP_DIR / "world_map_equirectangular.jpg"

# LOADING INPUTS

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

def plot_route_from_coordinates(
    port_a,
    port_b,
    coordinates,
    show_port_names=True,
):
    """
    Plot one sea route between two ports using the coordinates returned by
    route_distance().
    """

    OUTPUT_MAP_DIR.mkdir(parents=True, exist_ok=True)

    img = mpimg.imread(MAP_IMAGE)

    fig, ax = plt.subplots(figsize=(16, 8))

    ax.imshow(
        img,
        extent=[-180, 180, -90, 90],
        origin="upper",
        zorder=0,
    )

    # Plot the sea route using the coordinates from route_distance()
    for segment in split_route_at_dateline(coordinates):
        lons = [point[0] for point in segment]
        lats = [point[1] for point in segment]

        ax.plot(
            lons,
            lats,
            linewidth=1.5,
            alpha=0.75,
            zorder=3,
        )

    # Plot the two ports
    ax.scatter(
        [port_a["longitude"], port_b["longitude"]],
        [port_a["latitude"], port_b["latitude"]],
        s=90,
        edgecolor="black",
        linewidth=0.6,
        zorder=5,
    )

    if show_port_names:
        ax.text(
            port_a["longitude"] + 1.5,
            port_a["latitude"] + 1.0,
            port_a["port_name"],
            fontsize=8,
            zorder=6,
        )

        ax.text(
            port_b["longitude"] + 1.5,
            port_b["latitude"] + 1.0,
            port_b["port_name"],
            fontsize=8,
            zorder=6,
        )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    output_file = (
        OUTPUT_MAP_DIR
        / f"route_{safe_filename(port_a['port_name'])}_to_{safe_filename(port_b['port_name'])}.png"
    )

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()
    print(f"Route map saved to: {output_file}")

# COMPUTE THE FLEET CAPACITY IN KM

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

def total_distance_year(ships, file, plot, start_year=2035, output_file=None):
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

def main():
    countries = load_all_countries()
    ships = load_ship_segments()

    active_ports = get_operating_ports(countries, 2035)
    """
    print(f"\nOperating ports in 2035: {len(active_ports)}")

    port0 = active_ports[0]
    for port in active_ports:
        print(
            f"- {port['port_name']} "
            f"({port['country']}), "
            f"available from {int(port['start_year'])}"
        )
        distance_km, coordinates = route_distance(port0, port)
        plot_route_from_coordinates(
            port_a=port0,
            port_b=port,
            coordinates=coordinates,
            show_port_names=True,
        )
        print (
            f"Distance between {port0['port_name']} and {port['port_name']} is {distance_km} km"
        )
        port0 = port
    """

    ships = add_distance_to_ships(ships)
    for ship in ships:
        print(
            f"- {ship.shipname} - "
            f"distance {int(ship.distance)} km/year - "
        )

    total_distances = total_distance_year(
        ships,
        "outputs/deployment_baseline.txt",True,2035,"outputs/fleet_distance_km.pdf"
        )

    for row in total_distances:
        print(
            f"{row['year']}: "
            f"{row['total_distance_km']:,.0f} km/year"
        )

if __name__ == "__main__":
    main()