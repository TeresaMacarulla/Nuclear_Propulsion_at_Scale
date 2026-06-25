class Country:
    """Country-level input class for maritime routes and nuclear supply-chain modelling.

    Boolean variables are scenario flags. Capacity variables are numerical inputs
    that can be set to zero when the country is not considered active in that
    part of the supply chain or when the capacity is unknown.
    """

    def __init__(
        self,
        name,
        iso3,
        region,
        nuclear_port_capable,
        nuclear_port_count,
        route_relevance,
        uranium_mining,
        uranium_conversion,
        enrichment,
        fuel_fabrication,
        reactor_fabrication,
        waste_management,
        uranium_production_tU_per_year,
        conversion_capacity_tU_per_year,
        enrichment_capacity_SWU_per_year,
        fuel_fabrication_capacity_tHM_per_year,
        reactor_fabrication_capacity_units_per_year,
        notes="",
    ):
        self.name = name
        self.iso3 = iso3
        self.region = region

        # Maritime / route role
        self.nuclear_port_capable = nuclear_port_capable
        self.nuclear_port_count = nuclear_port_count
        self.route_relevance = route_relevance

        # Supply-chain role
        self.uranium_mining = uranium_mining
        self.uranium_conversion = uranium_conversion
        self.enrichment = enrichment
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
            f"=== {self.name} ({self.iso3}) country characteristics ===\n"
            f"Region: {self.region}\n"
            f"Nuclear-port capable: {self.nuclear_port_capable}\n"
            f"Number of candidate nuclear ports: {self.nuclear_port_count}\n"
            f"Relevant for ship routes: {self.route_relevance}\n"
            f"Uranium mining: {self.uranium_mining}\n"
            f"Uranium conversion: {self.uranium_conversion}\n"
            f"Enrichment: {self.enrichment}\n"
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
