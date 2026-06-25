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


# Temporary set up, will organize later
# Deployment over time (2035-2050)
years = [i for i in range(16)]# years after 2035
# make fleet with Allseas SMRs to begin with. Use fleet shares from Overleaf document.
fleet_shares = [ # tuples (ship segment filepath [str], share of overall fleet [float,%])
    ("inputs/ship/ship_bulkcarrier.txt",21.6),
    ("inputs/ship/ship_container.txt",7.0),("inputs/ship/ship_l_container.txt",18.0),("inputs/ship/ship_ul_container.txt",20.0),
    ("inputs/ship/ship_offshore.txt",12.6),("inputs/ship/ship_tanker.txt",2.7),
    ("inputs/ship/ship_m_icebreaker.txt",3.0),("inputs/ship/ship_l_icebreaker.txt",3.0),("inputs/ship/ship_fishing.txt",2.1),
    ("inputs/ship/ship_cruise.txt",5.0),("inputs/ship/ship_ferry.txt",5.0)
]
ships_total = 600 # 600 vessels in total
fleet = []
fuel_needs = []
infrastructure_needs = []
for year in years: # loop over years after 2035
    fleet_i = []
    for j in range(len(fleet_shares)): # loop over ship segments
        fleet_i.append(init_powered_ship_from_files(fleet_shares[j][0],"inputs/reactor_allseas.txt",
                                                    number=round(fleet_shares[j][1]*1e-2*ships_total*sigmoid(year,1,years[-1]/2))))
    fleet.append(fleet_i)
    fuel_needs_i,infrastructure_needs_i = model(fleet_i)
    fuel_needs.append(fuel_needs_i)
    infrastructure_needs.append(infrastructure_needs_i)
# extract data
fuel_throughput  = [fuel_needs[i].fuel_throughput for i in range(len(fuel_needs))]
swu = [fuel_needs[i].swu for i in range(len(fuel_needs))]
# plot relevant values
plt.plot(np.array(years)+2035,fuel_throughput)
plt.title("Fuel throughput of the entire 600 ship fleet over time")
plt.xlabel("Year")
plt.ylabel("tons")
plt.savefig("plots/fuel_throughput.png")
plt.close()

plt.plot(np.array(years)+2035,np.array(swu)*1e-6)
plt.title("Separative work required of the entire 600 ship fleet over time")
plt.xlabel("Year")
plt.ylabel("MSWU")
plt.savefig("plots/swu.png")
plt.close()

# plot number of ships
fleet_matrix = np.array(fleet)
ships_total_over_time = np.zeros(len(fleet_matrix[:,0]))
for j in range(len(fleet_matrix[0,:])):
    shipnumber = np.array([fleet_matrix[i,j].shipnumber for i in range(len(fleet_matrix[:,j]))])
    ships_total_over_time += shipnumber
    plt.plot(np.array(years)+2035,shipnumber,label=fleet_matrix[0,j].shipname)
plt.plot(np.array(years)+2035,ships_total_over_time,label="Total",lw =4,color='k')
plt.title("Fleet size over time")
plt.xlabel("Year")
plt.ylabel("Number")
plt.legend()
plt.savefig("plots/fleet.png")
plt.close()
# # Test: Panamax containership with Allseas SMR
# PoweredPanamaxContainer = init_powered_ship_from_files("inputs/ship/ship_container.txt","inputs/reactor_allseas.txt")
# # increase number of ships:
# PoweredPanamaxContainer.set_number(18)
# fuel_needs,infrastructure_needs = model([PoweredPanamaxContainer])
# print(f"Fleet requires {fuel_needs.fuel_throughput} tons of fuel and {fuel_needs.swu:e} SWU every {fuel_needs.N_years} years")
# print(f"Fleet consists of:")
# for ship_segment in fleet:
#     print(f"{ship_segment.shipnumber} {ship_segment.shipname} ship(s) with a total of {ship_segment.total_reactornumber} {ship_segment.reactorname} reactors")