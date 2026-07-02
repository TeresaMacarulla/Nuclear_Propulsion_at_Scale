import glob
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.colors as mcolors
from utilities import init_country_from_file


COUNTRY_INPUT_DIR = Path("inputs") / "country"
OUTPUT_DIR = Path("outputs") / "maps"
MAP_IMAGE = Path("outputs") / "maps" / "world_map_equirectangular.jpg"


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
                        "latitude": lat,
                        "longitude": lon,
                        "start_year": start_year,
                    }
                )

    return active_ports

def plot_world_map_with_ports(active_ports, year, show_port_names=False):
    """
    Plot active operating ports for the selected year on an equirectangular
    world map image.

    The map image must be stored at:
        outputs/maps/world_map_equirectangular.jpg

    The image must be equirectangular, meaning:
        longitude: -180 to 180
        latitude:  -90 to 90
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not MAP_IMAGE.exists():
        raise FileNotFoundError(
            f"Map image not found: {MAP_IMAGE}\n"
            "Make sure the file is stored inside outputs/maps/ "
            "and named world_map_equirectangular.jpg"
        )

    # Read background map image
    img = mpimg.imread(MAP_IMAGE)

    fig, ax = plt.subplots(figsize=(16, 8))

    # Plot the map as a geographic background
    ax.imshow(
        img,
        extent=[-180, 180, -90, 90],
        origin="upper",
        zorder=0,
    )

    # Extract active port data
    longitudes = [port["longitude"] for port in active_ports]
    latitudes = [port["latitude"] for port in active_ports]
    start_years = [port["start_year"] for port in active_ports]

    # Colour scale:
    # green = earlier activation, red = later activation
    cmap = plt.cm.RdYlGn_r
    norm = mcolors.Normalize(vmin=2030, vmax=2052)

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

    # Optional labels
    if show_port_names:
        for port in active_ports:
            ax.text(
                port["longitude"] + 1.5,
                port["latitude"] + 1.0,
                port["port_name"],
                fontsize=7,
                zorder=6,
            )

    # Map limits
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.set_title(
        f"Operating ports in the fleet route network in {year}",
        fontsize=16,
        pad=15,
    )

    # Colour bar
    cbar = plt.colorbar(
        scatter,
        ax=ax,
        orientation="horizontal",
        fraction=0.045,
        pad=0.08,
    )
    cbar.set_label("Port activation year")

    cbar.set_ticks([2034, 2036, 2038, 2040, 2042, 2044, 2046, 2048, 2050, 2052, 2054, 2056, 2058, 2060])

    output_file = OUTPUT_DIR / f"operating_ports_{year}.png"

    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.show()

    print(f"\nMap saved to: {output_file}")


def main():
    countries = load_all_countries()

    year = int(input("Enter year to plot operating ports: "))

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

    plot_world_map_with_ports(active_ports, year)


if __name__ == "__main__":
    main()