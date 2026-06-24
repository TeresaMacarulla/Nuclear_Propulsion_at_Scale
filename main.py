import numpy as np
from reactor import Reactor
from ship import Ship, PoweredShip
from utilities import *

# Test: Panamax containership with Allseas SMR
#Allseas = init_reactor_from_file("inputs/reactor_allseas.txt")
#PanamaxContainer = init_ship_from_file("inputs/ship_container.txt")
PoweredPanamaxContainer = init_powered_ship_from_files("inputs/ship_container.txt","inputs/reactor_allseas.txt")
# increase number of ships:
PoweredPanamaxContainer.set_number(18)
print(PoweredPanamaxContainer)
def model(powered_ship):
    """
    Main function for calculating model outputs for a single year.

    Parameters
    ----------
    powered_ship : instance of PoweredShip class
        The input paramaters for the ship and reactor.

    Returns
    -------
    instance of FuelNeeds class
        Fuel related outputs.
    
    instance of InfrastructureNeeds class
        Infrastructure related outputs.
    """
    N_years = 5 # years between refuelings. Should maybe add as variable in Ship class instead
    fuel_throughput  = fuelmass_from_burnup(powered_ship.power,powered_ship.op_time/24*N_years,powered_ship.burnup)
    return FuelNeeds(fuel_throughput),InfrastructureNeeds()