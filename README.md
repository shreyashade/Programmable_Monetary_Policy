# Enhanced CBDC Economic Simulation

A comprehensive simulation system for modeling the economic impacts of Central Bank Digital Currency (CBDC) implementation with programmable monetary policy.

![CBDC Simulation](https://img.shields.io/badge/CBDC-Simulation-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Overview

This project provides a sophisticated economic simulation framework that demonstrates how a country with adopted CBDCs could control its economic future through programmable monetary policy. The simulation incorporates real-world economic data, transparent calculation processes, and natural language explanations to help users understand the complex interactions between CBDC features and economic outcomes.

## Key Features

- **Real-World Data Integration**: Initialize simulations with actual economic data from any country using World Bank indicators
- **Dynamic Simulation**: Project economic outcomes over multiple quarters based on current economic conditions and policy changes
- **Comprehensive Economic Model**: Incorporates IS-LM-BP framework with sectoral components (households, businesses, banking, government, external)
- **CBDC-Specific Controls**: Model advanced CBDC mechanisms including:
  - Time-based money validity controls
  - Use-case restrictions and conditional spending constraints
  - Automatic fiscal transfers
  - Smart contract-based lending
  - Foreign exchange controls
- **International Trade Components**: Includes tariffs, customs efficiency, exchange rate mechanisms, and cross-border CBDC settlement
- **Banking Sector Dynamics**: Models interactions between traditional banking and CBDC, including disintermediation effects
- **Calculation Transparency**: Detailed logging of all economic calculations to understand how results are derived
- **Natural Language Explanations**: Plain-language descriptions of economic mechanisms, parameter changes, and policy recommendations
- **Interactive Interface**: User-friendly graphical interface for configuring parameters, running simulations, and visualizing results
- **Scenario Testing**: Framework for testing various economic scenarios and policy responses, including sensitivity analysis

## Installation

1. Clone this repository:
```bash
git clone https://github.com/shreyashade/Programmable_Monetary_Policy.git
cd enhanced-cbdc-simulation
```

2. Install required dependencies:
```bash
pip install numpy pandas matplotlib tkinter
```

3. Run the simulation interface:
```bash
python enhanced_interface.py
```

## Usage

### Basic Simulation

1. Launch the interface with `python enhanced_interface.py`
2. Configure simulation parameters or select a predefined scenario
3. Click "Run Simulation" to execute
4. View results in the Dashboard, Results, and Explanations tabs

### Using Real-World Data

1. In the "Real-World Data Integration" section, select a country
2. Choose the data year (most recent available by default)
3. Click "Load Country Data" to initialize the simulation with actual economic indicators
4. Run the simulation to see projected outcomes based on real-world starting conditions

### Understanding Results

- The **Dashboard** tab provides a high-level overview of key economic indicators
- The **Results** tab allows detailed exploration of specific variables over time
- The **Details** tab shows comprehensive information about the simulation configuration
- The **Calculations** tab reveals the step-by-step economic calculations
- The **Explanations** tab offers natural language descriptions of economic mechanisms

### Scenario Testing

For advanced scenario testing and sensitivity analysis, use the scenario_testing.py module:

```python
from scenario_testing import ScenarioTester
from cbdc_simulation import create_default_config

# Initialize tester
tester = ScenarioTester(create_default_config())

# Run scenarios
tester.run_scenario("Base", create_default_config())
tester.run_scenario("High CBDC Interest", modified_config)

# Compare results
tester.compare_scenarios(["Base", "High CBDC Interest"], 
                        ["gdp", "inflation_rate", "bank_deposits"])

# Generate reports
report = tester.generate_scenario_report("High CBDC Interest")
```

## Project Structure

- **cbdc_simulation.py**: Core economic simulation engine
- **data_integration.py**: Real-world data fetching and integration
- **enhanced_interface.py**: Interactive graphical user interface
- **scenario_testing.py**: Framework for testing economic scenarios
- **test_runner.py**: Automated testing utilities

## Economic Model

The simulation is based on an enhanced IS-LM-BP framework that incorporates CBDC-specific mechanisms:

1. **IS Curve (Goods Market)**: Y = C + I + G + NX
   - Consumption (C) is affected by CBDC spending constraints
   - Investment (I) is influenced by smart contract lending

2. **LM Curve (Money Market)**: M/P = L(Y, r)
   - Money supply (M) includes both traditional money and CBDC
   - CBDC interest rates affect money demand

3. **BP Curve (External Balance)**: NX + CF = 0
   - Net exports (NX) are influenced by exchange rates
   - Capital flows (CF) are affected by CBDC foreign exchange controls

4. **Banking Sector**: Models disintermediation effects when CBDC competes with bank deposits

5. **Price Level Determination**: Based on output gap and inflation expectations

## CBDC Parameters

The simulation includes the following CBDC-specific parameters:

- **CBDC Interest Rate**: Interest paid on CBDC balances
- **Programmable Money Validity**: Time period for which CBDC remains valid
- **Conditional Spending Constraints**: Restrictions on how CBDC can be spent
- **Automatic Fiscal Transfers**: Direct payments through CBDC
- **Smart Contract Based Lending**: Automated lending through smart contracts
- **Foreign Exchange Controls**: Restrictions on cross-border CBDC flows
- **Macroprudential Tools**: System-wide financial stability tools
- **Emergency Override Mechanisms**: Crisis response capabilities

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Economic model based on IS-LM-BP framework with CBDC extensions
- Data provided by World Bank Development Indicators
- Inspired by research on programmable monetary policy and CBDC implementation
