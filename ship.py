class Ship:
    def __init__(self,propulsion,auxiliary,avg_speed,op_time,portcalls,name):
        self.propulsion = propulsion
        self.auxiliary = auxiliary
        self.avg_speed = avg_speed
        self.op_time = op_time
        self.portcalls = portcalls
        self.name = name
    def __str__(self):
        return (
            f"=== {self.name} ship characteristics ===\n"
            f"Installed propulsion power: {self.propulsion} MW\n"
            f"Installed auxiliary power:  {self.auxiliary} MW\n"
            f"Average speed:  {self.avg_speed} knots\n"
            f"Operational time:    {self.op_time} hours\n"
            f"Number of portcalls per year:  {self.portcalls}"
        )    
from reactor import Reactor   
import math 
class PoweredShip(Ship,Reactor):
    # set number of combinations of ship and reactor
    def __init__(self):
        super().__init__() # inherit from parents
        self.reactor_number = math.ceil((self.propulsion+self.power)*1.0/self.power) # divide ship power demand by reactor power supply and round up to nearest integer to find number of reactor modules needed
    def set_number(self,number):
        return self.number