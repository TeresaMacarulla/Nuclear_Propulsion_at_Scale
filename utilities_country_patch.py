from country import Country

def str_to_bool(value):
    """Convert txt-file boolean fields to Python booleans.

    Accepted true values: 1, true, yes, y.
    Everything else is interpreted as False.
    """
    return str(value).strip().lower() in ("1", "true", "yes", "y")

def init_country_from_file(filename):
    file = np.loadtxt(filename, delimiter=';', dtype=str)
    row = file[1, :]

    return Country(
        name=row[0],
        iso3=row[1],
        region=row[2],
        nuclear_port_capable=str_to_bool(row[3]),
        nuclear_port_count=int(float(row[4])),
        route_relevance=str_to_bool(row[5]),
        uranium_mining=str_to_bool(row[6]),
        uranium_conversion=str_to_bool(row[7]),
        enrichment=str_to_bool(row[8]),
        fuel_fabrication=str_to_bool(row[9]),
        reactor_fabrication=str_to_bool(row[10]),
        waste_management=str_to_bool(row[11]),
        uranium_production_tU_per_year=float(row[12]),
        conversion_capacity_tU_per_year=float(row[13]),
        enrichment_capacity_SWU_per_year=float(row[14]),
        fuel_fabrication_capacity_tHM_per_year=float(row[15]),
        reactor_fabrication_capacity_units_per_year=float(row[16]),
        notes=row[17] if len(row) > 17 else "",
    )
