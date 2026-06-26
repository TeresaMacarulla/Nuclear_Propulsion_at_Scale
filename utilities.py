import numpy as np
from reactor import Reactor
from ship import Ship, PoweredShip
from country import Country

class FuelNeeds:
    def __init__(self,fuel_throughput,swu,feedmass):
        self.fuel_throughput = fuel_throughput
        self.swu = swu
        self.feedmass = feedmass
class InfrastructureNeeds:
    def __init__(self):
        pass

def init_reactor_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    power,burnup,enrichment,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,0]
    return Reactor(power,burnup,enrichment,name)

def init_ship_from_file(filename):
    file = np.loadtxt(filename, delimiter=';',dtype=str)
    installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,name = file[1,1].astype(float),file[1,2].astype(float),file[1,3].astype(float),file[1,4].astype(float),file[1,5].astype(float),file[1,6].astype(float),file[1,0]
    return Ship(installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,name)

def init_powered_ship_from_files(shipfilename,reactorfilename,number=1):
    shipfile = np.loadtxt(shipfilename, delimiter=';',dtype=str)
    reactorfile = np.loadtxt(reactorfilename, delimiter=';',dtype=str)
    power,burnup,enrichment,reactorname = reactorfile[1,1].astype(float),reactorfile[1,2].astype(float),reactorfile[1,3].astype(float),reactorfile[1,0]
    installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname = shipfile[1,1].astype(float),shipfile[1,2].astype(float),shipfile[1,3].astype(float),shipfile[1,4].astype(float),shipfile[1,5].astype(float),shipfile[1,6].astype(float),shipfile[1,0]
    return PoweredShip(installed_power,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname,power,burnup,enrichment,reactorname,number=number)

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

def feedmass(fuelmass,enrichment,tail_assay,feed_assay):
    """
    Calculate the required feed mass to produce a given fuel mass with given enrichment, with given tail and feed mass assays.

    Parameters
    ----------
    fuelmass : float
        Mass of enriched uranium fuel [kg].
    enrichment : float
        The enrichment of the uranium fuel [decimal].
    tail_assay : float
        Mass assay of tail [decimal].
    feed_assay : float
        Mass assay of feed [decimal].
    Returns
    -------
    float
        Feed mass [kg].
    """

    return fuelmass*(enrichment-tail_assay)/(feed_assay-tail_assay)

def SW(fuelmass,enrichment,tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2): # assume 0.4% tail assay and natural uranium feed for now
    """
    Calculate the separative work needed to produce a certain mass of enriched uranium from natural uranium.

    Parameters
    ----------
    fuelmass : float
        Mass of enriched uranium fuel [kg].
    enrichment : float
        The enrichment of the uranium fuel [decimal].
    tail_assay : float
        Mass assay of tail [decimal].
    feed_assay : float
        Mass assay of feed [decimal].
    Returns
    -------
    float
        Separative work [SWU].
    """
    F =feedmass(fuelmass,enrichment,tail_assay,feed_assay)
    W  = F-fuelmass
    return fuelmass*(1-2*enrichment)*np.log((1-enrichment)/enrichment)+W*(1-2*tail_assay)*np.log((1-tail_assay)/tail_assay)-F*(1-2*feed_assay)*np.log((1-feed_assay)/feed_assay)

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

def sigmoid(x,a,midpoint):
    return 1 / (1 + np.exp(-a*(x-midpoint)))