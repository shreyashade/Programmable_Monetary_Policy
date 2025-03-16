"""
CBDC Economic Simulation - User Guide

This guide provides instructions for using the CBDC economic simulation system,
including installation, configuration, running simulations, and interpreting results.
"""

# CBDC Economic Simulation: User Guide

## 1. Introduction

The CBDC Economic Simulation is a powerful tool for exploring how Central Bank Digital Currency (CBDC) implementation and programmable monetary policy could transform economic control mechanisms. This guide will help you install, configure, and use the simulation system effectively.

## 2. Installation

### 2.1 System Requirements

- Python 3.8 or higher
- Required Python packages: numpy, pandas, matplotlib, tkinter
- Minimum 4GB RAM recommended
- 500MB free disk space

### 2.2 Installation Steps

1. Clone or download the simulation repository:
   ```
   git clone https://github.com/your-username/cbdc-simulation.git
   cd cbdc-simulation
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Verify installation:
   ```
   python cbdc_simulation.py --version
   ```

## 3. Getting Started

### 3.1 Running the Simulation Interface

To launch the graphical user interface:

```
python cbdc_interface.py
```

This will open the main simulation window with parameter controls and visualization panels.

### 3.2 Running from Command Line

For batch processing or scripted scenarios, you can run the simulation from the command line:

```
python cbdc_simulation.py --config config_file.json --output results.csv
```

### 3.3 Running Test Scenarios

To run predefined test scenarios:

```
python test_runner.py
```

This will execute all test scenarios and save results to the `test_results` directory.

## 4. Configuring Simulations

### 4.1 Parameter Categories

The simulation includes several categories of parameters:

- **Simulation Settings**: Time horizon, random seed
- **Initial Economic State**: Starting values for GDP, inflation, unemployment, etc.
- **Macroeconomic Parameters**: Consumption, investment, Phillips curve sensitivity, etc.
- **CBDC Parameters**: Interest rates, programmable features, constraints
- **International Trade Parameters**: Tariffs, exchange rates, capital controls
- **Banking Sector Parameters**: Capital requirements, reserve requirements, etc.

### 4.2 Using the Interface

The graphical interface provides intuitive controls for all parameters:

1. **Parameter Sections**: Parameters are organized into collapsible sections
2. **Sliders**: Adjust numeric parameters with sliders
3. **Dropdown Menus**: Select from predefined options
4. **Checkboxes**: Toggle boolean parameters
5. **Scenario Selection**: Choose from predefined scenarios or create custom ones
6. **Load/Save**: Save configurations for later use or load existing ones

### 4.3 Configuration Files

Configurations can be saved and loaded as JSON files with the following structure:

```json
{
  "time_horizon": 20,
  "random_seed": 42,
  "initial_state": {
    "gdp": 20000,
    "inflation_rate": 2.0,
    "unemployment_rate": 4.0,
    "interest_rate": 2.5,
    "government_spending": 4000,
    "tax_revenue": 3500,
    "cbdc_supply": 0
  },
  "macro_parameters": {
    "autonomous_consumption": 1500,
    "marginal_propensity_to_consume": 0.6,
    "autonomous_investment": 2000,
    "investment_interest_sensitivity": 100,
    "phillips_curve_sensitivity": 0.5,
    "natural_unemployment": 4.0,
    "potential_output_growth": 2.5
  },
  "cbdc_parameters": {
    "cbdc_interest_rate": 0.0,
    "programmable_money_validity": 365,
    "conditional_spending_constraints": 0.0,
    "automatic_fiscal_transfers": 0.0,
    "smart_contract_based_lending": 0.0,
    "foreign_exchange_controls": 0.0,
    "macroprudential_tools": 0.0,
    "emergency_override_mechanisms": 0.0,
    "programmable_asset_purchases": 0.0
  },
  "trade_parameters": {
    "tariff_rate": 0.05,
    "customs_efficiency": 0.8,
    "exchange_rate_regime": "floating",
    "exchange_rate_target": 1.0,
    "capital_flow_controls": 0.0,
    "cbdc_trade_settlement": 0.0
  },
  "banking_parameters": {
    "capital_requirement": 0.08,
    "reserve_requirement": 0.02,
    "lending_risk_appetite": 0.5,
    "cbdc_disintermediation_factor": 0.2,
    "quantitative_easing": 0.0
  },
  "policy_changes": {
    "4": {
      "cbdc_interest_rate": 1.0
    },
    "8": {
      "automatic_fiscal_transfers": 200.0
    }
  },
  "shocks": {
    "6": {
      "gdp": -500.0
    }
  }
}
```

## 5. Running Simulations

### 5.1 Basic Simulation

To run a basic simulation:

1. Configure parameters using the interface or load a configuration file
2. Click the "Run Simulation" button
3. View results in the Dashboard, Results, and Details tabs

### 5.2 Scenario Comparison

To compare different scenarios:

1. Run the first scenario and save the results
2. Modify parameters or load a different configuration
3. Run the second scenario
4. Use the Results tab to select variables and compare outcomes

### 5.3 Sensitivity Analysis

To perform sensitivity analysis:

1. Use the `scenario_testing.py` module with the `run_sensitivity_analysis` function
2. Specify the parameter to vary and the range of values
3. Run the analysis and examine the results

Example:
```python
from scenario_testing import run_sensitivity_analysis
from cbdc_simulation import create_default_config

config = create_default_config()
results = run_sensitivity_analysis(
    config,
    "cbdc_parameters.cbdc_interest_rate",
    [0.0, 1.0, 2.0, 3.0, 4.0],
    "sensitivity_results"
)
```

## 6. Analyzing Results

### 6.1 Dashboard View

The Dashboard tab provides:

- Key metrics summary (GDP growth, inflation, unemployment, etc.)
- Four main charts showing important economic variables
- Quick overview of simulation outcomes

### 6.2 Results View

The Results tab allows:

- Selection of specific variables to plot
- Customization of chart display
- Comparison of multiple variables over time

### 6.3 Details View

The Details tab provides:

- Summary of simulation parameters
- Final values of key economic indicators
- Analysis of CBDC impact

### 6.4 Exported Data

Simulation results are exported as CSV files with columns for all economic variables and rows for each time step. These can be imported into other analysis tools for further processing.

## 7. Predefined Scenarios

### 7.1 Default Scenario

The default scenario represents a conventional economy without CBDC, providing a baseline for comparison.

### 7.2 CBDC Adoption Scenario

This scenario models the gradual introduction of CBDC with moderate programmable features.

### 7.3 Trade War Scenario

This scenario simulates increased tariffs and trade barriers, with CBDC used for trade settlement.

### 7.4 Banking Crisis Scenario

This scenario models financial sector stress with deposit flight to CBDC and central bank emergency measures.

## 8. Creating Custom Scenarios

### 8.1 Using the Interface

To create a custom scenario:

1. Start with a predefined scenario as a base
2. Modify parameters as needed
3. Save the configuration with a descriptive name

### 8.2 Using the API

To create custom scenarios programmatically:

```python
from scenario_testing import ScenarioTester
from cbdc_simulation import create_default_config

tester = ScenarioTester()
custom_config = tester.create_custom_scenario(
    "High CBDC Interest",
    "CBDC Adoption",
    {
        "cbdc_parameters.cbdc_interest_rate": 2.0,
        "policy_changes.4:smart_contract_based_lending": 0.5
    }
)
results = tester.run_scenario("High CBDC Interest", custom_config)
```

### 8.3 Adding Policy Changes

To add policy changes at specific time steps:

1. In the interface, use the "Policy Changes" section
2. Programmatically, add entries to the `policy_changes` dictionary:
   ```python
   config.policy_changes = {
       4: {"cbdc_interest_rate": 1.0},
       8: {"automatic_fiscal_transfers": 200.0}
   }
   ```

### 8.4 Adding Economic Shocks

To add economic shocks:

1. In the interface, use the "Economic Shocks" section
2. Programmatically, add entries to the `shocks` dictionary:
   ```python
   config.shocks = {
       6: {"gdp": -500.0, "unemployment_rate": 2.0}
   }
   ```

## 9. Interpreting Results

### 9.1 Key Economic Indicators

- **GDP**: Total economic output
- **Inflation Rate**: Rate of price increases
- **Unemployment Rate**: Percentage of labor force without jobs
- **Interest Rate**: Market interest rate
- **CBDC Supply**: Amount of CBDC in circulation
- **Bank Deposits**: Traditional bank deposits
- **Financial Stress Index**: Measure of financial system stability

### 9.2 CBDC Impact Metrics

- **CBDC Adoption Rate**: CBDC as percentage of total money supply
- **Bank Disintermediation**: Reduction in bank deposits due to CBDC
- **Monetary Policy Transmission**: Effectiveness of interest rate changes
- **Economic Stability**: Reduced volatility in key indicators

### 9.3 Comparative Analysis

When comparing scenarios, consider:

- Differences in growth trajectories
- Inflation and unemployment outcomes
- Financial stability implications
- Speed and effectiveness of policy responses
- Long-term structural changes

## 10. Advanced Usage

### 10.1 Extending the Model

To extend the model with new features:

1. Add new parameters to the appropriate parameter classes
2. Implement the economic relationships in the model components
3. Update the visualization to display new variables

### 10.2 Custom Reporting

To create custom reports:

```python
from scenario_testing import ScenarioTester

tester = ScenarioTester()
tester.run_standard_scenarios()
report_path = tester.generate_report()
```

### 10.3 Batch Processing

For batch processing multiple scenarios:

```python
import json
import os
from cbdc_simulation import SimulationConfig, CBDCSimulation

# Load configurations from directory
config_dir = "configs"
results_dir = "batch_results"
os.makedirs(results_dir, exist_ok=True)

for filename in os.listdir(config_dir):
    if filename.endswith(".json"):
        config_path = os.path.join(config_dir, filename)
        config = SimulationConfig.from_json(config_path)
        
        simulation = CBDCSimulation(config)
        results = simulation.run()
        
        results_path = os.path.join(results_dir, f"{os.path.splitext(filename)[0]}_results.csv")
        results.to_csv(results_path, index=False)
```

## 11. Troubleshooting

### 11.1 Common Issues

- **Simulation Crashes**: Check for invalid parameter combinations
- **Unrealistic Results**: Verify parameter values are within reasonable ranges
- **Performance Issues**: Reduce time horizon or simplify scenario

### 11.2 Error Messages

- **"Invalid parameter value"**: Parameter outside allowed range
- **"Configuration file not found"**: Check file path
- **"Simulation diverged"**: Economic model became unstable, adjust parameters

### 11.3 Getting Help

For additional assistance:

- Check the documentation in the `documentation.md` file
- Examine the source code comments
- Contact the development team at support@cbdc-simulation.example.com

## 12. Conclusion

The CBDC Economic Simulation provides a powerful platform for exploring the economic impacts of central bank digital currencies and programmable monetary policy. By following this guide, you can configure, run, and analyze simulations to gain insights into how CBDCs could transform economic control mechanisms and outcomes.

Remember that while the simulation is based on established economic principles, it represents a simplified model of complex real-world systems. Results should be interpreted as illustrative rather than predictive, and should inform rather than determine policy decisions.
