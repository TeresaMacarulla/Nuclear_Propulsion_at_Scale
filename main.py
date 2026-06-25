import numpy as np
from matplotlib import pyplot as plt
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

# Deployment over time (2035-2050)
def deployment(scenario,ships_total = 600):
    """
    Get model outputs over time for a given deployment scenario.

    Parameters
    ----------
    scenario : string
        Filename of scenario. Filepath=f"inputs/scenario/scenario_{scenario}.txt"
    ships_total : int
        Total number of ships in fleet in 2050.
            
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
    years = [i for i in range(16)]# years after 2035
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
        fuel_needs_i,infrastructure_needs_i = model(fleet_i)
        fuel_needs.append(fuel_needs_i)
        infrastructure_needs.append(infrastructure_needs_i)
    return fuel_needs,infrastructure_needs,fleet,years

# Example: load baseline scenario
fuel_needs,infrastructure_needs,fleet,years = deployment("baseline")
def plot_scenario(scenario,ships_total = 600):
    """
    Plot model outputs over time for a given deployment scenario.

    Parameters
    ----------
    scenario : string
        Filename of scenario. Filepath=f"inputs/scenario/scenario_{scenario}.txt"
    ships_total : int
        Total number of ships in fleet in 2050.
            
    Returns
    -------
    void
    """
    # consider adding option for loading stored results from file
    fuel_needs,infrastructure_needs,fleet,years = deployment(scenario,ships_total)
    # extract data
    fuel_throughput  = [fuel_needs[i].fuel_throughput for i in range(len(fuel_needs))]
    swu = [fuel_needs[i].swu for i in range(len(fuel_needs))]
    # plot relevant values
    plt.plot(np.array(years)+2035,fuel_throughput)
    plt.title(f"Fuel throughput of the entire 600 ship fleet over time\n in {scenario} scenario")
    plt.xlabel("Year")
    plt.ylabel("tons")
    plt.savefig(f"plots/{scenario}_fuel_throughput.png")
    plt.close()

    plt.plot(np.array(years)+2035,np.array(swu)*1e-6)
    plt.title(f"Separative work required of the entire 600 ship fleet over time\n in {scenario} scenario")
    plt.xlabel("Year")
    plt.ylabel("MSWU")
    plt.savefig(f"plots/{scenario}_swu.png")
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
    plt.ylabel("Number")
    plt.legend()
    plt.savefig(f"plots/{scenario}_fleet.png")
    plt.close()
    return
plot_scenario("baseline")
# # Test: Panamax containership with Allseas SMR
# PoweredPanamaxContainer = init_powered_ship_from_files("inputs/ship/ship_container.txt","inputs/reactor_allseas.txt")
# # increase number of ships:
# PoweredPanamaxContainer.set_number(18)
# fuel_needs,infrastructure_needs = model([PoweredPanamaxContainer])
# print(f"Fleet requires {fuel_needs.fuel_throughput} tons of fuel and {fuel_needs.swu:e} SWU every {fuel_needs.N_years} years")
# print(f"Fleet consists of:")
# for ship_segment in fleet:
#     print(f"{ship_segment.shipnumber} {ship_segment.shipname} ship(s) with a total of {ship_segment.total_reactornumber} {ship_segment.reactorname} reactors")