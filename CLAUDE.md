# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an industrial waste heat recovery simulation project using TESPy (Thermal Engineering Systems in Python). The project models heat pump systems that recover and upgrade waste heat from industrial processes, calculating performance metrics like COP (Coefficient of Performance) and exergetic efficiency under various operating conditions.

## Installation and Setup

Install all dependencies:
```bash
pip install -r requirements.txt
```

The project requires Python 3.x with the following key dependencies:
- TESPy >= 0.7.5 (thermal system simulation)
- CoolProp >= 6.4.1 (thermodynamic properties)
- fluprodia == 3.3 (fluid property diagrams)
- matplotlib >= 3.6.3, plotly >= 5.20.0 (visualization)
- numpy >= 1.24.0, scipy >= 1.10.0, pandas >= 1.5.3 (numerical analysis)
- scikit-learn >= 1.2.1 (machine learning for linearization)

## Architecture

### Core Components (src/components/)

The project follows an object-oriented architecture with a base class hierarchy:

1. **HeatPumpBase** (waste_heat_source.py) - Abstract base class for all heat pump models
   - Manages TESPy network initialization and configuration
   - Handles design and offdesign simulations
   - Provides COP calculation methods (Lorenz, Carnot)
   - Implements exergy analysis via TESPy's ExergyAnalysis
   - Generates visualization (state diagrams, Sankey diagrams, waterfall diagrams)
   - Provides partload characteristic generation and linearization for MILP optimization

2. **HeatPumpCascadeBase** (heat_pump_cascade.py) - Base class for two-stage cascade heat pumps
   - Extends HeatPumpBase for dual-refrigerant systems
   - Manages two working fluids (wf1, wf2) and intermediate temperature levels
   - Validates intermediate pressure against critical pressure

3. **Concrete implementations** - Subclasses define specific heat pump configurations:
   - heat_pump_base.py (appears to be incomplete/placeholder)
   - boiler.py (placeholder for backup heating system)

### Key Architectural Patterns

**Network Definition Pattern:**
Each heat pump model follows this structure:
- `generate_components()` - Creates TESPy components (compressors, heat exchangers, valves)
- `generate_connections()` - Connects components and defines buses
- `init_simulation()` - Sets initial parameters and starting values
- `design_simulation()` - Performs design point calculation
- `offdesign_simulation()` - Calculates partload characteristics

**Fluid Naming Convention:**
- `wf` - Working fluid (refrigerant, single-stage systems)
- `wf1`, `wf2` - Working fluids (cascade systems)
- `si` - Heat source inlet fluid
- `so` - Heat source outlet fluid

**Connection Naming Convention:**
- `A0`, `A1`, ... - Main refrigerant cycle connections
- `B1`, `B2` - Heat source (evaporator side)
- `C1`, `C2`, `C3` - Heat sink (condenser side)

**Component Parameter Dictionary:**
All models use a `params` dictionary containing:
- `setup`: Model type, refrigerant(s)
- `fluids`: Working fluid compositions
- `ambient`: Ambient conditions for exergy analysis
- Component-specific parameters (e.g., `evap`, `cond`, `comp`)
- Temperature/pressure/mass flow specifications
- `offdesign`: Partload simulation ranges

### Critical Implementation Details

**TESPy Network Initialization:**
```python
self.nw = Network(T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s')
```

**Parameter Handling:**
- When changing parameters, set to `None` first to clear constraints
- Quality: `x=1` (saturated vapor), `x=0` (saturated liquid)
- Pressure ratio: `pr` is outlet/inlet (e.g., 0.98 = 2% pressure drop)
- Heat values: Negative for heat removal (e.g., `Q=-1000` kW)

**Offdesign Simulation:**
- Uses "stable range" technique: sweeps parameters forward and backward to improve convergence
- Requires design simulation to complete successfully first
- Automatically saves stable initialization points for subsequent calculations
- Results saved in MW units to `output/` directory

**Cost Calculation:**
- Implements Kosmadakis & Arpagaus methodology for CAPEX estimation
- Uses CEPCI (Chemical Engineering Plant Cost Index) for year adjustment
- Cost functions saved in `input/CEPCI.json`

**Exergy Analysis:**
- Fuel exergy (E_F): Power input + heat source exergy
- Product exergy (E_P): Heat output exergy
- Exergetic efficiency: epsilon = E_P / E_F

### Directory Structure

- `src/components/` - Heat pump model classes
- `src/components/input/` - Configuration files (CEPCI data, state diagram configs, pre-calculated diagrams)
- `src/components/stable/` - Saved TESPy network states for initialization
- `src/components/output/` - Simulation results, plots, logs

## Running Simulations

**Basic Workflow:**
```python
# Initialize heat pump with parameter dictionary
hp = SomeHeatPump(params)

# Run complete simulation
hp.run_model(print_cop=True, exergy_analysis=True)

# Generate state diagram
hp.generate_state_diagram(diagram_type='logph', savefig=True)

# Perform offdesign analysis
hp.offdesign_simulation(log_simulations=True)

# Generate partload characteristics for optimization
partload_char = hp.calc_partload_char()
linear_model = hp.linearize_partload_char(partload_char, variable='P', line_type='offset')
```

**Performance Metrics:**
- `cop` - Simulated coefficient of performance
- `cop_lorenz` - Ideal Lorenz cycle COP
- `eta_lorenz` - Lorenz efficiency (cop / cop_lorenz)
- `cop_carnot` - Ideal Carnot cycle COP
- `eta_carnot` - Carnot efficiency (cop / cop_carnot)
- `epsilon` - Exergetic efficiency

## Important Implementation Notes

**Thermodynamic Validation:**
The `check_thermodynamic_results()` method validates:
- No negative mass flows
- Heat exchangers transfer heat from hot to cold (Q < 0)
- Positive terminal temperature differences (ttd_u, ttd_l > 0)
- Positive compressor power and pressure ratios

**Pressure Level Calculation:**
Use `get_pressure_levels(T_evap, T_cond, wf)` to calculate evaporation, condensation, and intermediate pressures accounting for terminal temperature differences.

**Visualization:**
- State diagrams: log(p)-h or T-s diagrams using fluprodia
- Sankey diagrams: Exergy flows using plotly
- Waterfall diagrams: Component-wise exergy destruction
- Partload characteristics: Q-P curves colored by COP or epsilon

**Linearization for Optimization:**
The `linearize_partload_char()` method converts nonlinear COP characteristics into linear models for use in Mixed-Integer Linear Programming (MILP) optimization problems. Supports both "origin" (through-origin) and "offset" (with intercept) line types.

## Working with Cascade Systems

Cascade systems use two refrigerants operating at different temperature levels:
- Low-stage cycle: Evaporates from waste heat source
- High-stage cycle: Condenses to heat sink
- Intermediate Heat Exchanger: Transfers heat between stages
- Each cycle has its own state diagram

When implementing cascade models:
- Always validate intermediate temperature is below critical temperature of both refrigerants
- Consider pinch point constraints in intermediate heat exchanger