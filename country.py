class Country:
    """Country-level input class for maritime routes and nuclear supply-chain modelling.

    Boolean variables are scenario flags. Capacity variables are numerical inputs
    that can be set to zero when the country is not considered active in that
    part of the supply chain or when the capacity is unknown.
    """

    def __init__(
        self,
        name, # Country name, e.g. "France", "Norway", "Canada"
        iso3, # Three-letter ISO country code, e.g. "FRA", "NOR", "CAN"
        region, # Broad geographical region, e.g. "Europe", "North America", "Asia"
        nuclear_port_capable, # Boolean flag: True if the country has ports that could potentially handle nuclear-powered ships
        nuclear_port_count, # Number of candidate ports in the country that could be relevant for nuclear-ship deployment
        route_relevance,  # Boolean flag: True if the country is relevant for the assumed shipping routes, even if it is not part of the fuel supply chain
        uranium_mining, # Boolean flag: True if the country is considered a uranium mining or milling country
        uranium_conversion, # Boolean flag: True if the country has uranium conversion capacity, U3O8 to UF6
        enrichment, # Boolean flag: True if the country has uranium enrichment capacity
        fuel_fabrication, # Boolean flag: True if the country has nuclear fuel fabrication capacity or is considered a candidate for it
        reactor_fabrication, # Boolean flag: True if the country has reactor/module manufacturing capacity or is considered a candidate for it
        waste_management, # Boolean flag: True if the country is considered relevant for spent-fuel or radioactive-waste management
        uranium_production_tU_per_year, # Annual uranium mine production, expressed as tonnes of contained uranium per year [tU/year]
        conversion_capacity_tU_per_year, # Annual uranium conversion capacity, expressed as tonnes of uranium per year [tU/year]
        enrichment_capacity_SWU_per_year, # Annual enrichment capacity, expressed in separative work units per year [SWU/year]
        fuel_fabrication_capacity_tHM_per_year, # Annual nuclear fuel fabrication capacity, expressed as tonnes of heavy metal per year [tHM/year]
        reactor_fabrication_capacity_units_per_year, # Annual reactor/module fabrication capacity, expressed as reactor units or modules per year
        notes="", # Optional free-text notes, assumptions, references, or comments about the country
    ):
        self.countryname = name
        self.iso3 = iso3
        self.region = region

        # Maritime / route role
        self.nuclear_port_capable = nuclear_port_capable
        self.nuclear_port_count = nuclear_port_count
        self.route_relevance = route_relevance

        # Supply-chain role
        self.uranium_mining = uranium_mining
        self.uranium_conversion = uranium_conversion
        self.enrichment_capacity = enrichment
        self.fuel_fabrication = fuel_fabrication
        self.reactor_fabrication = reactor_fabrication
        self.waste_management = waste_management

        # Supply-chain capacities
        self.uranium_production_tU_per_year = uranium_production_tU_per_year
        self.conversion_capacity_tU_per_year = conversion_capacity_tU_per_year
        self.enrichment_capacity_SWU_per_year = enrichment_capacity_SWU_per_year
        self.fuel_fabrication_capacity_tHM_per_year = fuel_fabrication_capacity_tHM_per_year
        self.reactor_fabrication_capacity_units_per_year = reactor_fabrication_capacity_units_per_year

        self.notes = notes

    def __str__(self):
        return (
            f"=== {self.country_name} ({self.iso3}) country characteristics ===\n"
            f"Region: {self.region}\n"
            f"Nuclear-port capable: {self.nuclear_port_capable}\n"
            f"Number of candidate nuclear ports: {self.nuclear_port_count}\n"
            f"Relevant for ship routes: {self.route_relevance}\n"
            f"Uranium mining: {self.uranium_mining}\n"
            f"Uranium conversion: {self.uranium_conversion}\n"
            f"Enrichment: {self.enrichment_capacity}\n"
            f"Fuel fabrication: {self.fuel_fabrication}\n"
            f"Reactor fabrication: {self.reactor_fabrication}\n"
            f"Waste management: {self.waste_management}\n"
            f"Uranium production: {self.uranium_production_tU_per_year} tU/year\n"
            f"Conversion capacity: {self.conversion_capacity_tU_per_year} tU/year\n"
            f"Enrichment capacity: {self.enrichment_capacity_SWU_per_year} SWU/year\n"
            f"Fuel fabrication capacity: {self.fuel_fabrication_capacity_tHM_per_year} tHM/year\n"
            f"Reactor fabrication capacity: {self.reactor_fabrication_capacity_units_per_year} units/year\n"
            f"Notes: {self.notes}\n"
        )
