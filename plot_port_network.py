import glob
import csv
import json
import math
import re
import unicodedata
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.colors as mcolors
from utilities import init_country_from_file


COUNTRY_INPUT_DIR = Path("inputs") / "country"
OUTPUT_DIR = Path("outputs") / "maps"
ROUTE_OUTPUT_DIR = Path("outputs") / "routes"
ROUTE_CACHE_DIR = ROUTE_OUTPUT_DIR / "cache"
MAP_IMAGE = Path("outputs") / "maps" / "world_map_equirectangular.jpg"

YEAR_MIN = 2030
YEAR_MAX = 2060

EUROPE_COUNTRIES = {
    "netherlands",
    "belgium",
    "germany",
    "spain",
    "france",
    "poland",
    "italy",
    "romania",
    "norway",
}

AMERICA_COUNTRIES = {
    "united states",
    "brazil",
}

MIDDLE_EAST_COUNTRIES = {
    "united arab emirates",
}

AUSTRALIA_COUNTRIES = {
    "australia",
}

RUSSIA_COUNTRIES = {
    "russia",
}

# Preferred gateway port for each European country.
# Only one active port per European country is selected for long-distance routes.
EUROPEAN_GATEWAY_PREFERENCES = {
    "netherlands": ["rotterdam", "amsterdam"],
    "belgium": ["antwerp bruges", "north sea"],
    "germany": ["hamburg", "bremen bremerhaven", "niedersachsen"],
    "spain": ["algeciras", "valencia", "barcelona"],
    "france": ["le havre rouen paris", "marseille fos"],
    "poland": ["gdansk"],
    "italy": ["genoa", "trieste"],
    "romania": ["constanta"],
    "norway": ["bergen", "kirkenes", "tromso"],
}

def ensure_list(value):
    """Ensure that a scalar value is treated as a list."""
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]

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

def normalize_port_name(name):
    """Normalize text for robust comparison."""
    text = str(text).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.replace("port of ", "")
    text = text.replace("ports of ", "")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return text.strip()

def safe_filename(text):
    """Create a safe filename from a text string."""
    text = normalize_port_name(text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")

def is_same_country_connection_allowed(port_a, port_b):
    """
    Decide if a connection between two ports in the same country is allowed.

    General rule:
        - Do not connect ports in the same country.

    Exception:
        - Russia:
            Provideniya -- Murmansk
            Provideniya -- Arkhangelsk

        - Do not connect Arkhangelsk -- Murmansk.
    """
    country_a = str(port_a["country"]).strip().lower()
    country_b = str(port_b["country"]).strip().lower()

    if country_a != country_b:
        return True

    if country_a != "russia":
        return False

    name_a = normalize_port_name(port_a["port_name"])
    name_b = normalize_port_name(port_b["port_name"])
    pair = {name_a, name_b}

    allowed_russian_pairs = [
        {"provideniya", "murmansk"},
        {"provideniya", "arkhangelsk"},
    ]

    return pair in allowed_russian_pairs

def normalize_longitude(lon):
    """Normalize longitude to the range [-180, 180]."""
    return ((float(lon) + 180.0) % 360.0) - 180.0

def haversine_km(lon1, lat1, lon2, lat2):
    """Great-circle distance between two lon/lat points in km."""
    radius_earth_km = 6371.0

    lon1 = math.radians(float(lon1))
    lat1 = math.radians(float(lat1))
    lon2 = math.radians(float(lon2))
    lat2 = math.radians(float(lat2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    )

    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return radius_earth_km * c

def route_length_from_coordinates(coordinates):
    """Calculate route length from route polyline coordinates."""
    total = 0.0

    for p1, p2 in zip(coordinates[:-1], coordinates[1:]):
        lon1, lat1 = p1
        lon2, lat2 = p2
        total += haversine_km(lon1, lat1, lon2, lat2)

    return total

def route_cache_file(port_a, port_b):
    """Return a stable cache file path for one route."""
    a = f"{port_a['country']}_{port_a['port_name']}"
    b = f"{port_b['country']}_{port_b['port_name']}"

    names = sorted([safe_filename(a), safe_filename(b)])
    filename = f"{names[0]}__{names[1]}.json"

    return ROUTE_CACHE_DIR / filename

def compute_sea_route(port_a, port_b):
    """
    Compute a sea route between two ports using the searoute package.

    The searoute package returns a route that follows maritime paths and avoids
    land. The result is cached to avoid recomputing the same route every time.
    """

    ROUTE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = route_cache_file(port_a, port_b)

    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)

    try:
        import searoute as sr
    except ImportError as exc:
        raise ImportError(
            "The package 'searoute' is required to compute sea routes.\n"
            "Install it with:\n\n"
            "    pip install searoute\n"
        ) from exc

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

    if distance_km is None:
        distance_km = route_length_from_coordinates(coordinates)

    route = {
        "from_port": port_a["port_name"],
        "from_country": port_a["country"],
        "to_port": port_b["port_name"],
        "to_country": port_b["country"],
        "activation_year": max(port_a["start_year"], port_b["start_year"]),
        "distance_km": float(distance_km),
        "coordinates": coordinates,
    }

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(route, f, indent=2)

    return route

def country_key(port):
    """Return normalized country name."""
    return normalize_port_name(port["country"])

def port_key(port):
    """Unique comparable identifier for a port."""
    return (
        normalize_port_name(port["country"]),
        normalize_port_name(port["port_name"]),
    )

def is_european_port(port):
    return country_key(port) in EUROPE_COUNTRIES

def is_american_port(port):
    return country_key(port) in AMERICA_COUNTRIES

def is_middle_east_port(port):
    return country_key(port) in MIDDLE_EAST_COUNTRIES

def is_australian_port(port):
    return country_key(port) in AUSTRALIA_COUNTRIES

def is_russian_port(port):
    return country_key(port) in RUSSIA_COUNTRIES

def get_port_by_name(active_ports, port_name, country=None):
    """Find an active port by name, optionally restricted by country."""
    target_name = normalize_port_name(port_name)
    target_country = normalize_port_name(country) if country is not None else None

    for port in active_ports:
        if normalize_port_name(port["port_name"]) != target_name:
            continue

        if target_country is not None and country_key(port) != target_country:
            continue

        return port

    return None

def select_gateway_port_for_country(country_ports):
    """
    Select one gateway port for a country.

    Preference:
    1. Use manually defined preferred gateway ports.
    2. If none are active, use the earliest activated port.
    """

    if not country_ports:
        return None

    country = country_key(country_ports[0])
    preferences = EUROPEAN_GATEWAY_PREFERENCES.get(country, [])

    for preferred_name in preferences:
        for port in country_ports:
            if normalize_port_name(port["port_name"]) == preferred_name:
                return port

    return min(country_ports, key=lambda p: p["start_year"])

def select_european_gateway_ports(active_ports):
    """
    Select one active gateway port per European country.
    """

    ports_by_country = {}

    for port in active_ports:
        if not is_european_port(port):
            continue

        ports_by_country.setdefault(country_key(port), []).append(port)

    gateway_ports = []

    for country_ports in ports_by_country.values():
        gateway = select_gateway_port_for_country(country_ports)

        if gateway is not None:
            gateway_ports.append(gateway)

    return gateway_ports

def add_route_pair(route_pairs, port_a, port_b, allow_same_country=False):
    """
    Add a route pair if it is not duplicated and if same-country rules allow it.

    By default, same-country routes are blocked.
    However, explicit scenario rules can override this using allow_same_country=True.
    """

    if port_a is None or port_b is None:
        return

    if port_key(port_a) == port_key(port_b):
        return

    if not allow_same_country:
        if not is_same_country_connection_allowed(port_a, port_b):
            return

    key = tuple(sorted([port_key(port_a), port_key(port_b)]))

    if key not in route_pairs:
        route_pairs[key] = (port_a, port_b)

def build_scenario_route_pairs(active_ports):
    """
    Build route pairs according to scenario rules.

    Current rules:
    1. One gateway port from each active European country connects to each active American port.
    2. One gateway port from each active European country connects to each active Middle East port.
    3. One gateway port from each active European country connects to each active Australian port.
    4. Russian icebreaker-specific routes:
       Provideniya--Murmansk and Provideniya--Arkhangelsk.
    """

    route_pairs = {}

    european_gateways = select_european_gateway_ports(active_ports)

    american_ports = [port for port in active_ports if is_american_port(port)]
    middle_east_ports = [port for port in active_ports if is_middle_east_port(port)]
    australian_ports = [port for port in active_ports if is_australian_port(port)]

    # Rule 1: Europe -> America
    for european_port in european_gateways:
        for american_port in american_ports:
            add_route_pair(route_pairs, european_port, american_port)

    # Rule 2: Europe -> Middle East
    for european_port in european_gateways:
        for middle_east_port in middle_east_ports:
            add_route_pair(route_pairs, european_port, middle_east_port)

    # Rule 3: Europe -> Australia
    for european_port in european_gateways:
        for australian_port in australian_ports:
            add_route_pair(route_pairs, european_port, australian_port)

    # Rule 4: icebreaker / Northern Sea Route Russian connections
    provideniya = get_port_by_name(active_ports, "Provideniya", country="Russia")
    murmansk = get_port_by_name(active_ports, "Murmansk", country="Russia")
    arkhangelsk = get_port_by_name(active_ports, "Arkhangelsk", country="Russia")

    add_route_pair(route_pairs, provideniya, murmansk, allow_same_country=True)
    add_route_pair(route_pairs, provideniya, arkhangelsk, allow_same_country=True)

    return list(route_pairs.values())

def build_operating_routes(active_ports):
    """
    Build scenario-based sea-route connections between active ports.

    This replaces the previous all-to-all connection logic.
    """

    routes = []

    route_pairs = build_scenario_route_pairs(active_ports)

    for port_a, port_b in route_pairs:

        try:
            route = compute_sea_route(port_a, port_b)
            routes.append(route)

        except Exception as exc:
            print(
                f"Warning: could not compute route "
                f"{port_a['port_name']} -> {port_b['port_name']}: {exc}"
            )

    return routes

def total_route_distance_km(routes):
    """Return the sum of all route distances in km."""
    if not routes:
        return 0.0

    return sum(float(route["distance_km"]) for route in routes)

def save_routes_to_csv(routes, year):
    """Save route distances to a CSV file."""

    ROUTE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = ROUTE_OUTPUT_DIR / f"operating_routes_{year}.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")

        writer.writerow(
            [
                "from_port",
                "from_country",
                "to_port",
                "to_country",
                "activation_year",
                "distance_km",
            ]
        )

        for route in routes:
            writer.writerow(
                [
                    route["from_port"],
                    route["from_country"],
                    route["to_port"],
                    route["to_country"],
                    int(route["activation_year"]),
                    round(route["distance_km"], 2),
                ]
            )

        writer.writerow([])
        writer.writerow(
            [
                "TOTAL",
                "",
                "",
                "",
                "",
                round(total_route_distance_km(routes), 2),
            ])

    print(f"Route distance table saved to: {output_file}")

def split_route_at_dateline(coordinates):
    """
    Split a route into segments if it crosses the map edge/dateline.

    This prevents matplotlib from drawing a wrong horizontal line across the map.
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


def plot_port_network(
    active_ports,
    year,
    routes=None,
    plot_routes=False,
    show_port_names=False,
):
    """
    Plot active ports and optionally active sea routes on the world map.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MAP_IMAGE.exists():
        raise FileNotFoundError(
            f"Map image not found: {MAP_IMAGE}\n"
            "Make sure the file is stored inside outputs/maps/ "
            "and named world_map_equirectangular.jpg"
        )

    img = mpimg.imread(MAP_IMAGE)

    fig, ax = plt.subplots(figsize=(16, 8))

    ax.imshow(
        img,
        extent=[-180, 180, -90, 90],
        origin="upper",
        zorder=0,
    )

    if plot_routes and routes:
        for route in routes:
            for segment in split_route_at_dateline(route["coordinates"]):
                lons = [point[0] for point in segment]
                lats = [point[1] for point in segment]

                ax.plot(
                    lons,
                    lats,
                    linewidth=1,
                    alpha=0.35,
                    zorder=3,
                )

    longitudes = [port["longitude"] for port in active_ports]
    latitudes = [port["latitude"] for port in active_ports]
    start_years = [port["start_year"] for port in active_ports]

    cmap = plt.cm.RdYlGn_r
    norm = mcolors.Normalize(vmin=YEAR_MIN, vmax=YEAR_MAX)

    scatter = ax.scatter(
        longitudes,
        latitudes,
        c=start_years,
        cmap=cmap,
        norm=norm,
        s=75,
        edgecolor="black",
        linewidth=0.5,
        zorder=5,
    )

    if show_port_names:
        for port in active_ports:
            ax.text(
                port["longitude"] + 1.5,
                port["latitude"] + 1.0,
                port["port_name"],
                fontsize=7,
                zorder=6,
            )

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    total_km = total_route_distance_km(routes) if plot_routes and routes else 0.0

    if plot_routes:
        title = (
            f"Operating ports and sea routes in the fleet network in {year}\n"
            f"{len(routes)} active routes | Total route distance: {total_km:,.0f} km"
        )
        output_file = OUTPUT_DIR / f"operating_ports_and_routes_{year}.png"
    else:
        title = f"Operating ports in the fleet network in {year}"
        output_file = OUTPUT_DIR / f"operating_ports_{year}.png"

    ax.set_title(title, fontsize=16, pad=15)

    if plot_routes:
        ax.text(
            0.01,
            0.02,
            f"Total route distance: {total_km:,.0f} km\n"
            f"Active routes: {len(routes)}",
            transform=ax.transAxes,
            fontsize=10,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="black"),
            zorder=10,
        )

    cbar = plt.colorbar(
        scatter,
        ax=ax,
        orientation="horizontal",
        fraction=0.045,
        pad=0.08,
    )

    cbar.set_label("Port activation year")
    cbar.set_ticks([2030, 2035, 2040, 2045, 2050, 2055, 2060])

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()

    print(f"\nMap saved to: {output_file}")


def ask_plot_mode():
    """Ask the user whether to plot only ports or ports plus routes."""

    print("\nSelect plot mode:")
    print("1 - Ports only")
    print("2 - Ports + sea routes")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "2":
        return True

    return False


def ask_show_port_names():
    """Ask whether port names should be shown."""

    choice = input("Show port names? [y/N]: ").strip().lower()

    return choice in ("y", "yes")


def main():
    countries = load_all_countries()

    year = int(input("Enter year to plot operating network: "))

    plot_routes = ask_plot_mode()
    show_port_names = ask_show_port_names()

    active_ports = get_operating_ports(countries, year)

    print(f"\nOperating ports in {year}: {len(active_ports)}")

    for port in active_ports:
        print(
            f"- {port['port_name']} "
            f"({port['country']}), "
            f"available from {int(port['start_year'])}"
        )

    if not active_ports:
        print("No operating ports are active in this year.")
        return

    routes = []

    if plot_routes:
        print("\nBuilding sea-route connections. This may take some time...")
        routes = build_operating_routes(active_ports)

        print(f"Operating sea routes in {year}: {len(routes)}")
        print(f"Total route distance in {year}: {total_route_distance_km(routes):,.0f} km")

        save_routes_to_csv(routes, year)

    plot_port_network(
        active_ports=active_ports,
        year=year,
        routes=routes,
        plot_routes=plot_routes,
        show_port_names=show_port_names,
    )


if __name__ == "__main__":
    main()