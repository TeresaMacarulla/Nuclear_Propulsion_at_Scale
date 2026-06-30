class FuelNeeds:
    def __init__(self,fuel_throughput,swu,feedmass,pebble_number,waste):
        self.fuel_throughput = fuel_throughput # fuel throughput [tons of enriched uranium]
        self.pebble_number = pebble_number# TRISO pebbles needed = TRISO pebbles out
        self.swu = swu # separative work needed [SWU]
        self.feedmass = feedmass # natural uranium need in [tons]
        self.waste = waste # waste volume [m^3]
class InfrastructureNeeds:
    def __init__(self):
        pass