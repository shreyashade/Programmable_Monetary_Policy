"""
CBDC Economic Simulation - Main Entry Point

This module serves as the main entry point for the enhanced CBDC economic simulation system.
It provides a command-line interface for running simulations, scenarios, and tests.
"""

import os
import sys
import argparse
import time
from typing import Dict, List, Any, Optional, Tuple

# Import simulation components
from cbdc_simulation import (
    SimulationConfig, CBDCParameters, TradeParameters, 
    BankingParameters, MacroParameters, EconomicState,
    CBDCSimulation, create_default_config,
    create_cbdc_adoption_scenario,
    create_trade_war_scenario,
    create_banking_crisis_scenario
)
from data_integration import WorldBankDataFetcher, DataExplainer
from scenario_testing import ScenarioTester, EnhancedCBDCSimulation, run_standard_scenarios, run_sensitivity_analysis
from test_runner import run_tests, run_performance_test, validate_economic_relationships


def main():
    """Main entry point for the CBDC simulation system."""
    parser = argparse.ArgumentParser(description="Enhanced CBDC Economic Simulation System")
    
    # Define command-line arguments
    parser.add_argument("--mode", type=str, default="gui", 
                        choices=["gui", "scenario", "test", "validate", "performance"],
                        help="Operation mode: gui, scenario, test, validate, or performance")
    
    parser.add_argument("--scenario", type=str, default="default",
                        choices=["default", "cbdc_adoption", "trade_war", "banking_crisis", "all"],
                        help="Predefined scenario to run")
    
    parser.add_argument("--country", type=str, default=None,
                        help="Country code for real-world data initialization (e.g., USA)")
    
    parser.add_argument("--output", type=str, default="results",
                        help="Directory to save output files")
    
    parser.add_argument("--time_horizon", type=int, default=20,
                        help="Simulation time horizon in quarters")
    
    parser.add_argument("--cbdc_interest", type=float, default=None,
                        help="CBDC interest rate (overrides scenario default)")
    
    parser.add_argument("--spending_constraints", type=float, default=None,
                        help="CBDC spending constraints (0-1, overrides scenario default)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Handle different operation modes
    if args.mode == "gui":
        # Launch the graphical user interface
        print("Launching CBDC Simulation GUI...")
        from enhanced_interface import EnhancedCBDCSimulationApp
        app = EnhancedCBDCSimulationApp()
        app.mainloop()
    
    elif args.mode == "scenario":
        # Run predefined scenarios
        print(f"Running scenario mode with scenario: {args.scenario}")
        
        if args.scenario == "all":
            # Run all standard scenarios
            run_standard_scenarios()
        else:
            # Get the appropriate scenario configuration
            if args.scenario == "default":
                config = create_default_config()
            elif args.scenario == "cbdc_adoption":
                config = create_cbdc_adoption_scenario()
            elif args.scenario == "trade_war":
                config = create_trade_war_scenario()
            elif args.scenario == "banking_crisis":
                config = create_banking_crisis_scenario()
            
            # Override time horizon if specified
            if args.time_horizon:
                config.time_horizon = args.time_horizon
            
            # Override CBDC parameters if specified
            if args.cbdc_interest is not None:
                config.cbdc_parameters.cbdc_interest_rate = args.cbdc_interest
            
            if args.spending_constraints is not None:
                config.cbdc_parameters.conditional_spending_constraints = args.spending_constraints
            
            # Initialize with real-world data if country is specified
            if args.country:
                print(f"Initializing with data from {args.country}...")
                data_fetcher = WorldBankDataFetcher()
                country_data = data_fetcher.get_country_data(args.country)
                
                if country_data:
                    simulation_state = data_fetcher.convert_to_simulation_state(country_data)
                    
                    # Update initial state
                    for key, value in simulation_state.items():
                        if hasattr(config.initial_state, key):
                            setattr(config.initial_state, key, value)
                    
                    print(f"Successfully initialized with data from {country_data.get('country_name', args.country)}")
                else:
                    print(f"Could not fetch data for country code: {args.country}")
            
            # Run the scenario
            tester = ScenarioTester()
            results = tester.run_scenario(args.scenario, config)
            
            # Generate report
            report = tester.generate_scenario_report(args.scenario)
            report_path = os.path.join(args.output, f"{args.scenario}_report.md")
            
            with open(report_path, 'w') as f:
                f.write(report)
            
            # Export data
            data_path = os.path.join(args.output, f"{args.scenario}_data.csv")
            tester.export_scenario_data(args.scenario, data_path)
            
            # Export calculation logs
            logs_path = os.path.join(args.output, f"{args.scenario}_calculations.txt")
            tester.export_calculation_logs(args.scenario, logs_path)
            
            print(f"Scenario completed. Results saved to {args.output} directory.")
    
    elif args.mode == "test":
        # Run unit tests
        print("Running unit tests...")
        run_tests()
    
    elif args.mode == "validate":
        # Validate economic relationships
        print("Validating economic relationships...")
        validate_economic_relationships()
    
    elif args.mode == "performance":
        # Run performance test
        print(f"Running performance test with time horizon: {args.time_horizon}")
        run_performance_test(args.time_horizon)


if __name__ == "__main__":
    main()
