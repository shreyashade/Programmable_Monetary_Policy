"""
CBDC Economic Simulation - Test Runner

This module provides utilities for testing the CBDC economic simulation system
and validating its behavior under different scenarios.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Any, Optional, Tuple

# Import the simulation system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cbdc_simulation import (
    SimulationConfig, CBDCParameters, TradeParameters, 
    BankingParameters, MacroParameters, EconomicState,
    CBDCSimulation, create_default_config
)
from data_integration import WorldBankDataFetcher, DataExplainer
from scenario_testing import ScenarioTester, EnhancedCBDCSimulation

class SimulationTests(unittest.TestCase):
    """Test cases for the CBDC economic simulation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = create_default_config()
        self.simulation = CBDCSimulation(self.config)
    
    def test_simulation_runs(self):
        """Test that the simulation runs without errors."""
        results = self.simulation.run()
        self.assertIsNotNone(results)
        self.assertGreater(len(results), 0)
    
    def test_gdp_calculation(self):
        """Test that GDP is calculated correctly."""
        results = self.simulation.run()
        
        # Check that GDP is positive
        self.assertTrue(all(results["gdp"] > 0))
        
        # Check that GDP components add up
        for i, row in results.iterrows():
            if all(c in row for c in ["consumption", "investment", "government_spending", "net_exports"]):
                components_sum = row["consumption"] + row["investment"] + row["government_spending"] + row["net_exports"]
                self.assertAlmostEqual(row["gdp"], components_sum, delta=0.1)
    
    def test_inflation_unemployment_relationship(self):
        """Test the Phillips curve relationship between inflation and unemployment."""
        # Modify config to create a scenario with changing unemployment
        config = create_default_config()
        config.time_horizon = 20
        
        # Add a shock to increase unemployment
        config.shocks = {
            5: {"unemployment_rate": 2.0}  # Increase unemployment in quarter 5
        }
        
        simulation = CBDCSimulation(config)
        results = simulation.run()
        
        # Check that inflation decreases when unemployment increases
        pre_shock_inflation = results.iloc[4]["inflation_rate"]
        post_shock_inflation = results.iloc[6]["inflation_rate"]
        
        self.assertGreater(results.iloc[6]["unemployment_rate"], results.iloc[4]["unemployment_rate"])
        self.assertLess(post_shock_inflation, pre_shock_inflation)
    
    def test_cbdc_interest_rate_effect(self):
        """Test the effect of CBDC interest rate on the economy."""
        # Create two configurations with different CBDC interest rates
        config_low = create_default_config()
        config_low.cbdc_parameters.cbdc_interest_rate = 0.0
        
        config_high = create_default_config()
        config_high.cbdc_parameters.cbdc_interest_rate = 3.0
        
        # Run simulations
        sim_low = CBDCSimulation(config_low)
        results_low = sim_low.run()
        
        sim_high = CBDCSimulation(config_high)
        results_high = sim_high.run()
        
        # Higher CBDC interest rate should lead to more CBDC adoption
        self.assertGreater(
            results_high.iloc[-1]["cbdc_supply"], 
            results_low.iloc[-1]["cbdc_supply"]
        )
        
        # Higher CBDC interest rate should lead to less bank deposits
        self.assertLess(
            results_high.iloc[-1]["bank_deposits"], 
            results_low.iloc[-1]["bank_deposits"]
        )
    
    def test_data_integration(self):
        """Test the data integration functionality."""
        data_fetcher = WorldBankDataFetcher()
        
        # Test country data fetching
        country_data = data_fetcher.get_country_data("USA")
        self.assertIsNotNone(country_data)
        self.assertIn("country_name", country_data)
        self.assertEqual(country_data["country_code"], "USA")
        
        # Test conversion to simulation state
        simulation_state = data_fetcher.convert_to_simulation_state(country_data)
        self.assertIsNotNone(simulation_state)
        self.assertIn("gdp", simulation_state)
    
    def test_natural_language_explanations(self):
        """Test the natural language explanation functionality."""
        data_explainer = DataExplainer()
        
        # Test variable explanation
        explanation = data_explainer.explain_variable("inflation_rate")
        self.assertIsNotNone(explanation)
        self.assertGreater(len(explanation), 0)
        
        # Test parameter change explanation
        explanation = data_explainer.explain_parameter_change("cbdc_interest_rate", 0.0, 2.0)
        self.assertIsNotNone(explanation)
        self.assertGreater(len(explanation), 0)
        
        # Test calculation explanation
        variables = {
            "consumption": 12000,
            "investment": 4000,
            "government_spending": 3000,
            "net_exports": -500,
            "gdp": 18500
        }
        explanation = data_explainer.explain_calculation("gdp_components", variables)
        self.assertIsNotNone(explanation)
        self.assertGreater(len(explanation), 0)


class ScenarioTests(unittest.TestCase):
    """Test cases for scenario testing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tester = ScenarioTester(create_default_config())
    
    def test_scenario_comparison(self):
        """Test scenario comparison functionality."""
        # Run two scenarios
        self.tester.run_scenario("Base", create_default_config())
        
        # Create a high inflation scenario
        config = create_default_config()
        config.initial_state.inflation_rate = 5.0
        self.tester.run_scenario("High Inflation", config)
        
        # Compare scenarios
        variables = ["inflation_rate", "interest_rate"]
        figures = self.tester.compare_scenarios(["Base", "High Inflation"], variables)
        
        self.assertEqual(len(figures), len(variables))
        for var in variables:
            self.assertIn(var, figures)
    
    def test_sensitivity_analysis(self):
        """Test sensitivity analysis functionality."""
        # Run base scenario
        self.tester.run_scenario("Base", create_default_config())
        
        # Run sensitivity analysis
        parameter_values = [0.0, 1.0, 2.0]
        output_variables = ["gdp", "inflation_rate"]
        
        figures = self.tester.sensitivity_analysis(
            "cbdc_interest_rate", parameter_values, output_variables
        )
        
        self.assertEqual(len(figures), len(output_variables))
        for var in output_variables:
            self.assertIn(var, figures)
    
    def test_scenario_report(self):
        """Test scenario report generation."""
        # Run a scenario
        self.tester.run_scenario("Base", create_default_config())
        
        # Generate report
        report = self.tester.generate_scenario_report("Base")
        
        self.assertIsNotNone(report)
        self.assertGreater(len(report), 0)
        self.assertIn("# Scenario Analysis: Base", report)


class EnhancedSimulationTests(unittest.TestCase):
    """Test cases for the enhanced simulation with calculation logging."""
    
    def test_calculation_logging(self):
        """Test that calculation logging works correctly."""
        config = create_default_config()
        
        # Create a list to store logs
        logs = []
        
        # Run enhanced simulation
        simulation = EnhancedCBDCSimulation(config, logs)
        results = simulation.run()
        
        # Check that logs were generated
        self.assertGreater(len(logs), 0)
        
        # Check log content
        log_text = "\n".join(logs)
        self.assertIn("Starting equilibrium calculation", log_text)
        self.assertIn("IS-LM-BP Equations", log_text)
        self.assertIn("After state update", log_text)


def run_tests():
    """Run all tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


def run_performance_test(time_horizon=100):
    """
    Run a performance test to measure simulation speed.
    
    Args:
        time_horizon: Number of quarters to simulate
    """
    import time
    
    print(f"Running performance test with time_horizon={time_horizon}")
    
    # Create configuration
    config = create_default_config()
    config.time_horizon = time_horizon
    
    # Measure execution time
    start_time = time.time()
    
    simulation = CBDCSimulation(config)
    results = simulation.run()
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"Simulation completed in {execution_time:.2f} seconds")
    print(f"Average time per quarter: {execution_time / time_horizon:.4f} seconds")
    
    return execution_time


def validate_economic_relationships():
    """Validate key economic relationships in the simulation."""
    print("Validating economic relationships...")
    
    # Create tester
    tester = ScenarioTester(create_default_config())
    
    # Test Phillips Curve relationship
    print("\nTesting Phillips Curve relationship (inflation vs unemployment)...")
    
    # Create scenarios with different unemployment rates
    unemployment_rates = [3.0, 4.0, 5.0, 6.0, 7.0]
    
    for rate in unemployment_rates:
        config = create_default_config()
        config.initial_state.unemployment_rate = rate
        tester.run_scenario(f"Unemployment_{rate}", config)
    
    # Compare inflation rates
    scenario_names = [f"Unemployment_{rate}" for rate in unemployment_rates]
    figures = tester.compare_scenarios(scenario_names, ["inflation_rate"])
    
    # Check if inflation decreases as unemployment increases
    inflation_values = []
    for name in scenario_names:
        results = tester.scenario_results[name]
        inflation_values.append(results.iloc[-1]["inflation_rate"])
    
    print(f"Unemployment rates: {unemployment_rates}")
    print(f"Resulting inflation rates: {inflation_values}")
    
    if all(inflation_values[i] > inflation_values[i+1] for i in range(len(inflation_values)-1)):
        print("✓ Phillips Curve relationship validated: inflation decreases as unemployment increases")
    else:
        print("✗ Phillips Curve relationship not consistently observed")
    
    # Test IS curve relationship (interest rates vs output)
    print("\nTesting IS curve relationship (interest rates vs output)...")
    
    # Create scenarios with different interest rates
    interest_rates = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    for rate in interest_rates:
        config = create_default_config()
        config.initial_state.interest_rate = rate
        tester.run_scenario(f"Interest_{rate}", config)
    
    # Compare GDP
    scenario_names = [f"Interest_{rate}" for rate in interest_rates]
    figures = tester.compare_scenarios(scenario_names, ["gdp"])
    
    # Check if GDP decreases as interest rates increase
    gdp_values = []
    for name in scenario_names:
        results = tester.scenario_results[name]
        gdp_values.append(results.iloc[-1]["gdp"])
    
    print(f"Interest rates: {interest_rates}")
    print(f"Resulting GDP values: {gdp_values}")
    
    if all(gdp_values[i] > gdp_values[i+1] for i in range(len(gdp_values)-1)):
        print("✓ IS curve relationship validated: GDP decreases as interest rates increase")
    else:
        print("✗ IS curve relationship not consistently observed")
    
    # Test CBDC disintermediation effect
    print("\nTesting CBDC disintermediation effect...")
    
    # Create scenarios with different CBDC interest rates
    cbdc_rates = [0.0, 1.0, 2.0, 3.0, 4.0]
    
    for rate in cbdc_rates:
        config = create_default_config()
        config.cbdc_parameters.cbdc_interest_rate = rate
        tester.run_scenario(f"CBDC_Rate_{rate}", config)
    
    # Compare bank deposits
    scenario_names = [f"CBDC_Rate_{rate}" for rate in cbdc_rates]
    figures = tester.compare_scenarios(scenario_names, ["bank_deposits", "cbdc_supply"])
    
    # Check if bank deposits decrease and CBDC supply increases as CBDC interest rates increase
    deposits_values = []
    cbdc_values = []
    for name in scenario_names:
        results = tester.scenario_results[name]
        deposits_values.append(results.iloc[-1]["bank_deposits"])
        cbdc_values.append(results.iloc[-1]["cbdc_supply"])
    
    print(f"CBDC interest rates: {cbdc_rates}")
    print(f"Resulting bank deposits: {deposits_values}")
    print(f"Resulting CBDC supply: {cbdc_values}")
    
    if all(deposits_values[i] > deposits_values[i+1] for i in range(len(deposits_values)-1)):
        print("✓ Disintermediation effect validated: bank deposits decrease as CBDC interest rates increase")
    else:
        print("✗ Disintermediation effect not consistently observed for bank deposits")
    
    if all(cbdc_values[i] < cbdc_values[i+1] for i in range(len(cbdc_values)-1)):
        print("✓ Disintermediation effect validated: CBDC supply increases as CBDC interest rates increase")
    else:
        print("✗ Disintermediation effect not consistently observed for CBDC supply")


if __name__ == "__main__":
    # Run unit tests
    print("Running unit tests...")
    run_tests()
    
    # Run performance test
    print("\nRunning performance test...")
    run_performance_test(time_horizon=50)
    
    # Validate economic relationships
    print("\nValidating economic relationships...")
    validate_economic_relationships()
