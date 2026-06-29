import numpy as np
from matplotlib import pyplot as plt
from utilities import *

def model(powered_ships,
          N_years = 5, # years between refuelings. Should maybe add as variable in Ship class instead
          tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2 # assume tail assay of 0.40% and natural uranium as feed as default
          ):
    """
    Main function for calculating model outputs for a single year.

    Parameters
    ----------
    powered_ships : list of instances of PoweredShip class
        The input paramaters for the different combinations of ship and reactor.
    N_years : int
        Years between refuelings.
    tail_assay : float
        Mass assay of tail after enrichment.
    feed_assay : float
        Mass assay of feed in enrichment.
    Returns
    -------
    instance of FuelNeeds class
        Fuel related outputs.
    instance of InfrastructureNeeds class
        Infrastructure related outputs.
    """
    fuel_throughput  = 0.0 # metric tons
    _feedmass = 0.0 # metric tons
    swu = 0.0 # SWU 
    for powered_ship in powered_ships:
        # The following returns masses/SWUs needed per refueling. Must divide by N_years to get per year
        fuelmass  = fuelmass_from_burnup(powered_ship.power,powered_ship.op_time/24*N_years,powered_ship.burnup)*powered_ship.total_reactornumber
        fuel_throughput += fuelmass
        swu  += SW(fuelmass*1e+3,powered_ship.enrichment*1e-2,tail_assay,feed_assay)
        _feedmass += feedmass(fuelmass,powered_ship.enrichment,tail_assay,feed_assay)
    return FuelNeeds(fuel_throughput,swu,_feedmass),InfrastructureNeeds()

# Deployment over time (2035-2050)
def deployment(scenario,ships_total = 600,N_years = 5,tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2,end_year = 2050):
    """
    Get model outputs over time for a given deployment scenario.

    Parameters
    ----------
    scenario : string
        Filename of scenario. Filepath=f"inputs/scenario/scenario_{scenario}.txt"
    ships_total : int
        Total number of ships in fleet in 2050.
    N_years : int
        Years between refuelings.
    tail_assay : float
        Mass assay of tail after enrichment.
    feed_assay : float
        Mass assay of feed in enrichment.
    Returns
    -------
    List of instances of FuelNeeds class
        Fuel related outputs over time.
    List of instances of InfrastructureNeeds class
        Infrastructure related outputs over time.
    List of lists of instances of PoweredShip class
        Fleet composition over time
    List of floats
        Years after 2035.
    """
    years = [i for i in range(end_year-2035+1)]# years after 2035
    fleet_shares = np.loadtxt(f"inputs/scenario/scenario_{scenario}.txt",delimiter=';',dtype=str)
    fleet = []
    fuel_needs = []
    infrastructure_needs = []
    for year in years: # loop over years after 2035
        fleet_i = []
        for j in range(1,len(fleet_shares[:,0])): # loop over ship segments
            fleet_i.append(init_powered_ship_from_files(f"inputs/ship/ship_{fleet_shares[j,0]}.txt",
                                                        f"inputs/reactor_{fleet_shares[j,2]}.txt",
                                                        number=round(fleet_shares[j,1].astype(float)*1e-2*ships_total*sigmoid(year,1,years[-1]/2)))
                                                        )
        fleet.append(fleet_i)
        fuel_needs_i,infrastructure_needs_i = model(fleet_i,N_years,tail_assay,feed_assay)
        fuel_needs.append(fuel_needs_i)
        infrastructure_needs.append(infrastructure_needs_i)
    return fuel_needs,infrastructure_needs,fleet,years

# Example: load baseline scenario
fuel_needs,infrastructure_needs,fleet,years = deployment("baseline")
def plot_scenario(scenario,ships_total = 600,N_years = 5,tail_assay=0.4*1e-2,feed_assay = 0.72*1e-2,end_year=2050):
    """
    Plot model outputs over time for a given deployment scenario.

    Parameters
    ----------
    scenario : string
        Filename of scenario. Filepath=f"inputs/scenario/scenario_{scenario}.txt"
    ships_total : int
        Total number of ships in fleet in 2050.
    N_years : int
        Years between refuelings.
    tail_assay : float
        Mass assay of tail after enrichment.
    feed_assay : float
        Mass assay of feed in enrichment.
    Returns
    -------
    void
    """
    # consider adding option for loading stored results from file
    fuel_needs,infrastructure_needs,fleet,years = deployment(scenario,ships_total,N_years,tail_assay,feed_assay,end_year)
    # extract data
    fuel_throughput  = [fuel_needs[i].fuel_throughput for i in range(len(fuel_needs))]
    swu = [fuel_needs[i].swu for i in range(len(fuel_needs))]
    feedmass = [fuel_needs[i].feedmass for i in range(len(fuel_needs))]

    # plot fresh fuel throughput
    plt.plot(np.array(years)+2035,np.array(fuel_throughput)/N_years,marker ='o',color='g') # divide by N_years to get yearly value
    plt.title(f"Fuel throughput of a {ships_total} ship fleet per year\n in {scenario} scenario")
    plt.xlabel("Year")
    plt.ylabel("tons")
    plt.savefig(f"plots/{scenario}_fuel_throughput.png")
    plt.close()

    # plot separative work
    plt.plot(np.array(years)+2035,np.array(swu)*1e-6/N_years,marker='o')# divide by N_years to get yearly value
    plt.title(f"Separative work required of a {ships_total} ship fleet per year\n in {scenario} scenario\n natural uranium feed, {tail_assay*1e+2}% tail assay")
    plt.xlabel("Year")
    plt.ylabel("MSWU")
    plt.tight_layout()
    plt.savefig(f"plots/{scenario}_swu.png")
    plt.close()

    # plot natural uranium consumption
    plt.plot(np.array(years)+2035,np.array(feedmass)*1e-3/N_years,color='m',marker='s') # divide by N_years to get yearly value
    plt.title(f"Natural uranium required of a {ships_total} ship fleet per year\n in {scenario} scenario, {tail_assay*1e+2}% tail assay")
    plt.xlabel("Year")
    plt.ylabel("tons")
    plt.savefig(f"plots/{scenario}_feedmass.png")
    plt.close()

    # plot number of ships
    fleet_matrix = np.array(fleet)
    ships_total_over_time = np.zeros(len(fleet_matrix[:,0]))
    for j in range(len(fleet_matrix[0,:])):
        shipnumber = np.array([fleet_matrix[i,j].shipnumber for i in range(len(fleet_matrix[:,j]))])
        ships_total_over_time += shipnumber
        plt.plot(np.array(years)+2035,shipnumber,label=fleet_matrix[0,j].shipname)
    plt.plot(np.array(years)+2035,ships_total_over_time,label="Total",lw =4,color='k')
    plt.title(f"Fleet size over time\n in {scenario} scenario")
    plt.xlabel("Year")
    plt.ylabel("Number of vessels")
    plt.legend()
    plt.savefig(f"plots/{scenario}_fleet.png")
    plt.close()
    return
plot_scenario("baseline",ships_total=800,end_year=2060)
# # Test: Panamax containership with Allseas SMR
# PoweredPanamaxContainer = init_powered_ship_from_files("inputs/ship/ship_container.txt","inputs/reactor_allseas.txt")
# # increase number of ships:
# PoweredPanamaxContainer.set_number(18)
# fuel_needs,infrastructure_needs = model([PoweredPanamaxContainer])
# print(f"Fleet requires {fuel_needs.fuel_throughput} tons of fuel and {fuel_needs.swu:e} SWU every {fuel_needs.N_years} years")
# print(f"Fleet consists of:")
# for ship_segment in fleet:
#     print(f"{ship_segment.shipnumber} {ship_segment.shipname} ship(s) with a total of {ship_segment.total_reactornumber} {ship_segment.reactorname} reactors")