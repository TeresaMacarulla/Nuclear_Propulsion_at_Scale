class Ship:
    def __init__(self,installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,name):
        self.installed_power = installed_power
        self.propulsion = propulsion
        self.auxiliary = auxiliary
        self.avg_speed = avg_speed
        self.op_time = op_time
        self.portcalls = portcalls
        self.shipname = name
    def __str__(self):
        return (
            f"=== {self.shipname} ship characteristics ===\n"
            f"Installed propulsion power: {self.propulsion} MW\n"
            f"Installed auxiliary power:  {self.auxiliary} MW\n"
            f"Average speed:  {self.avg_speed} knots\n"
            f"Operational time:    {self.op_time} hours\n"
            f"Number of portcalls per year:  {self.portcalls}\n"
        )    
from reactor import Reactor   
from country import Country
import math

class PoweredShip(Ship,Reactor,Country):
    def __init__(self,
                 installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname, # Ship parameters
                 power,burnup,enrichment,reactorname, # Reactor parameters
                 countryname,iso3,region,nuclear_port_capable,nuclear_port_count,route_relevance, # Country parameters
                 uranium_mining,uranium_conversion,enrichment_capacity,fuel_fabrication, # Country parameters
                 reactor_fabrication,waste_management,uranium_production_tU_per_year, # Country parameters
                 conversion_capacity_tU_per_year,enrichment_capacity_SWU_per_year, # Country parameters
                 fuel_fabrication_capacity_tHM_per_year, reactor_fabrication_capacity_units_per_year,notes, # Country parameters
                 number = 1 # PoweredShip parameters
                 ):
        # Run initialisers from parent classes
        Ship.__init__(self,installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname) 
        Reactor.__init__(self,power,burnup,enrichment,reactorname)
        Country.__init__(self,countryname,iso3,region,nuclear_port_capable,nuclear_port_count,route_relevance,
                         uranium_mining,uranium_conversion,enrichment_capacity,fuel_fabrication,reactor_fabrication,
                         waste_management,uranium_production_tU_per_year,conversion_capacity_tU_per_year,enrichment_capacity_SWU_per_year,
                         fuel_fabrication_capacity_tHM_per_year,reactor_fabrication_capacity_units_per_year,notes
                         )
        # Continue with initialiser for child class
        self.reactornumber = math.ceil(self.installed_power/self.power) # divide ship power demand by reactor power supply and round up to nearest integer to find number of reactor modules needed
        self.shipnumber = number
        self.total_reactornumber = self.shipnumber*self.reactornumber

    # set number of combinations of ship and reactor
    def set_number(self,number): # set number of ships of this type
        self.shipnumber = number
        self.total_reactornumber = self.shipnumber*self.reactornumber
    
    def __str__(self):
        return f"{self.shipnumber} {self.shipname} ship(s) from {self.countryname} with {self.reactornumber} {self.reactorname} reactors each\n"+Ship.__str__(self)+Reactor.__str__(self)+Country.__str__(self)