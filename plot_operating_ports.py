import glob
from pathlib import Path

import matplotlib.pyplot as plt

from utilities import init_country_from_file


COUNTRY_INPUT_DIR = Path("inputs") / "country"
OUTPUT_DIR = Path("outputs") / "maps"


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


def plot_world_map_with_ports(active_ports, year):
    """Plot active ports on a world map."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(16, 8))

    # Try to use Basemap if available. If not, use a simple lon/lat plot.
    try:
        from mpl_toolkits.basemap import Basemap

        m = Basemap(
            projection="cyl",
            llcrnrlat=-60,
            urcrnrlat=85,
            llcrnrlon=-180,
            urcrnrlon=180,
            resolution="c",
            ax=ax,
        )

        m.drawmapboundary(fill_color="lightblue")
        m.fillcontinents(color="whitesmoke", lake_color="lightblue")
        m.drawcoastlines(linewidth=0.5)
        m.drawcountries(linewidth=0.4)
        m.drawparallels(range(-60, 91, 30), labels=[1, 0, 0, 0], linewidth=0.2)
        m.drawmeridians(range(-180, 181, 60), labels=[0, 0, 0, 1], linewidth=0.2)

        for port in active_ports:
            lon = port["longitude"]
            lat = port["latitude"]
            x, y = m(lon, lat)

            ax.scatter(x, y, s=45, marker="o", zorder=5)
            ax.text(
                x + 2,
                y + 1,
                port["port_name"],
                fontsize=8,
                zorder=6,
            )

    except ImportError:
        # Simple fallback if Basemap is not installed.
        ax.set_xlim(-180, 180)
        ax.set_ylim(-60, 85)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True, linestyle=":", linewidth=0.5)

        for port in active_ports:
            lon = port["longitude"]
            lat = port["latitude"]

            ax.scatter(lon, lat, s=45, marker="o", zorder=5)
            ax.text(
                lon + 2,
                lat + 1,
                port["port_name"],
                fontsize=8,
                zorder=6,
            )

    ax.set_title(
        f"Operating ports in the fleet route network in {year}",
        fontsize=16,
        pad=15,
    )

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