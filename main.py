from tespy.networks import Network
from tespy.components import(
    CycleCloser, Compressor, Valve, SimpleHeatExchanger
)
from tespy.connections import Connection

# create a network object with R134a as fluid
my_plant = Network()

# set the unitsystem for temperatures to °C and for pressure to bar
my_plant.units.set_defaults(
    temperature="degC", pressure="bar", enthalpy="kJ/kg", heat="kW", power="kW"
)

cc = CycleCloser('cycle closer')

# heat sink
co = SimpleHeatExchanger('condensor')
# heat source
ev = SimpleHeatExchanger('evaporater')

va = Valve('expansion valve')
cp = Compressor('compressor')

# connections of heat pump
c1 = Connection(cc, 'out1', ev, 'in1', label='1')
c2 = Connection(ev, 'out1', cp, 'in1', label='2')
c3 = Connection(cp, 'out1', co, 'in1', label='3')
c4 = Connection(co, 'out1', va, 'in1', label='4')
c0 = Connection(va, 'out1', cc, 'in1', label='0')

# this line is crutial: you have to add all connections to your network
my_plant.add_conns(c0, c1, c2, c3, c4)

# set the component and connection parameters
co.set_attr(pr=0.98, Q=-1000)
ev.set_attr(pr=0.98)
cp.set_attr(eta_s=0.85)

c2.set_attr(T=20, x=1, fluid={'R134a':1})
c4.set_attr(T=80, x=0)

my_plant.solve(mode='design')
my_plant.print_results()

print(f'COP = {abs(co.Q.val) / cp.P.val}')