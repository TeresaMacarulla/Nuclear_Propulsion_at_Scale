class Country:
    """
    """

    def __init__(
        self,
        name, # Country name, e.g. "France", "Norway", "Canada"
        iso3, # Three-letter ISO country code, e.g. "FRA", "NOR", "CAN"
        region, # Broad geographical region, e.g. "Europe", "North America", "Asia"
        oecd_member,   # True if the country is in the OECD
        supply, # True if the country takes part in the supply chain
        step,              # Supply-chain step: "enrichment", "triso_fabrication", "reactor_manufacturing"
        supply_from_year, # Year when the capability is assumed available
        capacity,          # Numerical capacity per year
        capacity_unit,     # e.g. "SWU/year", "t/year", "reactor modules/year"
        operation, # True if the country has relevant ports for the ships operation routes
        available_from_year, # Year when the country ports start taking part in the routes
        ports, # Number of relevant ports
        ports_names, # Names of the relevant ports
        latitude,  # Port latitudes separated by ","
        longitude, # Port longitude separated by ","
    ):
        self.countryname = name
        self.iso3 = iso3
        self.region = region
        self.oecd_member = oecd_member
        self.supply = supply
        self.step = step
        self.supply_from_year = supply_from_year
        self.capacity = capacity
        self.capacity_unit = capacity_unit
        self.operation = operation
        self.available_from_year = available_from_year
        self.ports = ports
        self.ports_names = ports_names
        self.latitude = latitude
        self.longitude = longitude

    def __str__(self):
        return (
            f"=== {self.countryname} ({self.iso3}) country characteristics ===\n"
            f"Region: {self.region}\n"
            f"OECD member: {self.eucd_member}\n"
            f"Taking part in the supply chain: {self.supply}\n"
            f"Step in the supply chain: {self.step}\n"
            f"Taking part in the supply chain from year: {self.supply_from_year}\n"
            f"Production: {self.capacity} {self.capacity_unit}\n"
            f"Taking part in the fleet operation routes: {self.operation}\n"  
            f"Ports available from year: {self.available_from_year}\n"
            f"Number of relevant ports: {self.ports}\n"
            f"Port names: {self.port_names}\n"          
        )
