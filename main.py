import numpy as np
from reactor import Reactor
from ship import Ship, PoweredShip
from utilities import *

def model(powered_ships):
    """
    Main function for calculating model outputs for a single year.

    Parameters
    ----------
    powered_ships : list of instances of PoweredShip class
        The input paramaters for the different combinations of ship and reactor.

    Returns
    -------
    instance of FuelNeeds class
        Fuel related outputs.
    
    instance of InfrastructureNeeds class
        Infrastructure related outputs.
    """
    N_years = 5 # years between refuelings. Should maybe add as variable in Ship class instead
    fuel_throughput  = 0.0 # metric tons
    swu = 0.0 # SWU 
    for powered_ship in powered_ships:
        fuelmass  = fuelmass_from_burnup(powered_ship.power,powered_ship.op_time/24*N_years,powered_ship.burnup)*powered_ship.total_reactornumber
        fuel_throughput += fuelmass
        swu  += SW(fuelmass*1e+3,powered_ship.enrichment*1e-2)
    return FuelNeeds(fuel_throughput,swu,N_years),InfrastructureNeeds()

# Test: Panamax containership with Allseas SMR
PoweredPanamaxContainer = init_powered_ship_from_files("inputs/ship_container.txt","inputs/reactor_allseas.txt")
# increase number of ships:
PoweredPanamaxContainer.set_number(18)
fuel_needs,infrastructure_needs = model([PoweredPanamaxContainer])
print(f"Fleet requires {fuel_needs.fuel_throughput} tons of fuel and {fuel_needs.swu:e} SWU every {fuel_needs.N_years} years")