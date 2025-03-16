"""
CBDC Economic Simulation System

This module implements a comprehensive economic simulation for a national economy
that has adopted Central Bank Digital Currency (CBDC) and programmable monetary policy.
The simulation models macroeconomic dynamics, sectoral interactions, international trade,
and the impacts of CBDC-enabled policy controls.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
import networkx as nx
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Callable, Optional, Union, Any
import json
import os
import time
from enum import Enum, auto

# =============================================================================
# Core Data Structures
# =============================================================================

class PolicyType(Enum):
    """Types of economic policies that can be implemented."""
    MONETARY = auto()
    FISCAL = auto()
    TRADE = auto()
    MACROPRUDENTIAL = auto()
    CAPITAL_CONTROL = auto()
    CBDC_SPECIFIC = auto()

@dataclass
class EconomicState:
    """Container for all economic state variables at a point in time."""
    # Macroeconomic indicators
    gdp: float = 0.0
    potential_gdp: float = 0.0
    inflation_rate: float = 0.0
    unemployment_rate: float = 0.0
    interest_rate: float = 0.0
    policy_rate: float = 0.0
    exchange_rate: float = 1.0
    
    # Fiscal variables
    government_spending: float = 0.0
    tax_revenue: float = 0.0
    government_debt: float = 0.0
    budget_deficit: float = 0.0
    
    # Monetary variables
    money_supply: float = 0.0
    cbdc_supply: float = 0.0
    bank_reserves: float = 0.0
    
    # Sectoral variables
    consumption: float = 0.0
    investment: float = 0.0
    net_exports: float = 0.0
    
    # International variables
    exports: float = 0.0
    imports: float = 0.0
    current_account: float = 0.0
    capital_account: float = 0.0
    foreign_reserves: float = 0.0
    
    # Banking sector
    bank_loans: float = 0.0
    bank_deposits: float = 0.0
    interbank_rate: float = 0.0
    loan_interest_rate: float = 0.0
    deposit_interest_rate: float = 0.0
    
    # Price variables
    price_level: float = 1.0
    wage_level: float = 1.0
    asset_prices: float = 1.0
    
    # Expectation variables
    inflation_expectations: float = 0.0
    growth_expectations: float = 0.0
    
    # Financial stability indicators
    financial_stress_index: float = 0.0
    systemic_risk_indicator: float = 0.0
    
    # Additional state variables can be added as dictionary
    additional_variables: Dict[str, float] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, float]:
        """Convert state to dictionary, excluding the additional_variables field."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if field_name != 'additional_variables' and not callable(field_value):
                result[field_name] = field_value
        
        # Add additional variables
        result.update(self.additional_variables)
        return result
    
    def as_array(self, variables: List[str]) -> np.ndarray:
        """Extract specified variables as numpy array."""
        state_dict = self.as_dict()
        return np.array([state_dict.get(var, 0.0) for var in variables])

@dataclass
class CBDCParameters:
    """Parameters controlling CBDC features and programmable monetary policy."""
    # Basic CBDC parameters
    cbdc_interest_rate: float = 0.0
    tiered_interest_rates: Dict[str, float] = field(default_factory=dict)
    programmable_money_validity: int = 365  # days
    
    # Spending controls
    conditional_spending_constraints: float = 0.0  # 0-1 scale
    sectoral_spending_limits: Dict[str, float] = field(default_factory=dict)
    geographical_spending_limits: Dict[str, float] = field(default_factory=dict)
    
    # Fiscal integration
    automatic_fiscal_transfers: float = 0.0
    dynamic_taxation_policies: float = 0.0
    
    # Financial system controls
    smart_contract_based_lending: float = 0.0
    foreign_exchange_controls: float = 0.0
    capital_controls: float = 0.0
    
    # Behavioral and regulatory
    behavioral_economics_incentives: float = 0.0
    automated_compliance_reporting: float = 0.0
    privacy_settings: float = 1.0
    
    # Stability tools
    macroprudential_tools: float = 0.0
    emergency_override_mechanisms: float = 0.0
    
    # Financial instruments
    inflation_indexed_instruments: float = 0.0
    programmable_asset_purchases: float = 0.0
    cbdc_derivatives: float = 0.0
    
    # Integration
    interoperability_protocols: float = 1.0
    
    # Additional parameters can be added as dictionary
    additional_parameters: Dict[str, float] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary, excluding the additional_parameters field."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if field_name != 'additional_parameters' and not callable(field_value):
                result[field_name] = field_value
        
        # Add additional parameters
        result.update(self.additional_parameters)
        return result

@dataclass
class TradeParameters:
    """Parameters controlling international trade and tariffs."""
    # Basic trade parameters
    tariff_rate: float = 0.0
    non_tariff_barriers: float = 0.0
    customs_efficiency: float = 1.0
    
    # Trade agreements
    free_trade_agreements: Dict[str, float] = field(default_factory=dict)
    preferential_tariffs: Dict[str, float] = field(default_factory=dict)
    
    # Exchange rate regime
    exchange_rate_regime: str = "floating"  # floating, managed, fixed
    exchange_rate_target: float = 1.0
    intervention_threshold: float = 0.1
    
    # Capital flow management
    capital_flow_controls: float = 0.0
    foreign_investment_restrictions: float = 0.0
    
    # Trade composition
    export_promotion: Dict[str, float] = field(default_factory=dict)
    import_substitution: Dict[str, float] = field(default_factory=dict)
    
    # CBDC trade features
    cbdc_trade_settlement: float = 0.0
    cross_border_cbdc_limits: float = 0.0
    
    # Additional parameters can be added as dictionary
    additional_parameters: Dict[str, float] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary, excluding the additional_parameters field."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if field_name != 'additional_parameters' and not callable(field_value):
                result[field_name] = field_value
        
        # Add additional parameters
        result.update(self.additional_parameters)
        return result

@dataclass
class BankingParameters:
    """Parameters controlling the banking sector and financial system."""
    # Regulatory parameters
    capital_requirement: float = 0.08
    reserve_requirement: float = 0.02
    liquidity_coverage_ratio: float = 1.0
    
    # Banking behavior
    lending_risk_appetite: float = 0.5
    interbank_market_activity: float = 1.0
    
    # Central bank operations
    discount_rate: float = 0.05
    standing_facility_spread: float = 0.01
    quantitative_easing: float = 0.0
    
    # Financial market parameters
    market_liquidity: float = 1.0
    risk_premium: float = 0.02
    term_premium: float = 0.01
    
    # CBDC banking impacts
    cbdc_disintermediation_factor: float = 0.0
    bank_cbdc_distribution_role: float = 1.0
    
    # Financial stability tools
    countercyclical_buffer: float = 0.0
    systemic_risk_charge: float = 0.0
    
    # Additional parameters can be added as dictionary
    additional_parameters: Dict[str, float] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary, excluding the additional_parameters field."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if field_name != 'additional_parameters' and not callable(field_value):
                result[field_name] = field_value
        
        # Add additional parameters
        result.update(self.additional_parameters)
        return result

@dataclass
class MacroParameters:
    """Basic macroeconomic parameters for the simulation."""
    # IS-LM parameters
    autonomous_consumption: float = 1500.0
    marginal_propensity_to_consume: float = 0.6
    autonomous_investment: float = 2000.0
    investment_interest_sensitivity: float = 100.0
    money_demand_income_sensitivity: float = 0.2
    money_demand_interest_sensitivity: float = 50.0
    
    # Phillips curve and Okun's law
    phillips_curve_sensitivity: float = 0.5
    okun_law_coefficient: float = 0.5
    
    # Growth model parameters
    productivity_growth: float = 0.02
    capital_depreciation: float = 0.1
    capital_output_ratio: float = 3.0
    
    # International parameters
    export_income_elasticity: float = 1.0
    import_income_elasticity: float = 1.0
    export_price_elasticity: float = 1.5
    import_price_elasticity: float = 1.5
    
    # Policy rule parameters
    taylor_rule_inflation: float = 1.5
    taylor_rule_output: float = 0.5
    
    # Structural parameters
    natural_unemployment: float = 4.0
    potential_output_growth: float = 0.025
    neutral_interest_rate: float = 2.5
    
    # Expectation formation
    adaptive_expectations_weight: float = 0.7
    
    # Additional parameters can be added as dictionary
    additional_parameters: Dict[str, float] = field(default_factory=dict)
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary, excluding the additional_parameters field."""
        result = {}
        for field_name, field_value in self.__dict__.items():
            if field_name != 'additional_parameters' and not callable(field_value):
                result[field_name] = field_value
        
        # Add additional parameters
        result.update(self.additional_parameters)
        return result

@dataclass
class SimulationConfig:
    """Configuration for the simulation run."""
    # Time parameters
    time_horizon: int = 20  # quarters
    start_date: str = "2025-01-01"
    
    # Initial conditions
    initial_state: EconomicState = field(default_factory=EconomicState)
    
    # Parameter sets
    macro_parameters: MacroParameters = field(default_factory=MacroParameters)
    cbdc_parameters: CBDCParameters = field(default_factory=CBDCParameters)
    trade_parameters: TradeParameters = field(default_factory=TradeParameters)
    banking_parameters: BankingParameters = field(default_factory=BankingParameters)
    
    # Shock scenarios
    shocks: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    # Policy interventions
    policy_changes: Dict[int, Dict[str, float]] = field(default_factory=dict)
    
    # Random seed for stochastic components
    random_seed: int = 42
    
    # Output configuration
    output_variables: List[str] = field(default_factory=list)
    save_frequency: int = 1
    
    def to_json(self, filepath: str) -> None:
        """Save configuration to JSON file."""
        config_dict = {
            "time_horizon": self.time_horizon,
            "start_date": self.start_date,
            "initial_state": self.initial_state.as_dict(),
            "macro_parameters": self.macro_parameters.as_dict(),
            "cbdc_parameters": self.cbdc_parameters.as_dict(),
            "trade_parameters": self.trade_parameters.as_dict(),
            "banking_parameters": self.banking_parameters.as_dict(),
            "shocks": self.shocks,
            "policy_changes": self.policy_changes,
            "random_seed": self.random_seed,
            "output_variables": self.output_variables,
            "save_frequency": self.save_frequency
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def from_json(cls, filepath: str) -> 'SimulationConfig':
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        # Create basic config
        config = cls(
            time_horizon=config_dict.get("time_horizon", 20),
            start_date=config_dict.get("start_date", "2025-01-01"),
            random_seed=config_dict.get("random_seed", 42),
            output_variables=config_dict.get("output_variables", []),
            save_frequency=config_dict.get("save_frequency", 1)
        )
        
        # Load initial state
        if "initial_state" in config_dict:
            state_dict = config_dict["initial_state"]
            # Extract known fields
            known_fields = {k: v for k, v in state_dict.items() 
                           if k in EconomicState.__annotations__}
            # Extract additional fields
            additional = {k: v for k, v in state_dict.items() 
                         if k not in EconomicState.__annotations__}
            # Create state
            state = EconomicState(**known_fields)
            state.additional_variables = additional
            config.initial_state = state
        
        # Load parameter sets using similar pattern
        if "macro_parameters" in config_dict:
            config.macro_parameters = cls._load_parameters(
                MacroParameters, config_dict["macro_parameters"])
        
        if "cbdc_parameters" in config_dict:
            config.cbdc_parameters = cls._load_parameters(
                CBDCParameters, config_dict["cbdc_parameters"])
        
        if "trade_parameters" in config_dict:
            config.trade_parameters = cls._load_parameters(
                TradeParameters, config_dict["trade_parameters"])
        
        if "banking_parameters" in config_dict:
            config.banking_parameters = cls._load_parameters(
                BankingParameters, config_dict["banking_parameters"])
        
        # Load shocks and policy changes
        if "shocks" in config_dict:
            # Convert string keys (JSON limitation) back to integers
            config.shocks = {int(k): v for k, v in config_dict["shocks"].items()}
        
        if "policy_changes" in config_dict:
            # Convert string keys (JSON limitation) back to integers
            config.policy_changes = {int(k): v for k, v in config_dict["policy_changes"].items()}
        
        return config
    
    @staticmethod
    def _load_parameters(param_class, param_dict):
        """Helper to load parameters from dictionary into dataclass."""
        # Extract known fields
        known_fields = {k: v for k, v in param_dict.items() 
                       if k in param_class.__annotations__}
        # Extract additional fields
        additional = {k: v for k, v in param_dict.items() 
                     if k not in param_class.__annotations__}
        # Create parameters
        params = param_class(**known_fields)
        params.additional_parameters = additional
        return params

# =============================================================================
# Economic Model Components
# =============================================================================

class EconomicModel:
    """Core economic model implementing the enhanced IS-LM-BP framework with CBDC features."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize the economic model with configuration."""
        self.config = config
        self.current_state = config.initial_state
        self.macro_params = config.macro_parameters
        self.cbdc_params = config.cbdc_parameters
        self.trade_params = config.trade_parameters
        self.banking_params = config.banking_parameters
        
        # Initialize history storage
        self.history = []
        self.save_state()  # Save initial state
    
    def save_state(self) -> None:
        """Save current state to history."""
        self.history.append(self.current_state.as_dict())
    
    def step(self, t: int) -> None:
        """Advance the model by one time step."""
        # Apply any shocks scheduled for this time step
        self._apply_shocks(t)
        
        # Apply any policy changes scheduled for this time step
        self._apply_policy_changes(t)
        
        # Solve for equilibrium in this period
        self._solve_equilibrium()
        
        # Update state variables based on equilibrium
        self._update_state_variables()
        
        # Save the new state
        self.save_state()
    
    def _apply_shocks(self, t: int) -> None:
        """Apply any shocks scheduled for the current time step."""
        if t in self.config.shocks:
            shock_dict = self.config.shocks[t]
            for var_name, shock_value in shock_dict.items():
                # Apply shock to state variable if it exists
                if hasattr(self.current_state, var_name):
                    setattr(self.current_state, var_name, 
                            getattr(self.current_state, var_name) + shock_value)
                # Otherwise, check if it's in additional_variables
                elif var_name in self.current_state.additional_variables:
                    self.current_state.additional_variables[var_name] += shock_value
                # Or it might be a parameter
                elif hasattr(self.macro_params, var_name):
                    setattr(self.macro_params, var_name, 
                            getattr(self.macro_params, var_name) + shock_value)
                elif hasattr(self.cbdc_params, var_name):
                    setattr(self.cbdc_params, var_name, 
                            getattr(self.cbdc_params, var_name) + shock_value)
                elif hasattr(self.trade_params, var_name):
                    setattr(self.trade_params, var_name, 
                            getattr(self.trade_params, var_name) + shock_value)
                elif hasattr(self.banking_params, var_name):
                    setattr(self.banking_params, var_name, 
                            getattr(self.banking_params, var_name) + shock_value)
    
    def _apply_policy_changes(self, t: int) -> None:
        """Apply any policy changes scheduled for the current time step."""
        if t in self.config.policy_changes:
            policy_dict = self.config.policy_changes[t]
            for var_name, new_value in policy_dict.items():
                # Apply policy change to parameter if it exists
                if hasattr(self.macro_params, var_name):
                    setattr(self.macro_params, var_name, new_value)
                elif hasattr(self.cbdc_params, var_name):
                    setattr(self.cbdc_params, var_name, new_value)
                elif hasattr(self.trade_params, var_name):
                    setattr(self.trade_params, var_name, new_value)
                elif hasattr(self.banking_params, var_name):
                    setattr(self.banking_params, var_name, new_value)
    
    def _solve_equilibrium(self) -> None:
        """Solve for economic equilibrium in the current period."""
        # Initial guess based on previous state
        initial_guess = [
            self.current_state.gdp,
            self.current_state.interest_rate,
            self.current_state.exchange_rate,
            self.current_state.price_level
        ]
        
        # Solve system of equations
        try:
            solution = fsolve(self._equilibrium_equations, initial_guess)
            
            # Extract solution components
            gdp, interest_rate, exchange_rate, price_level = solution
            
            # Update state with solution
            self.current_state.gdp = gdp
            self.current_state.interest_rate = interest_rate
            self.current_state.exchange_rate = exchange_rate
            self.current_state.price_level = price_level
            
        except Exception as e:
            print(f"Error solving equilibrium: {e}")
            # Fallback: simple update based on previous values
            self.current_state.gdp *= (1 + 0.005)  # Small growth
            self.current_state.price_level *= (1 + 0.005)  # Small inflation
    
    def _equilibrium_equations(self, vars) -> np.ndarray:
        """System of equations that must be satisfied in equilibrium."""
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
        
        return np.array([goods_market, money_market, forex_market, price_adjustment])
    
    def _update_state_variables(self) -> None:
        """Update all state variables based on the current equilibrium."""
        # Extract current equilibrium values
        Y = self.current_state.gdp
        r = self.current_state.interest_rate
        e = self.current_state.exchange_rate
        P = self.current_state.price_level
        
        # Calculate unemployment using Okun's Law
        output_gap = (Y - self.current_state.potential_gdp) / self.current_state.potential_gdp
        u = self.macro_params.natural_unemployment - self.macro_params.okun_law_coefficient * output_gap * 100
        self.current_state.unemployment_rate = max(0, u)  # Ensure non-negative
        
        # Calculate inflation using Phillips Curve
        prev_inflation = self.current_state.inflation_rate
        inflation_expectation = self.current_state.inflation_expectations
        inflation_adjustment = -self.macro_params.phillips_curve_sensitivity * (u - self.macro_params.natural_unemployment)
        inflation = prev_inflation * 0.5 + inflation_expectation * 0.5 + inflation_adjustment
        inflation -= self.cbdc_params.inflation_indexed_instruments * 0.1  # CBDC effect
        self.current_state.inflation_rate = inflation
        
        # Update inflation expectations (adaptive)
        self.current_state.inflation_expectations = (
            self.macro_params.adaptive_expectations_weight * prev_inflation + 
            (1 - self.macro_params.adaptive_expectations_weight) * inflation
        )
        
        # Calculate policy rate using Taylor Rule
        inflation_gap = inflation - 2.0  # Assuming 2% target
        output_gap_percent = output_gap * 100
        policy_rate = (
            self.macro_params.neutral_interest_rate + 
            self.macro_params.taylor_rule_inflation * inflation_gap + 
            self.macro_params.taylor_rule_output * output_gap_percent +
            self.cbdc_params.emergency_override_mechanisms
        )
        self.current_state.policy_rate = max(0, policy_rate)  # Zero lower bound
        
        # Update banking sector variables
        self.current_state.loan_interest_rate = self.current_state.policy_rate + 2.0
        self.current_state.deposit_interest_rate = self.current_state.policy_rate - 1.0
        self.current_state.interbank_rate = self.current_state.policy_rate + 0.1
        
        # Calculate banking disintermediation from CBDC
        disintermediation = self.cbdc_params.cbdc_interest_rate * self.banking_params.cbdc_disintermediation_factor
        self.current_state.bank_deposits = self.current_state.bank_deposits * (1 - disintermediation)
        
        # Update international variables
        self.current_state.exports = 0.2 * Y * e  # Simple export function
        self.current_state.imports = 0.25 * Y / e  # Simple import function
        
        # Apply tariff effects
        tariff_effect = self.trade_params.tariff_rate * self.current_state.imports
        self.current_state.imports *= (1 - self.trade_params.tariff_rate * 0.5)  # Reduced imports due to tariffs
        self.current_state.tax_revenue += tariff_effect  # Tariff revenue
        
        # Update net exports
        self.current_state.net_exports = self.current_state.exports - self.current_state.imports
        
        # Update current account and capital account
        self.current_state.current_account = self.current_state.net_exports
        self.current_state.capital_account = -self.current_state.current_account  # Simplified balance
        
        # Update sectoral variables
        C0 = self.macro_params.autonomous_consumption
        c = self.macro_params.marginal_propensity_to_consume
        spending_constraint = self.cbdc_params.conditional_spending_constraints
        self.current_state.consumption = C0 + c * (Y - self.current_state.tax_revenue) * (1 - spending_constraint)
        
        I0 = self.macro_params.autonomous_investment
        b = self.macro_params.investment_interest_sensitivity
        smart_lending = self.cbdc_params.smart_contract_based_lending
        self.current_state.investment = I0 - b * r + smart_lending * 100
        
        # Update financial stability indicators
        # Simple model: higher debt, unemployment, and inflation increase stress
        self.current_state.financial_stress_index = (
            0.3 * (self.current_state.government_debt / Y) + 
            0.3 * (self.current_state.unemployment_rate / 10) + 
            0.4 * (abs(self.current_state.inflation_rate - 2) / 2)
        )
        
        # Update potential GDP (simple growth model)
        self.current_state.potential_gdp *= (1 + self.macro_params.potential_output_growth / 4)  # Quarterly growth
        
        # Update government debt based on deficit
        self.current_state.budget_deficit = self.current_state.government_spending - self.current_state.tax_revenue
        self.current_state.government_debt += self.current_state.budget_deficit
        
        # Update CBDC supply based on policy
        cbdc_growth = self.cbdc_params.programmable_asset_purchases / 1000
        self.current_state.cbdc_supply *= (1 + cbdc_growth)
        
        # Update money supply (including CBDC effects)
        self.current_state.money_supply = (
            self.current_state.bank_deposits * (1 - self.banking_params.reserve_requirement) + 
            self.current_state.cbdc_supply
        )
        
        # Update growth expectations
        prev_growth = self.current_state.growth_expectations
        actual_growth = Y / self.history[-1]["gdp"] - 1 if len(self.history) > 0 else 0
        self.current_state.growth_expectations = (
            self.macro_params.adaptive_expectations_weight * prev_growth + 
            (1 - self.macro_params.adaptive_expectations_weight) * actual_growth
        )

# =============================================================================
# CBDC System Components
# =============================================================================

class CBDCSystem:
    """Models the CBDC system and its programmable monetary policy features."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize the CBDC system with configuration."""
        self.config = config
        self.cbdc_params = config.cbdc_parameters
        self.current_state = config.initial_state
        
        # Initialize CBDC transaction network
        self.transaction_network = nx.DiGraph()
        
        # Initialize smart contracts
        self.active_contracts = []
    
    def update(self, state: EconomicState) -> None:
        """Update the CBDC system based on the current economic state."""
        self.current_state = state
        
        # Apply programmable money features
        self._apply_validity_periods()
        self._apply_conditional_spending()
        self._apply_tiered_interest()
        self._apply_automatic_transfers()
        self._execute_smart_contracts()
    
    def _apply_validity_periods(self) -> None:
        """Apply expiration to CBDC based on validity period."""
        # Simplified model: shorter validity periods increase velocity
        validity_days = self.cbdc_params.programmable_money_validity
        if validity_days < 365:
            # Increase effective money supply due to higher velocity
            velocity_multiplier = 365 / max(30, validity_days)  # Cap at 30 days minimum
            effective_increase = (velocity_multiplier - 1) * 0.1  # Scale effect
            self.current_state.additional_variables["money_velocity"] = 1 + effective_increase
        else:
            self.current_state.additional_variables["money_velocity"] = 1.0
    
    def _apply_conditional_spending(self) -> None:
        """Apply spending constraints to consumption."""
        # Effect already modeled in consumption function
        constraint_level = self.cbdc_params.conditional_spending_constraints
        
        # Track constrained vs unconstrained spending
        total_consumption = self.current_state.consumption
        constrained_consumption = total_consumption * constraint_level
        
        self.current_state.additional_variables["constrained_consumption"] = constrained_consumption
        self.current_state.additional_variables["unconstrained_consumption"] = total_consumption - constrained_consumption
    
    def _apply_tiered_interest(self) -> None:
        """Apply tiered interest rates to different CBDC holdings."""
        # Simplified model: calculate weighted average CBDC interest rate
        base_rate = self.cbdc_params.cbdc_interest_rate
        tier_adjustment = self.cbdc_params.tiered_interest_rates.get("tier1", 0.0)
        
        # Assume distribution across tiers
        weighted_rate = base_rate + tier_adjustment * 0.5
        self.current_state.additional_variables["effective_cbdc_rate"] = weighted_rate
    
    def _apply_automatic_transfers(self) -> None:
        """Apply automatic fiscal transfers through CBDC."""
        transfer_amount = self.cbdc_params.automatic_fiscal_transfers
        
        # Effect on government spending and household income
        self.current_state.government_spending += transfer_amount
        # Consumption effect already included in the model
        
        # Track transfers
        self.current_state.additional_variables["fiscal_transfers"] = transfer_amount
    
    def _execute_smart_contracts(self) -> None:
        """Execute any active smart contracts based on economic conditions."""
        # Example: Smart contract for counter-cyclical lending
        if self.cbdc_params.smart_contract_based_lending > 0:
            unemployment = self.current_state.unemployment_rate
            natural_rate = self.config.macro_parameters.natural_unemployment
            
            if unemployment > natural_rate:
                # Unemployment above natural rate triggers additional lending
                lending_boost = (unemployment - natural_rate) * self.cbdc_params.smart_contract_based_lending * 10
                self.current_state.additional_variables["smart_contract_lending"] = lending_boost
            else:
                self.current_state.additional_variables["smart_contract_lending"] = 0.0

# =============================================================================
# International Trade Components
# =============================================================================

class TradeSystem:
    """Models international trade, tariffs, and cross-border CBDC interactions."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize the trade system with configuration."""
        self.config = config
        self.trade_params = config.trade_parameters
        self.current_state = config.initial_state
        
        # Initialize trade network
        self.trade_network = nx.DiGraph()
        self._initialize_trade_network()
    
    def _initialize_trade_network(self) -> None:
        """Set up the initial trade network structure."""
        # Simplified model with a few major trading partners
        partners = ["USA", "EU", "China", "Japan", "UK"]
        
        # Add nodes for home country and partners
        self.trade_network.add_node("Home", gdp=self.current_state.gdp)
        for partner in partners:
            # Random GDP values for partners
            partner_gdp = np.random.uniform(0.5, 2.0) * self.current_state.gdp
            self.trade_network.add_node(partner, gdp=partner_gdp)
            
            # Add trade flows in both directions
            export_value = np.random.uniform(0.05, 0.15) * self.current_state.gdp
            import_value = np.random.uniform(0.05, 0.15) * self.current_state.gdp
            
            self.trade_network.add_edge("Home", partner, value=export_value, type="export")
            self.trade_network.add_edge(partner, "Home", value=import_value, type="import")
    
    def update(self, state: EconomicState) -> None:
        """Update the trade system based on the current economic state."""
        self.current_state = state
        
        # Update trade flows
        self._update_trade_flows()
        
        # Apply tariffs and trade policies
        self._apply_tariffs()
        
        # Update exchange rate based on regime
        self._update_exchange_rate()
        
        # Apply CBDC cross-border effects
        self._apply_cbdc_trade_effects()
    
    def _update_trade_flows(self) -> None:
        """Update bilateral trade flows based on economic conditions."""
        home_gdp = self.current_state.gdp
        exchange_rate = self.current_state.exchange_rate
        
        # Update node attribute
        self.trade_network.nodes["Home"]["gdp"] = home_gdp
        
        # Update all trade flows
        for u, v, data in list(self.trade_network.edges(data=True)):
            if u == "Home":  # Exports
                # Gravity model: exports depend on foreign GDP and exchange rate
                partner_gdp = self.trade_network.nodes[v]["gdp"]
                
                # Simple export function
                new_value = (
                    data["value"] * 
                    (1 + 0.8 * (partner_gdp / self.trade_network.nodes[v].get("prev_gdp", partner_gdp) - 1)) *  # Foreign growth effect
                    (1 + 0.5 * (1 - exchange_rate/self.current_state.additional_variables.get("prev_exchange_rate", 1.0)))  # Exchange rate effect
                )
                
                # Update edge
                self.trade_network.edges[u, v]["value"] = new_value
                
            elif v == "Home":  # Imports
                # Gravity model: imports depend on home GDP and exchange rate
                partner_gdp = self.trade_network.nodes[u]["gdp"]
                
                # Simple import function
                new_value = (
                    data["value"] * 
                    (1 + 0.8 * (home_gdp / self.current_state.additional_variables.get("prev_gdp", home_gdp) - 1)) *  # Domestic growth effect
                    (1 + 0.5 * (exchange_rate/self.current_state.additional_variables.get("prev_exchange_rate", 1.0) - 1))  # Exchange rate effect
                )
                
                # Apply tariff effect
                tariff_effect = 1 - self.trade_params.tariff_rate * 0.5
                new_value *= tariff_effect
                
                # Update edge
                self.trade_network.edges[u, v]["value"] = new_value
        
        # Store current values for next iteration
        for node in self.trade_network.nodes:
            self.trade_network.nodes[node]["prev_gdp"] = self.trade_network.nodes[node]["gdp"]
        
        self.current_state.additional_variables["prev_gdp"] = home_gdp
        self.current_state.additional_variables["prev_exchange_rate"] = exchange_rate
        
        # Calculate total exports and imports
        total_exports = sum(data["value"] for u, v, data in self.trade_network.edges(data=True) 
                           if u == "Home" and data["type"] == "export")
        total_imports = sum(data["value"] for u, v, data in self.trade_network.edges(data=True) 
                           if v == "Home" and data["type"] == "import")
        
        # Update state
        self.current_state.exports = total_exports
        self.current_state.imports = total_imports
        self.current_state.net_exports = total_exports - total_imports
    
    def _apply_tariffs(self) -> None:
        """Apply tariffs and calculate their effects."""
        tariff_rate = self.trade_params.tariff_rate
        imports = self.current_state.imports
        
        # Calculate tariff revenue
        tariff_revenue = tariff_rate * imports
        
        # Add to government revenue
        self.current_state.tax_revenue += tariff_revenue
        
        # Track tariff effects
        self.current_state.additional_variables["tariff_revenue"] = tariff_revenue
        self.current_state.additional_variables["effective_tariff_rate"] = tariff_rate
    
    def _update_exchange_rate(self) -> None:
        """Update exchange rate based on regime and economic factors."""
        regime = self.trade_params.exchange_rate_regime
        current_rate = self.current_state.exchange_rate
        
        if regime == "fixed":
            # Fixed exchange rate: maintain target
            target_rate = self.trade_params.exchange_rate_target
            self.current_state.exchange_rate = target_rate
            
            # Calculate intervention needed
            intervention_amount = abs(current_rate - target_rate) * 1000
            self.current_state.foreign_reserves -= intervention_amount
            
        elif regime == "managed":
            # Managed float: allow movement within bands
            target_rate = self.trade_params.exchange_rate_target
            threshold = self.trade_params.intervention_threshold
            
            # Calculate market pressure
            interest_differential = self.current_state.interest_rate - 2.0  # Assuming foreign rate is 2%
            trade_balance = self.current_state.net_exports / self.current_state.gdp
            
            # Market-based exchange rate movement
            market_rate = current_rate * (1 - 0.2 * interest_differential + 0.3 * trade_balance)
            
            # Check if intervention needed
            if abs(market_rate - target_rate) > threshold:
                # Intervene to keep within threshold
                direction = 1 if market_rate > target_rate else -1
                intervention_rate = target_rate + direction * threshold
                self.current_state.exchange_rate = intervention_rate
                
                # Calculate intervention amount
                intervention_amount = abs(market_rate - intervention_rate) * 500
                self.current_state.foreign_reserves -= intervention_amount
            else:
                # Allow market movement
                self.current_state.exchange_rate = market_rate
        
        else:  # floating
            # Floating exchange rate: determined by market forces
            interest_differential = self.current_state.interest_rate - 2.0  # Assuming foreign rate is 2%
            trade_balance = self.current_state.net_exports / self.current_state.gdp
            
            # Update exchange rate based on interest rates and trade balance
            new_rate = current_rate * (1 - 0.2 * interest_differential + 0.3 * trade_balance)
            
            # Apply capital controls if active
            if self.trade_params.capital_flow_controls > 0:
                # Dampen exchange rate movements
                dampening = self.trade_params.capital_flow_controls
                new_rate = current_rate * (1 - dampening) + new_rate * dampening
            
            self.current_state.exchange_rate = new_rate
    
    def _apply_cbdc_trade_effects(self) -> None:
        """Apply CBDC effects on international trade and capital flows."""
        cbdc_settlement = self.trade_params.cbdc_trade_settlement
        cross_border_limits = self.trade_params.cross_border_cbdc_limits
        
        if cbdc_settlement > 0:
            # CBDC settlement reduces transaction costs
            transaction_cost_reduction = cbdc_settlement * 0.05
            
            # Boost trade due to lower costs
            trade_boost = transaction_cost_reduction * 0.2
            self.current_state.exports *= (1 + trade_boost)
            self.current_state.imports *= (1 + trade_boost)
            
            # Track effect
            self.current_state.additional_variables["cbdc_trade_efficiency"] = transaction_cost_reduction
        
        if cross_border_limits > 0:
            # Restrictions on cross-border CBDC flows
            capital_flow_reduction = cross_border_limits * 0.1
            
            # Reduce capital account volatility
            self.current_state.capital_account *= (1 - capital_flow_reduction)
            
            # Track effect
            self.current_state.additional_variables["capital_flow_restriction"] = capital_flow_reduction

# =============================================================================
# Banking Sector Components
# =============================================================================

class BankingSystem:
    """Models the banking sector, financial system, and CBDC interactions."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize the banking system with configuration."""
        self.config = config
        self.banking_params = config.banking_parameters
        self.cbdc_params = config.cbdc_parameters
        self.current_state = config.initial_state
        
        # Initialize banking network
        self.banking_network = nx.DiGraph()
        self._initialize_banking_network()
        
        # Initialize initial balance sheets
        self._initialize_balance_sheets()
    
    def _initialize_banking_network(self) -> None:
        """Set up the initial banking network structure."""
        # Simplified model with central bank and commercial banks
        self.banking_network.add_node("Central_Bank", type="central_bank")
        
        # Add commercial banks of different sizes
        bank_sizes = {"Large_Bank_1": 0.3, "Large_Bank_2": 0.25, 
                     "Medium_Bank_1": 0.15, "Medium_Bank_2": 0.15,
                     "Small_Bank_1": 0.1, "Small_Bank_2": 0.05}
        
        for bank, size in bank_sizes.items():
            self.banking_network.add_node(bank, type="commercial_bank", size=size)
            
            # Add connections to central bank
            self.banking_network.add_edge("Central_Bank", bank, type="reserves")
            self.banking_network.add_edge(bank, "Central_Bank", type="borrowing")
            
            # Add interbank connections
            for other_bank in self.banking_network.nodes():
                if other_bank != bank and other_bank != "Central_Bank":
                    # Random interbank exposure
                    exposure = np.random.uniform(0, 0.1) * size
                    self.banking_network.add_edge(bank, other_bank, type="interbank", value=exposure)
    
    def _initialize_balance_sheets(self) -> None:
        """Initialize balance sheets for the banking system."""
        # Total banking system assets as percentage of GDP
        banking_assets_to_gdp = 2.0
        total_banking_assets = self.current_state.gdp * banking_assets_to_gdp
        
        # Aggregate balance sheet
        total_loans = total_banking_assets * 0.6
        total_securities = total_banking_assets * 0.2
        total_reserves = total_banking_assets * 0.1
        total_other_assets = total_banking_assets * 0.1
        
        total_deposits = total_banking_assets * 0.7
        total_borrowings = total_banking_assets * 0.2
        total_equity = total_banking_assets * 0.1
        
        # Set initial state
        self.current_state.bank_loans = total_loans
        self.current_state.bank_deposits = total_deposits
        self.current_state.bank_reserves = total_reserves
        
        # Store additional variables
        self.current_state.additional_variables["bank_securities"] = total_securities
        self.current_state.additional_variables["bank_other_assets"] = total_other_assets
        self.current_state.additional_variables["bank_borrowings"] = total_borrowings
        self.current_state.additional_variables["bank_equity"] = total_equity
    
    def update(self, state: EconomicState) -> None:
        """Update the banking system based on the current economic state."""
        self.current_state = state
        
        # Update balance sheets
        self._update_balance_sheets()
        
        # Apply regulatory requirements
        self._apply_regulations()
        
        # Process central bank operations
        self._central_bank_operations()
        
        # Calculate financial stability indicators
        self._calculate_stability_indicators()
        
        # Apply CBDC banking effects
        self._apply_cbdc_banking_effects()
    
    def _update_balance_sheets(self) -> None:
        """Update bank balance sheets based on economic conditions."""
        # Loan growth based on economic activity and interest rates
        gdp_growth = self.current_state.gdp / self.current_state.additional_variables.get("prev_gdp", self.current_state.gdp) - 1
        interest_effect = -0.2 * (self.current_state.loan_interest_rate - self.current_state.additional_variables.get("prev_loan_rate", self.current_state.loan_interest_rate))
        
        loan_growth = 0.5 * gdp_growth + interest_effect + 0.005  # Base quarterly growth
        loan_growth *= self.banking_params.lending_risk_appetite  # Risk appetite effect
        
        # Update loans
        self.current_state.bank_loans *= (1 + loan_growth)
        
        # Deposit growth based on economic activity and interest rates
        deposit_growth = 0.3 * gdp_growth + 0.1 * (self.current_state.deposit_interest_rate - 1.0) + 0.004  # Base quarterly growth
        
        # CBDC competition effect
        cbdc_effect = -0.1 * max(0, self.cbdc_params.cbdc_interest_rate - self.current_state.deposit_interest_rate)
        deposit_growth += cbdc_effect
        
        # Update deposits
        self.current_state.bank_deposits *= (1 + deposit_growth)
        
        # Update reserves based on deposit changes and reserve requirement
        required_reserves = self.current_state.bank_deposits * self.banking_params.reserve_requirement
        excess_reserves = max(0, self.current_state.bank_reserves - required_reserves)
        
        # Banks adjust excess reserves based on interest rates
        reserve_adjustment = -0.2 * (self.current_state.interest_rate - self.current_state.deposit_interest_rate)
        excess_reserves *= (1 + reserve_adjustment)
        
        self.current_state.bank_reserves = required_reserves + excess_reserves
        
        # Update other balance sheet items
        securities_growth = 0.2 * gdp_growth + 0.3 * (self.current_state.interest_rate - self.current_state.additional_variables.get("prev_interest_rate", self.current_state.interest_rate))
        self.current_state.additional_variables["bank_securities"] *= (1 + securities_growth)
        
        # Borrowings adjust to balance the balance sheet
        total_assets = (self.current_state.bank_loans + 
                       self.current_state.bank_reserves + 
                       self.current_state.additional_variables["bank_securities"] + 
                       self.current_state.additional_variables["bank_other_assets"])
        
        total_liabilities_ex_borrowings = (self.current_state.bank_deposits + 
                                         self.current_state.additional_variables["bank_equity"])
        
        self.current_state.additional_variables["bank_borrowings"] = total_assets - total_liabilities_ex_borrowings
        
        # Store current values for next iteration
        self.current_state.additional_variables["prev_loan_rate"] = self.current_state.loan_interest_rate
        self.current_state.additional_variables["prev_interest_rate"] = self.current_state.interest_rate
    
    def _apply_regulations(self) -> None:
        """Apply banking regulations and calculate compliance."""
        # Calculate capital ratio
        total_assets = (self.current_state.bank_loans + 
                       self.current_state.bank_reserves + 
                       self.current_state.additional_variables["bank_securities"] + 
                       self.current_state.additional_variables["bank_other_assets"])
        
        equity = self.current_state.additional_variables["bank_equity"]
        capital_ratio = equity / total_assets
        
        # Check capital requirement
        capital_requirement = self.banking_params.capital_requirement
        capital_shortfall = max(0, (capital_requirement - capital_ratio) * total_assets)
        
        if capital_shortfall > 0:
            # Banks respond to capital shortfall by reducing assets (loans)
            reduction_needed = capital_shortfall / (1 - capital_requirement)
            self.current_state.bank_loans -= reduction_needed * 0.8  # 80% from loans
            self.current_state.additional_variables["bank_securities"] -= reduction_needed * 0.2  # 20% from securities
        
        # Calculate liquidity coverage
        liquid_assets = self.current_state.bank_reserves + self.current_state.additional_variables["bank_securities"] * 0.8
        short_term_liabilities = self.current_state.bank_deposits * 0.3 + self.current_state.additional_variables["bank_borrowings"] * 0.5
        liquidity_ratio = liquid_assets / short_term_liabilities
        
        # Check liquidity requirement
        liquidity_requirement = self.banking_params.liquidity_coverage_ratio
        liquidity_shortfall = max(0, (liquidity_requirement - liquidity_ratio) * short_term_liabilities)
        
        if liquidity_shortfall > 0:
            # Banks respond to liquidity shortfall by increasing liquid assets
            self.current_state.bank_loans -= liquidity_shortfall * 0.5  # Reduce loans
            self.current_state.bank_reserves += liquidity_shortfall * 0.3  # Increase reserves
            self.current_state.additional_variables["bank_securities"] += liquidity_shortfall * 0.2  # Increase securities
        
        # Store regulatory metrics
        self.current_state.additional_variables["capital_ratio"] = capital_ratio
        self.current_state.additional_variables["liquidity_ratio"] = liquidity_ratio
    
    def _central_bank_operations(self) -> None:
        """Model central bank operations including CBDC issuance."""
        # Implement monetary policy
        policy_rate = self.current_state.policy_rate
        
        # Open market operations
        if self.banking_params.quantitative_easing != 0:
            # QE increases reserves and securities held by central bank
            qe_amount = self.banking_params.quantitative_easing * self.current_state.gdp * 0.01
            self.current_state.bank_reserves += qe_amount
            self.current_state.additional_variables["bank_securities"] -= qe_amount
            self.current_state.additional_variables["central_bank_securities"] = self.current_state.additional_variables.get("central_bank_securities", 0) + qe_amount
        
        # CBDC issuance
        cbdc_issuance = self.cbdc_params.programmable_asset_purchases
        if cbdc_issuance > 0:
            # Increase CBDC supply
            self.current_state.cbdc_supply += cbdc_issuance
            
            # Effect depends on whether it's a direct issuance or asset purchase
            self.current_state.additional_variables["central_bank_assets"] = self.current_state.additional_variables.get("central_bank_assets", 0) + cbdc_issuance
    
    def _calculate_stability_indicators(self) -> None:
        """Calculate financial stability indicators."""
        # Leverage in the banking system
        total_assets = (self.current_state.bank_loans + 
                       self.current_state.bank_reserves + 
                       self.current_state.additional_variables["bank_securities"] + 
                       self.current_state.additional_variables["bank_other_assets"])
        
        equity = self.current_state.additional_variables["bank_equity"]
        leverage = total_assets / equity
        
        # Credit growth
        if "prev_bank_loans" in self.current_state.additional_variables:
            credit_growth = self.current_state.bank_loans / self.current_state.additional_variables["prev_bank_loans"] - 1
        else:
            credit_growth = 0.01  # Default initial value
        
        # Funding stability
        stable_funding = self.current_state.bank_deposits * 0.7 + self.current_state.additional_variables["bank_borrowings"] * 0.3 + equity
        funding_stability = stable_funding / total_assets
        
        # Composite financial stability index
        stability_index = (
            0.3 * (1 / leverage) +  # Lower leverage is better
            0.3 * (1 - abs(credit_growth - 0.02) / 0.05) +  # Credit growth close to 2% is optimal
            0.4 * funding_stability  # Higher funding stability is better
        )
        
        # Update state
        self.current_state.financial_stress_index = 1 - stability_index
        self.current_state.additional_variables["banking_leverage"] = leverage
        self.current_state.additional_variables["credit_growth"] = credit_growth
        self.current_state.additional_variables["funding_stability"] = funding_stability
        
        # Store for next iteration
        self.current_state.additional_variables["prev_bank_loans"] = self.current_state.bank_loans
    
    def _apply_cbdc_banking_effects(self) -> None:
        """Apply CBDC effects on the banking system."""
        # CBDC disintermediation effect
        cbdc_rate = self.cbdc_params.cbdc_interest_rate
        deposit_rate = self.current_state.deposit_interest_rate
        
        if cbdc_rate > deposit_rate:
            # CBDC more attractive than bank deposits
            disintermediation = (cbdc_rate - deposit_rate) * self.banking_params.cbdc_disintermediation_factor
            
            # Shift from bank deposits to CBDC
            deposit_reduction = self.current_state.bank_deposits * disintermediation
            self.current_state.bank_deposits -= deposit_reduction
            self.current_state.cbdc_supply += deposit_reduction
            
            # Track effect
            self.current_state.additional_variables["cbdc_disintermediation"] = deposit_reduction
        else:
            self.current_state.additional_variables["cbdc_disintermediation"] = 0.0
        
        # CBDC distribution role for banks
        if self.banking_params.bank_cbdc_distribution_role > 0:
            # Banks earn fee income from CBDC distribution
            fee_income = self.current_state.cbdc_supply * 0.001 * self.banking_params.bank_cbdc_distribution_role
            
            # Add to bank equity
            self.current_state.additional_variables["bank_equity"] += fee_income
            
            # Track effect
            self.current_state.additional_variables["cbdc_fee_income"] = fee_income

# =============================================================================
# Simulation Controller
# =============================================================================

class CBDCSimulation:
    """Main simulation controller that coordinates all components."""
    
    def __init__(self, config: SimulationConfig):
        """Initialize the simulation with configuration."""
        self.config = config
        
        # Set random seed for reproducibility
        np.random.seed(config.random_seed)
        
        # Initialize component models
        self.economic_model = EconomicModel(config)
        self.cbdc_system = CBDCSystem(config)
        self.trade_system = TradeSystem(config)
        self.banking_system = BankingSystem(config)
        
        # Initialize results storage
        self.results = []
    
    def run(self) -> pd.DataFrame:
        """Run the simulation for the specified time horizon."""
        time_horizon = self.config.time_horizon
        
        for t in range(time_horizon):
            # Step 1: Update CBDC system
            self.cbdc_system.update(self.economic_model.current_state)
            
            # Step 2: Update banking system
            self.banking_system.update(self.economic_model.current_state)
            
            # Step 3: Update trade system
            self.trade_system.update(self.economic_model.current_state)
            
            # Step 4: Advance economic model
            self.economic_model.step(t)
            
            # Store results if needed
            if t % self.config.save_frequency == 0:
                self.results.append(self.economic_model.current_state.as_dict())
                
            print(f"Completed time step {t+1}/{time_horizon}")
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(self.results)
        return results_df
    
    def save_results(self, filepath: str) -> None:
        """Save simulation results to CSV file."""
        results_df = pd.DataFrame(self.results)
        results_df.to_csv(filepath, index=False)
    
    def plot_results(self, variables: List[str], title: str = "Simulation Results") -> plt.Figure:
        """Plot selected variables from simulation results."""
        results_df = pd.DataFrame(self.results)
        
        fig, axes = plt.subplots(len(variables), 1, figsize=(10, 3*len(variables)))
        if len(variables) == 1:
            axes = [axes]
        
        for i, var in enumerate(variables):
            if var in results_df.columns:
                axes[i].plot(results_df.index, results_df[var])
                axes[i].set_title(var)
                axes[i].grid(True)
            else:
                axes[i].text(0.5, 0.5, f"Variable '{var}' not found", 
                           horizontalalignment='center', verticalalignment='center')
        
        fig.tight_layout()
        fig.suptitle(title, fontsize=16)
        plt.subplots_adjust(top=0.95)
        
        return fig

# =============================================================================
# Scenario Generation
# =============================================================================

def create_default_config() -> SimulationConfig:
    """Create a default simulation configuration."""
    # Create basic config
    config = SimulationConfig(
        time_horizon=20,
        start_date="2025-01-01",
        random_seed=42,
        output_variables=["gdp", "inflation_rate", "unemployment_rate", "interest_rate", 
                         "exchange_rate", "cbdc_supply", "bank_deposits"],
        save_frequency=1
    )
    
    # Set initial state
    initial_state = EconomicState(
        gdp=20000.0,
        potential_gdp=20000.0,
        inflation_rate=2.0,
        unemployment_rate=4.0,
        interest_rate=2.5,
        policy_rate=2.5,
        exchange_rate=1.0,
        government_spending=4000.0,
        tax_revenue=3500.0,
        government_debt=20000.0,
        money_supply=3500.0,
        cbdc_supply=0.0,  # Starting with no CBDC
        bank_reserves=200.0,
        bank_loans=15000.0,
        bank_deposits=18000.0,
        price_level=1.0,
        inflation_expectations=2.0,
        growth_expectations=2.5
    )
    config.initial_state = initial_state
    
    # Set CBDC parameters (initially minimal)
    cbdc_params = CBDCParameters(
        cbdc_interest_rate=0.0,
        programmable_money_validity=365,
        conditional_spending_constraints=0.0,
        automatic_fiscal_transfers=0.0,
        smart_contract_based_lending=0.0,
        foreign_exchange_controls=0.0,
        macroprudential_tools=0.0,
        emergency_override_mechanisms=0.0
    )
    config.cbdc_parameters = cbdc_params
    
    # Set trade parameters
    trade_params = TradeParameters(
        tariff_rate=0.05,
        customs_efficiency=0.8,
        exchange_rate_regime="floating"
    )
    config.trade_parameters = trade_params
    
    # Set banking parameters
    banking_params = BankingParameters(
        capital_requirement=0.08,
        reserve_requirement=0.02,
        liquidity_coverage_ratio=1.0,
        lending_risk_appetite=0.5,
        cbdc_disintermediation_factor=0.2
    )
    config.banking_parameters = banking_params
    
    return config

def create_cbdc_adoption_scenario() -> SimulationConfig:
    """Create a scenario with gradual CBDC adoption."""
    config = create_default_config()
    
    # Set up policy changes for CBDC introduction
    config.policy_changes = {
        # Quarter 1: Initial CBDC introduction
        1: {
            "cbdc_interest_rate": 0.5,
            "cbdc_supply": 500.0
        },
        # Quarter 4: Expand CBDC features
        4: {
            "programmable_money_validity": 180,  # 6 months validity
            "conditional_spending_constraints": 0.1,
            "smart_contract_based_lending": 0.2
        },
        # Quarter 8: Full CBDC implementation
        8: {
            "cbdc_interest_rate": 1.0,
            "automatic_fiscal_transfers": 200.0,
            "programmable_asset_purchases": 300.0,
            "foreign_exchange_controls": 0.3
        },
        # Quarter 12: Economic crisis response
        12: {
            "emergency_override_mechanisms": 1.0,
            "macroprudential_tools": 0.5,
            "automatic_fiscal_transfers": 500.0
        }
    }
    
    # Add economic shocks
    config.shocks = {
        # Quarter 10: Negative economic shock
        10: {
            "gdp": -1000.0,
            "inflation_rate": 1.5,
            "unemployment_rate": 2.0
        }
    }
    
    return config

def create_trade_war_scenario() -> SimulationConfig:
    """Create a scenario with trade tensions and tariff escalation."""
    config = create_default_config()
    
    # Set up policy changes for trade war
    config.policy_changes = {
        # Quarter 2: Initial tariff increase
        2: {
            "tariff_rate": 0.15,
            "foreign_exchange_controls": 0.2
        },
        # Quarter 4: Trading partner retaliation (external shock)
        4: {
            "exports": -500.0
        },
        # Quarter 6: Further escalation
        6: {
            "tariff_rate": 0.25,
            "foreign_exchange_controls": 0.4,
            "exchange_rate_regime": "managed",
            "exchange_rate_target": 1.1,
            "intervention_threshold": 0.05
        },
        # Quarter 10: CBDC response
        10: {
            "cbdc_trade_settlement": 0.5,
            "cross_border_cbdc_limits": 0.3,
            "cbdc_supply": 1000.0
        },
        # Quarter 14: De-escalation
        14: {
            "tariff_rate": 0.1,
            "foreign_exchange_controls": 0.1,
            "exchange_rate_regime": "floating"
        }
    }
    
    return config

def create_banking_crisis_scenario() -> SimulationConfig:
    """Create a scenario with banking sector stress and CBDC response."""
    config = create_default_config()
    
    # Set up policy changes and shocks
    config.policy_changes = {
        # Quarter 2: Initial signs of stress
        2: {
            "lending_risk_appetite": 0.7  # Increased risk-taking
        },
        # Quarter 5: CBDC introduction as preparation
        5: {
            "cbdc_supply": 500.0,
            "cbdc_interest_rate": 0.0,
            "macroprudential_tools": 0.2
        }
    }
    
    # Add banking crisis shock
    config.shocks = {
        # Quarter 8: Banking crisis hits
        8: {
            "bank_loans": -2000.0,
            "bank_deposits": -1500.0,
            "financial_stress_index": 0.3,
            "loan_interest_rate": 2.0
        }
    }
    
    # Add policy response
    config.policy_changes.update({
        # Quarter 9: Crisis response
        9: {
            "emergency_override_mechanisms": 2.0,
            "policy_rate": -1.0,  # Policy rate cut
            "cbdc_interest_rate": 1.0,  # Attractive CBDC rate
            "smart_contract_based_lending": 0.8,
            "cbdc_supply": 3000.0,
            "quantitative_easing": 0.05  # 5% of GDP
        },
        # Quarter 12: Recovery measures
        12: {
            "emergency_override_mechanisms": 0.0,
            "policy_rate": 0.5,
            "cbdc_interest_rate": 0.5,
            "automatic_fiscal_transfers": 300.0
        }
    })
    
    return config

# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main function to run the simulation."""
    print("CBDC Economic Simulation System")
    print("===============================")
    
    # Create default configuration
    config = create_default_config()
    
    # Initialize simulation
    simulation = CBDCSimulation(config)
    
    # Run simulation
    print("Running simulation...")
    results = simulation.run()
    
    # Save results
    output_dir = "simulation_results"
    os.makedirs(output_dir, exist_ok=True)
    simulation.save_results(os.path.join(output_dir, "default_scenario_results.csv"))
    
    # Plot key variables
    key_vars = ["gdp", "inflation_rate", "unemployment_rate", "interest_rate"]
    fig = simulation.plot_results(key_vars, "Default Scenario - Key Macroeconomic Variables")
    fig.savefig(os.path.join(output_dir, "default_scenario_macro.png"))
    
    cbdc_vars = ["cbdc_supply", "bank_deposits", "money_supply"]
    fig = simulation.plot_results(cbdc_vars, "Default Scenario - CBDC and Banking Variables")
    fig.savefig(os.path.join(output_dir, "default_scenario_cbdc.png"))
    
    print("Simulation completed successfully.")
    print(f"Results saved to {output_dir}/")

if __name__ == "__main__":
    main()
