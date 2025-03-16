"""
CBDC Economic Simulation - Scenario Testing Module

This module provides predefined scenarios for testing the CBDC economic simulation system
and analyzing the impacts of different policy configurations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple
import os
import sys

# Import the simulation system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cbdc_simulation import (
    SimulationConfig, CBDCParameters, TradeParameters, 
    BankingParameters, MacroParameters, EconomicState,
    CBDCSimulation
)
from data_integration import WorldBankDataFetcher, DataExplainer

class ScenarioTester:
    """
    Class for running and analyzing different economic scenarios with the CBDC simulation.
    """
    
    def __init__(self, base_config: Optional[SimulationConfig] = None):
        """
        Initialize the scenario tester.
        
        Args:
            base_config: Optional base configuration to use for scenarios
        """
        self.base_config = base_config
        self.data_fetcher = WorldBankDataFetcher()
        self.data_explainer = DataExplainer(self.data_fetcher)
        self.scenario_results = {}
        self.calculation_logs = {}
    
    def run_scenario(self, name: str, config: SimulationConfig, log_calculations: bool = True) -> pd.DataFrame:
        """
        Run a simulation scenario and store the results.
        
        Args:
            name: Name of the scenario
            config: Simulation configuration for this scenario
            log_calculations: Whether to log detailed calculations
            
        Returns:
            DataFrame with simulation results
        """
        print(f"Running scenario: {name}")
        
        # Initialize calculation logs if needed
        calc_logs = [] if log_calculations else None
        
        # Run simulation
        simulation = EnhancedCBDCSimulation(config, calc_logs)
        results = simulation.run()
        
        # Store results and logs
        self.scenario_results[name] = results
        if log_calculations:
            self.calculation_logs[name] = calc_logs
        
        print(f"Scenario {name} completed with {len(results)} time steps")
        return results
    
    def compare_scenarios(self, scenario_names: List[str], variables: List[str]) -> Dict[str, plt.Figure]:
        """
        Compare multiple scenarios across specified variables.
        
        Args:
            scenario_names: List of scenario names to compare
            variables: List of variables to compare
            
        Returns:
            Dictionary of matplotlib figures for each variable
        """
        if not all(name in self.scenario_results for name in scenario_names):
            missing = [name for name in scenario_names if name not in self.scenario_results]
            raise ValueError(f"Missing scenarios: {missing}")
        
        figures = {}
        
        # Create a figure for each variable
        for var in variables:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for name in scenario_names:
                results = self.scenario_results[name]
                if var in results.columns:
                    ax.plot(results.index, results[var], label=name)
            
            ax.set_title(f"{var} Comparison")
            ax.set_xlabel("Time (quarters)")
            ax.set_ylabel(var)
            ax.legend()
            ax.grid(True)
            
            figures[var] = fig
        
        return figures
    
    def sensitivity_analysis(self, parameter_name: str, parameter_values: List[float], 
                            output_variables: List[str], base_scenario: str = "Base") -> Dict[str, plt.Figure]:
        """
        Perform sensitivity analysis by varying a parameter and observing impacts.
        
        Args:
            parameter_name: Name of the parameter to vary
            parameter_values: List of values to test
            output_variables: List of output variables to track
            base_scenario: Name of the base scenario to modify
            
        Returns:
            Dictionary of matplotlib figures for each output variable
        """
        if base_scenario not in self.scenario_results:
            raise ValueError(f"Base scenario '{base_scenario}' not found")
        
        # Get base configuration
        if self.base_config is None:
            raise ValueError("Base configuration not set")
        
        base_config = self.base_config
        
        # Run scenarios with different parameter values
        scenario_names = []
        
        for value in parameter_values:
            # Create a new configuration based on the base
            config = self._create_config_with_parameter(base_config, parameter_name, value)
            
            # Create scenario name
            scenario_name = f"{parameter_name}={value}"
            scenario_names.append(scenario_name)
            
            # Run scenario
            self.run_scenario(scenario_name, config)
        
        # Compare results
        figures = self.compare_scenarios(scenario_names, output_variables)
        
        return figures
    
    def _create_config_with_parameter(self, base_config: SimulationConfig, 
                                     parameter_name: str, value: float) -> SimulationConfig:
        """
        Create a new configuration with a modified parameter value.
        
        Args:
            base_config: Base configuration
            parameter_name: Name of the parameter to modify
            value: New value for the parameter
            
        Returns:
            New configuration with the modified parameter
        """
        # Create a copy of the base configuration
        config = SimulationConfig(
            time_horizon=base_config.time_horizon,
            start_date=base_config.start_date,
            random_seed=base_config.random_seed
        )
        
        # Copy initial state
        state_dict = base_config.initial_state.as_dict()
        state = EconomicState()
        for key, val in state_dict.items():
            if hasattr(state, key):
                setattr(state, key, val)
        config.initial_state = state
        
        # Copy parameter sets
        config.macro_parameters = MacroParameters()
        for key, val in base_config.macro_parameters.as_dict().items():
            if hasattr(config.macro_parameters, key):
                setattr(config.macro_parameters, key, val)
        
        config.cbdc_parameters = CBDCParameters()
        for key, val in base_config.cbdc_parameters.as_dict().items():
            if hasattr(config.cbdc_parameters, key):
                setattr(config.cbdc_parameters, key, val)
        
        config.trade_parameters = TradeParameters()
        for key, val in base_config.trade_parameters.as_dict().items():
            if hasattr(config.trade_parameters, key):
                setattr(config.trade_parameters, key, val)
        
        config.banking_parameters = BankingParameters()
        for key, val in base_config.banking_parameters.as_dict().items():
            if hasattr(config.banking_parameters, key):
                setattr(config.banking_parameters, key, val)
        
        # Modify the specified parameter
        if parameter_name in state_dict and hasattr(config.initial_state, parameter_name):
            setattr(config.initial_state, parameter_name, value)
        elif hasattr(config.macro_parameters, parameter_name):
            setattr(config.macro_parameters, parameter_name, value)
        elif hasattr(config.cbdc_parameters, parameter_name):
            setattr(config.cbdc_parameters, parameter_name, value)
        elif hasattr(config.trade_parameters, parameter_name):
            setattr(config.trade_parameters, parameter_name, value)
        elif hasattr(config.banking_parameters, parameter_name):
            setattr(config.banking_parameters, parameter_name, value)
        else:
            raise ValueError(f"Parameter '{parameter_name}' not found in any parameter set")
        
        return config
    
    def generate_scenario_report(self, scenario_name: str) -> str:
        """
        Generate a detailed report for a specific scenario.
        
        Args:
            scenario_name: Name of the scenario
            
        Returns:
            Markdown formatted report
        """
        if scenario_name not in self.scenario_results:
            raise ValueError(f"Scenario '{scenario_name}' not found")
        
        results = self.scenario_results[scenario_name]
        
        # Generate report
        report = [
            f"# Scenario Analysis: {scenario_name}",
            "",
            "## Summary Statistics",
            ""
        ]
        
        # Add summary statistics
        if len(results) > 0:
            initial = results.iloc[0]
            final = results.iloc[-1]
            
            # Calculate key metrics
            gdp_growth = ((final.get("gdp", 0) / initial.get("gdp", 1)) - 1) * 100
            inflation_avg = results.get("inflation_rate", pd.Series([0])).mean()
            unemployment_avg = results.get("unemployment_rate", pd.Series([0])).mean()
            
            report.extend([
                f"- **Time Horizon**: {len(results)} quarters",
                f"- **GDP Growth**: {gdp_growth:.2f}%",
                f"- **Average Inflation**: {inflation_avg:.2f}%",
                f"- **Average Unemployment**: {unemployment_avg:.2f}%",
                f"- **Final Exchange Rate**: {final.get('exchange_rate', 1.0):.4f}",
                f"- **Final CBDC Adoption**: {(final.get('cbdc_supply', 0) / final.get('money_supply', 1)) * 100:.2f}%",
                ""
            ])
        
        # Add natural language explanation
        if len(results) > 0:
            initial_state = results.iloc[0].to_dict()
            final_state = results.iloc[-1].to_dict()
            
            explanation = self.data_explainer.explain_simulation_results(
                initial_state, final_state, len(results)
            )
            
            report.extend([
                "## Detailed Analysis",
                "",
                explanation,
                ""
            ])
        
        # Add policy recommendations
        if len(results) > 0:
            # Extract CBDC parameters (assuming they're available)
            cbdc_params = {}
            
            recommendations = self.data_explainer.generate_policy_recommendations(
                results, cbdc_params
            )
            
            report.extend([
                "## Policy Recommendations",
                "",
                recommendations,
                ""
            ])
        
        return "\n".join(report)
    
    def export_scenario_data(self, scenario_name: str, filepath: str) -> None:
        """
        Export scenario data to a CSV file.
        
        Args:
            scenario_name: Name of the scenario
            filepath: Path to save the CSV file
        """
        if scenario_name not in self.scenario_results:
            raise ValueError(f"Scenario '{scenario_name}' not found")
        
        results = self.scenario_results[scenario_name]
        results.to_csv(filepath, index=True)
        
        print(f"Scenario data exported to {filepath}")
    
    def export_calculation_logs(self, scenario_name: str, filepath: str) -> None:
        """
        Export calculation logs to a text file.
        
        Args:
            scenario_name: Name of the scenario
            filepath: Path to save the text file
        """
        if scenario_name not in self.calculation_logs:
            raise ValueError(f"Calculation logs for scenario '{scenario_name}' not found")
        
        logs = self.calculation_logs[scenario_name]
        
        with open(filepath, 'w') as f:
            for log in logs:
                f.write(f"{log}\n\n")
        
        print(f"Calculation logs exported to {filepath}")


class EnhancedCBDCSimulation(CBDCSimulation):
    """Enhanced CBDC simulation with calculation logging and transparency."""
    
    def __init__(self, config, calculation_logs=None):
        """
        Initialize the enhanced simulation.
        
        Args:
            config: Simulation configuration
            calculation_logs: Optional list to store calculation logs
        """
        super().__init__(config)
        self.calculation_logs = calculation_logs or []
    
    def _solve_equilibrium(self):
        """Override to add calculation logging."""
        # Log initial state
        self._log_calculation("Starting equilibrium calculation", {
            "gdp": self.current_state.gdp,
            "interest_rate": self.current_state.interest_rate,
            "exchange_rate": self.current_state.exchange_rate,
            "price_level": self.current_state.price_level
        })
        
        # Call original method
        super()._solve_equilibrium()
        
        # Log final state
        self._log_calculation("Equilibrium solution", {
            "gdp": self.current_state.gdp,
            "interest_rate": self.current_state.interest_rate,
            "exchange_rate": self.current_state.exchange_rate,
            "price_level": self.current_state.price_level
        })
    
    def _equilibrium_equations(self, vars):
        """Override to add calculation logging."""
        # Extract variables
        Y, r, e, P = vars
        
        # Extract parameters for readability
        C0 = self.macro_params.autonomous_consumption
        c = self.macro_params.marginal_propensity_to_consume
        I0 = self.macro_params.autonomous_investment
        b = self.macro_params.investment_interest_sensitivity
        G = self.current_state.government_spending
        T = self.current_state.tax_revenue
        NX0 = self.current_state.net_exports
        M = self.current_state.money_supply
        k = self.macro_params.money_demand_income_sensitivity
        h = self.macro_params.money_demand_interest_sensitivity
        
        # CBDC effects
        spending_constraint = self.cbdc_params.conditional_spending_constraints
        smart_lending = self.cbdc_params.smart_contract_based_lending
        forex_controls = self.cbdc_params.foreign_exchange_controls
        
        # Calculate components with CBDC effects
        
        # Consumption with CBDC constraints
        C = C0 + c * (Y - T) * (1 - spending_constraint)
        
        # Investment with smart contract lending
        I = I0 - b * r + smart_lending * 100
        
        # Net exports with forex controls and exchange rate
        NX = NX0 - 0.2 * Y - forex_controls * 50 + 0.1 * (e - 1) * Y
        
        # Money demand
        Md = k * Y - h * r
        
        # System of equations (deviations from equilibrium should be zero)
        goods_market = Y - (C + I + G + NX)  # IS curve
        money_market = M / P - Md  # LM curve
        forex_market = NX - (r - 0.02) * 1000  # BP curve (simplified)
        price_adjustment = P - (Y / self.current_state.potential_gdp) * self.current_state.price_level  # Price level determination
        
        # Log calculations
        self._log_calculation("IS-LM-BP Equations", {
            "Y": Y,
            "r": r,
            "e": e,
            "P": P,
            "C": C,
            "I": I,
            "G": G,
            "NX": NX,
            "M": M,
            "Md": Md,
            "goods_market_eq": goods_market,
            "money_market_eq": money_market,
            "forex_market_eq": forex_market,
            "price_adjustment_eq": price_adjustment
        })
        
        return np.array([goods_market, money_market, forex_market, price_adjustment])
    
    def _update_state_variables(self):
        """Override to add calculation logging."""
        # Log initial state
        self._log_calculation("Before state update", {
            "gdp": self.current_state.gdp,
            "inflation_rate": self.current_state.inflation_rate,
            "unemployment_rate": self.current_state.unemployment_rate,
            "exchange_rate": self.current_state.exchange_rate
        })
        
        # Call original method
        super()._update_state_variables()
        
        # Log final state
        self._log_calculation("After state update", {
            "gdp": self.current_state.gdp,
            "inflation_rate": self.current_state.inflation_rate,
            "unemployment_rate": self.current_state.unemployment_rate,
            "exchange_rate": self.current_state.exchange_rate
        })
    
    def _log_calculation(self, title, variables):
        """
        Log a calculation step with variables.
        
        Args:
            title: Title for the calculation step
            variables: Dictionary of variable names and values
        """
        if self.calculation_logs is None:
            return
        
        # Format timestamp
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Format variables
        var_strings = []
        for name, value in variables.items():
            if isinstance(value, float):
                var_strings.append(f"{name} = {value:.6f}")
            else:
                var_strings.append(f"{name} = {value}")
        
        # Create log entry
        log_entry = f"[{timestamp}] {title}:\n" + "\n".join(var_strings)
        
        # Add to logs
        self.calculation_logs.append(log_entry)


def run_standard_scenarios():
    """Run a set of standard scenarios and generate reports."""
    from cbdc_simulation import create_default_config, create_cbdc_adoption_scenario, create_trade_war_scenario, create_banking_crisis_scenario
    
    # Create output directory
    os.makedirs("scenario_results", exist_ok=True)
    
    # Initialize scenario tester
    tester = ScenarioTester(create_default_config())
    
    # Run scenarios
    tester.run_scenario("Base", create_default_config())
    tester.run_scenario("CBDC Adoption", create_cbdc_adoption_scenario())
    tester.run_scenario("Trade War", create_trade_war_scenario())
    tester.run_scenario("Banking Crisis", create_banking_crisis_scenario())
    
    # Compare key variables
    key_variables = ["gdp", "inflation_rate", "unemployment_rate", "cbdc_supply", "bank_deposits"]
    figures = tester.compare_scenarios(
        ["Base", "CBDC Adoption", "Trade War", "Banking Crisis"],
        key_variables
    )
    
    # Save figures
    for var, fig in figures.items():
        fig.savefig(f"scenario_results/{var}_comparison.png")
    
    # Generate reports
    for scenario in ["Base", "CBDC Adoption", "Trade War", "Banking Crisis"]:
        report = tester.generate_scenario_report(scenario)
        
        with open(f"scenario_results/{scenario.lower().replace(' ', '_')}_report.md", 'w') as f:
            f.write(report)
        
        # Export data
        tester.export_scenario_data(
            scenario, 
            f"scenario_results/{scenario.lower().replace(' ', '_')}_data.csv"
        )
        
        # Export calculation logs
        tester.export_calculation_logs(
            scenario, 
            f"scenario_results/{scenario.lower().replace(' ', '_')}_calculations.txt"
        )
    
    print("Standard scenarios completed. Results saved to 'scenario_results' directory.")


def run_sensitivity_analysis():
    """Run sensitivity analysis on key CBDC parameters."""
    from cbdc_simulation import create_default_config
    
    # Create output directory
    os.makedirs("sensitivity_analysis", exist_ok=True)
    
    # Initialize scenario tester
    tester = ScenarioTester(create_default_config())
    
    # Run base scenario
    tester.run_scenario("Base", create_default_config())
    
    # Parameters to analyze
    parameters = {
        "cbdc_interest_rate": [-1.0, 0.0, 1.0, 2.0, 3.0],
        "conditional_spending_constraints": [0.0, 0.25, 0.5, 0.75, 1.0],
        "smart_contract_based_lending": [0.0, 0.25, 0.5, 0.75, 1.0],
        "foreign_exchange_controls": [0.0, 0.25, 0.5, 0.75, 1.0]
    }
    
    # Output variables to track
    output_variables = ["gdp", "inflation_rate", "unemployment_rate", "bank_deposits", "financial_stress_index"]
    
    # Run sensitivity analysis for each parameter
    for param, values in parameters.items():
        print(f"Running sensitivity analysis for {param}")
        
        figures = tester.sensitivity_analysis(param, values, output_variables)
        
        # Save figures
        for var, fig in figures.items():
            fig.savefig(f"sensitivity_analysis/{param}_{var}.png")
    
    print("Sensitivity analysis completed. Results saved to 'sensitivity_analysis' directory.")


if __name__ == "__main__":
    # Run standard scenarios
    run_standard_scenarios()
    
    # Run sensitivity analysis
    run_sensitivity_analysis()
