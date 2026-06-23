class Ship:
    def __init__(self,propulsion,auxiliary,avg_speed,op_time,portcalls,name):
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
import math
class PoweredShip(Ship,Reactor):
    def __init__(self,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname,power,burnup,enrichment,reactorname):
        Ship.__init__(self,propulsion,auxiliary,avg_speed,op_time,portcalls,shipname) 
        Reactor.__init__(self,power,burnup,enrichment,reactorname)
        self.reactornumber = math.ceil((self.propulsion+self.auxiliary)*1.0/self.power) # divide ship power demand by reactor power supply and round up to nearest integer to find number of reactor modules needed
        self.shipnumber = 1
        self.total_reactornumber = self.shipnumber*self.reactornumber

    # set number of combinations of ship and reactor
    def set_number(self,number): # set number of ships of this type
        self.shipnumber = number
        self.total_reactornumber = self.shipnumber*self.reactornumber
    
    def __str__(self):
        return f"{self.shipnumber} {self.shipname} ship(s) with {self.reactornumber} {self.reactorname} reactors each\n"+Ship.__str__(self)+Reactor.__str__(self)