import numpy as np
from reactor import Reactor
from ship import Ship, PoweredShip

def init_reactor_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    power,burnup,enrichment,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,0]
    return Reactor(power,burnup,enrichment,name)

def init_ship_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    propulsion,auxiliary,avg_speed,op_time,portcalls,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,4].astype(float),file[1,5].astype(float),file[1,0]
    return Ship(propulsion,auxiliary,avg_speed,op_time,portcalls,name)

def init_powered_ship_from_files(shipfilename,reactorfilename):
    shipfile = np.loadtxt(shipfilename, delimiter=';',dtype=str)
    reactorfile = np.loadtxt(reactorfilename, delimiter=';',dtype=str)
    power,burnup,enrichment,reactorname = reactorfile[1,1].astype(float),reactorfile[1,2].astype(float),reactorfile[1,3].astype(float),reactorfile[1,0]
    propulsion,auxiliary,avg_speed,op_time,portcalls,shipname = shipfile[1,1].astype(float),shipfile[1,2].astype(float),shipfile[1,3].astype(float),shipfile[1,4].astype(float),shipfile[1,5].astype(float),shipfile[1,0]
    return PoweredShip(propulsion,auxiliary,avg_speed,op_time,portcalls,shipname,power,burnup,enrichment,reactorname)

def fuelmass_from_burnup(power,time,burnup):
    """
    Calculate reactor fuel mass from burnup.

    Parameters
    ----------
    power : float
        The reactor power [MW].
    time : float
        Operating time [days].
    burnup : float
        Burnup of reactor [GWd/t]
    Returns
    -------
    float
        The fuel mass [metric tons].
    """
    return power*time/(burnup*1e+3)

class FuelNeeds:
    def __init__(self,fuel_throughput):
        self.fuel_throughput = fuel_throughput
class InfrastructureNeeds:
    def __init__(self):
        pass