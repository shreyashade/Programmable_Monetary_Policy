"""
CBDC Economic Simulation - Data Integration Module (Fixed Version)

This module provides data integration capabilities for the CBDC economic simulation system,
using standard Python libraries to fetch data from the World Bank API directly.
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import time
import datetime

class WorldBankDataFetcher:
    """
    Class for fetching real-world economic data from World Bank APIs.
    This enables the simulation to be initialized with actual country data.
    """
    
    def __init__(self):
        """Initialize the data fetcher."""
        # Base URL for World Bank API
        self.api_base_url = "https://api.worldbank.org/v2"
        
        # Common economic indicators and their codes
        self.common_indicators = {
            "gdp": "NY.GDP.MKTP.CD",                      # GDP (current US$)
            "gdp_growth": "NY.GDP.MKTP.KD.ZG",            # GDP growth (annual %)
            "inflation": "FP.CPI.TOTL.ZG",                # Inflation, consumer prices (annual %)
            "unemployment": "SL.UEM.TOTL.ZS",             # Unemployment, total (% of total labor force)
            "interest_rate": "FR.INR.LEND",               # Lending interest rate (%)
            "government_debt": "GC.DOD.TOTL.GD.ZS",       # Central government debt, total (% of GDP)
            "government_spending": "NE.CON.GOVT.ZS",      # Government expenditure (% of GDP)
            "money_supply": "FM.LBL.BMNY.GD.ZS",          # Broad money (% of GDP)
            "current_account": "BN.CAB.XOKA.GD.ZS",       # Current account balance (% of GDP)
            "exchange_rate": "PA.NUS.FCRF",               # Official exchange rate (LCU per US$, period average)
            "exports": "NE.EXP.GNFS.ZS",                  # Exports of goods and services (% of GDP)
            "imports": "NE.IMP.GNFS.ZS",                  # Imports of goods and services (% of GDP)
            "foreign_reserves": "FI.RES.TOTL.CD",         # Total reserves (includes gold, current US$)
            "tax_revenue": "GC.TAX.TOTL.GD.ZS",           # Tax revenue (% of GDP)
            "bank_capital": "FB.BNK.CAPA.ZS",             # Bank capital to assets ratio (%)
            "bank_nonperforming_loans": "FB.AST.NPER.ZS", # Bank nonperforming loans to total gross loans (%)
            "financial_depth": "FS.AST.PRVT.GD.ZS",       # Domestic credit to private sector (% of GDP)
            "tariff_rate": "TM.TAX.MRCH.WM.AR.ZS"         # Tariff rate, applied, weighted mean, all products (%)
        }
        
        # Mapping from indicator codes to simulation variables
        self.indicator_to_variable = {
            "NY.GDP.MKTP.CD": "gdp",
            "FP.CPI.TOTL.ZG": "inflation_rate",
            "SL.UEM.TOTL.ZS": "unemployment_rate",
            "FR.INR.LEND": "interest_rate",
            "GC.DOD.TOTL.GD.ZS": "government_debt",
            "NE.CON.GOVT.ZS": "government_spending",
            "FM.LBL.BMNY.GD.ZS": "money_supply",
            "BN.CAB.XOKA.GD.ZS": "current_account",
            "PA.NUS.FCRF": "exchange_rate",
            "NE.EXP.GNFS.ZS": "exports",
            "NE.IMP.GNFS.ZS": "imports",
            "FI.RES.TOTL.CD": "foreign_reserves",
            "GC.TAX.TOTL.GD.ZS": "tax_revenue",
            "FB.BNK.CAPA.ZS": "bank_capital_ratio",
            "FB.AST.NPER.ZS": "nonperforming_loans",
            "FS.AST.PRVT.GD.ZS": "bank_loans",
            "TM.TAX.MRCH.WM.AR.ZS": "tariff_rate"
        }
        
        # Cache for API responses to avoid redundant calls
        self.cache = {}
    
    def get_indicator_description(self, indicator_code: str) -> Dict[str, Any]:
        """
        Get detailed description of a specific indicator.
        
        Args:
            indicator_code: World Bank indicator code
            
        Returns:
            Dictionary with indicator details
        """
        cache_key = f"description_{indicator_code}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Construct URL for indicator metadata
            url = f"{self.api_base_url}/indicator/{indicator_code}?format=json"
            
            # Make API request
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant information
                if isinstance(data, list) and len(data) > 1 and len(data[1]) > 0:
                    indicator_info = data[1][0]
                    result = {
                        "indicatorCode": indicator_code,
                        "indicatorName": indicator_info.get("name", "Unknown"),
                        "topic": indicator_info.get("sourceNote", ""),
                        "longDescription": indicator_info.get("sourceNote", "")
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = result
                    return result
            
            # Default response if API call fails
            default_response = {
                "indicatorCode": indicator_code,
                "indicatorName": "Unknown",
                "topic": "",
                "longDescription": ""
            }
            self.cache[cache_key] = default_response
            return default_response
            
        except Exception as e:
            print(f"Error fetching indicator description: {e}")
            return {"indicatorCode": indicator_code, "indicatorName": "Unknown", "longDescription": ""}
    
    def get_indicator_data(self, country_code: str, indicator_code: str) -> Dict[str, Any]:
        """
        Get data for a specific indicator and country.
        
        Args:
            country_code: ISO 3166 alpha-3 country code
            indicator_code: World Bank indicator code
            
        Returns:
            Dictionary with indicator data by year
        """
        cache_key = f"data_{country_code}_{indicator_code}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Construct URL for indicator data
            url = f"{self.api_base_url}/country/{country_code}/indicator/{indicator_code}?format=json&per_page=100"
            
            # Make API request
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant information
                if isinstance(data, list) and len(data) > 1:
                    # Get country name from the first data point if available
                    country_name = data[1][0]["country"]["value"] if len(data[1]) > 0 else "Unknown"
                    
                    # Process data points
                    yearly_data = {}
                    for item in data[1]:
                        year = item.get("date")
                        value = item.get("value")
                        if year and value is not None:
                            yearly_data[year] = float(value)
                    
                    result = {
                        "countryCode": country_code,
                        "countryName": country_name,
                        "indicatorCode": indicator_code,
                        "indicatorName": self.get_indicator_description(indicator_code).get("indicatorName", "Unknown"),
                        "data": yearly_data
                    }
                    
                    # Cache the result
                    self.cache[cache_key] = result
                    return result
            
            # Default response if API call fails
            default_response = {
                "countryCode": country_code,
                "countryName": "Unknown",
                "indicatorCode": indicator_code,
                "indicatorName": "Unknown",
                "data": {}
            }
            self.cache[cache_key] = default_response
            return default_response
            
        except Exception as e:
            print(f"Error fetching indicator data: {e}")
            return {"data": {}}
    
    def get_country_data(self, country_code: str, year: Optional[int] = None) -> Dict[str, float]:
        """
        Get comprehensive economic data for a specific country.
        
        Args:
            country_code: ISO 3166 alpha-3 country code
            year: Specific year to fetch data for (default: most recent available)
            
        Returns:
            Dictionary with economic indicators
        """
        country_data = {}
        country_name = ""
        
        for indicator_name, indicator_code in self.common_indicators.items():
            try:
                response = self.get_indicator_data(country_code, indicator_code)
                
                if not country_name and "countryName" in response:
                    country_name = response["countryName"]
                
                if "data" in response:
                    data = response["data"]
                    
                    # If year is specified, get that specific year
                    if year is not None and str(year) in data and data[str(year)] is not None:
                        country_data[indicator_name] = data[str(year)]
                    # Otherwise, get the most recent available data
                    else:
                        # Find the most recent year with data
                        available_years = [int(y) for y in data.keys() if data[y] is not None]
                        if available_years:
                            most_recent_year = max(available_years)
                            country_data[indicator_name] = data[str(most_recent_year)]
                            country_data[f"{indicator_name}_year"] = most_recent_year
            except Exception as e:
                print(f"Error processing indicator {indicator_name}: {e}")
        
        # Add country name and code
        country_data["country_name"] = country_name
        country_data["country_code"] = country_code
        
        return country_data
    
    def search_countries(self, query: str) -> List[Dict[str, str]]:
        """
        Search for countries by name.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching countries with codes and names
        """
        try:
            # Construct URL for country search
            url = f"{self.api_base_url}/country?format=json&per_page=100"
            
            # Make API request
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract country information
                if isinstance(data, list) and len(data) > 1:
                    countries = []
                    query_lower = query.lower()
                    
                    for item in data[1]:
                        country_name = item.get("name", "")
                        country_code = item.get("id", "")
                        
                        # Check if query matches
                        if query_lower in country_name.lower() or query_lower in country_code.lower():
                            countries.append({
                                "code": country_code,
                                "name": country_name
                            })
                    
                    return countries
            
            # Fallback to common countries if API call fails
            return self._search_common_countries(query)
            
        except Exception as e:
            print(f"Error searching countries: {e}")
            return self._search_common_countries(query)
    
    def _search_common_countries(self, query: str) -> List[Dict[str, str]]:
        """
        Search for countries in a predefined list (fallback method).
        
        Args:
            query: Search query string
            
        Returns:
            List of matching countries with codes and names
        """
        common_countries = [
            {"code": "USA", "name": "United States"},
            {"code": "GBR", "name": "United Kingdom"},
            {"code": "DEU", "name": "Germany"},
            {"code": "FRA", "name": "France"},
            {"code": "JPN", "name": "Japan"},
            {"code": "CHN", "name": "China"},
            {"code": "IND", "name": "India"},
            {"code": "BRA", "name": "Brazil"},
            {"code": "CAN", "name": "Canada"},
            {"code": "AUS", "name": "Australia"},
            {"code": "RUS", "name": "Russian Federation"},
            {"code": "ZAF", "name": "South Africa"},
            {"code": "MEX", "name": "Mexico"},
            {"code": "KOR", "name": "Korea, Rep."},
            {"code": "IDN", "name": "Indonesia"},
            {"code": "TUR", "name": "Turkey"},
            {"code": "SAU", "name": "Saudi Arabia"},
            {"code": "ARG", "name": "Argentina"},
            {"code": "THA", "name": "Thailand"},
            {"code": "NGA", "name": "Nigeria"}
        ]
        
        query = query.lower()
        return [country for country in common_countries 
                if query in country["name"].lower() or query in country["code"].lower()]
    
    def convert_to_simulation_state(self, country_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Convert World Bank data format to simulation state variables.
        
        Args:
            country_data: Dictionary with country economic data
            
        Returns:
            Dictionary with simulation state variables
        """
        simulation_state = {}
        
        # Direct mappings
        if "gdp" in country_data:
            # Convert from USD to billions USD for simulation
            simulation_state["gdp"] = country_data["gdp"] / 1e9
        
        if "inflation" in country_data:
            simulation_state["inflation_rate"] = country_data["inflation"]
        
        if "unemployment" in country_data:
            simulation_state["unemployment_rate"] = country_data["unemployment"]
        
        if "interest_rate" in country_data:
            simulation_state["interest_rate"] = country_data["interest_rate"]
            # Set policy rate slightly below lending rate
            simulation_state["policy_rate"] = max(0, country_data["interest_rate"] - 1.0)
        
        if "government_debt" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            debt_pct = country_data["government_debt"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["government_debt"] = (debt_pct / 100) * gdp_billions
        
        if "government_spending" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            spending_pct = country_data["government_spending"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["government_spending"] = (spending_pct / 100) * gdp_billions
        
        if "tax_revenue" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            tax_pct = country_data["tax_revenue"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["tax_revenue"] = (tax_pct / 100) * gdp_billions
        
        if "money_supply" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            money_pct = country_data["money_supply"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["money_supply"] = (money_pct / 100) * gdp_billions
        
        if "exports" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            exports_pct = country_data["exports"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["exports"] = (exports_pct / 100) * gdp_billions
        
        if "imports" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            imports_pct = country_data["imports"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["imports"] = (imports_pct / 100) * gdp_billions
            
            # Calculate net exports
            simulation_state["net_exports"] = simulation_state["exports"] - simulation_state["imports"]
        
        if "current_account" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            ca_pct = country_data["current_account"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["current_account"] = (ca_pct / 100) * gdp_billions
        
        if "exchange_rate" in country_data:
            simulation_state["exchange_rate"] = country_data["exchange_rate"]
        
        if "foreign_reserves" in country_data:
            # Convert from USD to billions USD
            simulation_state["foreign_reserves"] = country_data["foreign_reserves"] / 1e9
        
        # Banking sector variables
        if "financial_depth" in country_data and "gdp" in country_data:
            # Convert from % of GDP to absolute value in billions
            loans_pct = country_data["financial_depth"]
            gdp_billions = country_data["gdp"] / 1e9
            simulation_state["bank_loans"] = (loans_pct / 100) * gdp_billions
            
            # Estimate bank deposits (typically slightly higher than loans)
            simulation_state["bank_deposits"] = simulation_state["bank_loans"] * 1.2
        
        if "bank_nonperforming_loans" in country_data:
            # Use as input to financial stress index (0-1 scale)
            npl_ratio = country_data["bank_nonperforming_loans"] / 100
            simulation_state["financial_stress_index"] = min(1.0, npl_ratio * 5)  # Scale up for stress index
        
        # Derived variables
        if "gdp" in country_data and "gdp_growth" in country_data:
            # Calculate potential GDP (slightly above actual GDP)
            gdp_billions = country_data["gdp"] / 1e9
            growth_rate = country_data["gdp_growth"] / 100
            simulation_state["potential_gdp"] = gdp_billions * (1 + 0.01)  # 1% above current
            
            # Set growth expectations
            simulation_state["growth_expectations"] = growth_rate
        
        # Set price level to 1.0 as baseline
        simulation_state["price_level"] = 1.0
        
        # Set inflation expectations equal to current inflation
        if "inflation_rate" in simulation_state:
            simulation_state["inflation_expectations"] = simulation_state["inflation_rate"]
        
        # Set CBDC supply to zero initially (pre-adoption)
        simulation_state["cbdc_supply"] = 0.0
        
        # Set loan and deposit interest rates based on policy rate
        if "policy_rate" in simulation_state:
            simulation_state["loan_interest_rate"] = simulation_state["policy_rate"] + 3.0
            simulation_state["deposit_interest_rate"] = max(0, simulation_state["policy_rate"] - 1.0)
        
        # Calculate consumption and investment based on GDP components
        if "gdp" in simulation_state and "government_spending" in simulation_state and "net_exports" in simulation_state:
            gdp = simulation_state["gdp"]
            govt = simulation_state["government_spending"]
            nx = simulation_state["net_exports"]
            
            # Typical ratios: consumption ~60%, investment ~20%
            simulation_state["consumption"] = gdp * 0.6
            simulation_state["investment"] = gdp - simulation_state["consumption"] - govt - nx
        
        return simulation_state
    
    def get_historical_data(self, country_code: str, indicators: List[str], start_year: int, end_year: int) -> pd.DataFrame:
        """
        Get historical data for multiple indicators over a time period.
        
        Args:
            country_code: ISO 3166 alpha-3 country code
            indicators: List of indicator codes or names
            start_year: Starting year for data
            end_year: Ending year for data
            
        Returns:
            DataFrame with years as index and indicators as columns
        """
        # Convert indicator names to codes if needed
        indicator_codes = []
        for indicator in indicators:
            if indicator in self.common_indicators:
                indicator_codes.append(self.common_indicators[indicator])
            else:
                indicator_codes.append(indicator)
        
        # Fetch data for each indicator
        data_by_indicator = {}
        for indicator_code in indicator_codes:
            response = self.get_indicator_data(country_code, indicator_code)
            
            if "data" in response:
                # Extract the variable name for this indicator
                var_name = self.indicator_to_variable.get(indicator_code, indicator_code)
                
                # Extract yearly data
                yearly_data = {}
                for year, value in response["data"].items():
                    if value is not None and start_year <= int(year) <= end_year:
                        yearly_data[int(year)] = value
                
                data_by_indicator[var_name] = yearly_data
        
        # Create a DataFrame with years as index
        years = list(range(start_year, end_year + 1))
        df = pd.DataFrame(index=years)
        
        # Add each indicator as a column
        for var_name, yearly_data in data_by_indicator.items():
            df[var_name] = pd.Series(yearly_data)
        
        return df
    
    def get_country_metadata(self, country_code: str) -> Dict[str, Any]:
        """
        Get metadata about a country.
        
        Args:
            country_code: ISO 3166 alpha-3 country code
            
        Returns:
            Dictionary with country metadata
        """
        try:
            # Construct URL for country metadata
            url = f"{self.api_base_url}/country/{country_code}?format=json"
            
            # Make API request
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract relevant information
                if isinstance(data, list) and len(data) > 1 and len(data[1]) > 0:
                    country_info = data[1][0]
                    
                    # Get country data for additional information
                    country_data = self.get_country_data(country_code)
                    
                    metadata = {
                        "country_code": country_code,
                        "country_name": country_info.get("name", "Unknown"),
                        "region": country_info.get("region", {}).get("value", "Unknown"),
                        "income_level": country_info.get("incomeLevel", {}).get("value", "Unknown"),
                        "capital_city": country_info.get("capitalCity", "Unknown"),
                        "longitude": country_info.get("longitude", None),
                        "latitude": country_info.get("latitude", None),
                        "data_year": max([country_data.get(f"{ind}_year", 0) for ind in self.common_indicators.keys()]),
                        "indicators_available": [ind for ind in self.common_indicators.keys() if ind in country_data],
                        "gdp_billions": country_data.get("gdp", 0) / 1e9 if "gdp" in country_data else 0
                    }
                    
                    return metadata
            
            # Fallback to basic information if API call fails
            country_data = self.get_country_data(country_code)
            
            metadata = {
                "country_code": country_code,
                "country_name": country_data.get("country_name", "Unknown"),
                "data_year": max([country_data.get(f"{ind}_year", 0) for ind in self.common_indicators.keys()]),
                "indicators_available": [ind for ind in self.common_indicators.keys() if ind in country_data],
                "gdp_billions": country_data.get("gdp", 0) / 1e9 if "gdp" in country_data else 0
            }
            
            return metadata
            
        except Exception as e:
            print(f"Error fetching country metadata: {e}")
            return {
                "country_code": country_code,
                "country_name": "Unknown",
                "data_year": 0,
                "indicators_available": [],
                "gdp_billions": 0
            }


class DataExplainer:
    """
    Class for generating natural language explanations of economic data and simulation results.
    """
    
    def __init__(self, data_fetcher: Optional[WorldBankDataFetcher] = None):
        """
        Initialize the data explainer.
        
        Args:
            data_fetcher: Optional WorldBankDataFetcher instance for accessing indicator descriptions
        """
        self.data_fetcher = data_fetcher or WorldBankDataFetcher()
        
        # Descriptions of key economic variables
        self.variable_descriptions = {
            "gdp": "Gross Domestic Product (GDP) is the total value of all goods and services produced in a country.",
            "inflation_rate": "Inflation rate measures the annual percentage increase in consumer prices.",
            "unemployment_rate": "Unemployment rate is the percentage of the labor force that is jobless and actively seeking employment.",
            "interest_rate": "Interest rate is the cost of borrowing money, typically expressed as an annual percentage.",
            "exchange_rate": "Exchange rate is the value of one currency in terms of another currency.",
            "government_debt": "Government debt is the total amount owed by the government to creditors.",
            "budget_deficit": "Budget deficit occurs when government spending exceeds revenue in a fiscal period.",
            "money_supply": "Money supply is the total amount of monetary assets available in an economy at a specific time.",
            "cbdc_supply": "CBDC supply is the total amount of Central Bank Digital Currency in circulation.",
            "consumption": "Consumption is the spending by households on goods and services.",
            "investment": "Investment is spending on capital goods, inventory, and structures that will be used for production.",
            "exports": "Exports are goods and services produced domestically but sold to foreign buyers.",
            "imports": "Imports are goods and services produced abroad but purchased by domestic buyers.",
            "net_exports": "Net exports are the value of exports minus imports.",
            "current_account": "Current account balance is the sum of net exports, net income from abroad, and net transfers.",
            "bank_loans": "Bank loans represent the total credit extended by banks to borrowers.",
            "bank_deposits": "Bank deposits are funds placed with banks for safekeeping and to earn interest.",
            "financial_stress_index": "Financial stress index measures the level of strain in financial markets and institutions."
        }
        
        # Descriptions of relationships between variables
        self.relationship_descriptions = {
            "phillips_curve": "The Phillips Curve describes the inverse relationship between unemployment and inflation.",
            "is_curve": "The IS (Investment-Saving) curve represents combinations of interest rates and output where the goods market is in equilibrium.",
            "lm_curve": "The LM (Liquidity-Money) curve represents combinations of interest rates and output where the money market is in equilibrium.",
            "okuns_law": "Okun's Law describes the relationship between unemployment and GDP growth.",
            "quantity_theory": "The Quantity Theory of Money relates money supply, velocity, price level, and output.",
            "uncovered_interest_parity": "Uncovered Interest Parity relates interest rate differentials to expected exchange rate changes.",
            "bank_lending_channel": "The Bank Lending Channel describes how monetary policy affects the economy through bank lending capacity."
        }
        
        # Descriptions of CBDC parameters and their effects
        self.cbdc_parameter_descriptions = {
            "cbdc_interest_rate": "Interest rate paid on CBDC balances, affecting the attractiveness of holding CBDC versus bank deposits.",
            "programmable_money_validity": "Time period for which CBDC remains valid, enabling velocity control and encouraging spending.",
            "conditional_spending_constraints": "Restrictions on how CBDC can be spent, enabling targeted stimulus and sectoral policies.",
            "automatic_fiscal_transfers": "Direct payments through CBDC, enabling rapid and targeted fiscal stimulus.",
            "smart_contract_based_lending": "Automated lending through smart contracts, potentially bypassing traditional banking channels.",
            "foreign_exchange_controls": "Restrictions on cross-border CBDC flows, enabling capital flow management.",
            "macroprudential_tools": "System-wide financial stability tools implemented through CBDC.",
            "emergency_override_mechanisms": "Crisis response capabilities built into the CBDC system."
        }
    
    def explain_variable(self, variable_name: str) -> str:
        """
        Generate an explanation for an economic variable.
        
        Args:
            variable_name: Name of the economic variable
            
        Returns:
            Natural language explanation
        """
        # Check if we have a predefined description
        if variable_name in self.variable_descriptions:
            return self.variable_descriptions[variable_name]
        
        # Check if it's a World Bank indicator
        for indicator_name, indicator_code in self.data_fetcher.common_indicators.items():
            if indicator_name == variable_name or self.data_fetcher.indicator_to_variable.get(indicator_code) == variable_name:
                # Get description from World Bank
                description = self.data_fetcher.get_indicator_description(indicator_code)
                if description and "longDescription" in description and description["longDescription"]:
                    return description["longDescription"]
        
        # Default explanation
        return f"{variable_name.replace('_', ' ').title()} is an economic indicator tracked in the simulation."
    
    def explain_relationship(self, relationship_name: str) -> str:
        """
        Generate an explanation for an economic relationship.
        
        Args:
            relationship_name: Name of the economic relationship
            
        Returns:
            Natural language explanation
        """
        if relationship_name in self.relationship_descriptions:
            return self.relationship_descriptions[relationship_name]
        
        # Default explanation
        return f"{relationship_name.replace('_', ' ').title()} is an economic relationship modeled in the simulation."
    
    def explain_cbdc_parameter(self, parameter_name: str) -> str:
        """
        Generate an explanation for a CBDC parameter.
        
        Args:
            parameter_name: Name of the CBDC parameter
            
        Returns:
            Natural language explanation
        """
        if parameter_name in self.cbdc_parameter_descriptions:
            return self.cbdc_parameter_descriptions[parameter_name]
        
        # Default explanation
        return f"{parameter_name.replace('_', ' ').title()} is a parameter controlling CBDC behavior in the simulation."
    
    def explain_calculation(self, calculation_name: str, variables: Dict[str, float]) -> str:
        """
        Generate an explanation for an economic calculation with actual values.
        
        Args:
            calculation_name: Name of the calculation
            variables: Dictionary of variable names and their values
            
        Returns:
            Natural language explanation with formula and values
        """
        if calculation_name == "gdp_components":
            c = variables.get("consumption", 0)
            i = variables.get("investment", 0)
            g = variables.get("government_spending", 0)
            nx = variables.get("net_exports", 0)
            gdp = variables.get("gdp", 0)
            
            explanation = (
                f"GDP is calculated as the sum of Consumption ({c:.2f}), Investment ({i:.2f}), "
                f"Government Spending ({g:.2f}), and Net Exports ({nx:.2f}).\n"
                f"GDP = C + I + G + NX = {c:.2f} + {i:.2f} + {g:.2f} + {nx:.2f} = {gdp:.2f}"
            )
            return explanation
        
        elif calculation_name == "inflation_phillips_curve":
            u = variables.get("unemployment_rate", 0)
            u_n = variables.get("natural_unemployment", 0)
            pi_e = variables.get("inflation_expectations", 0)
            beta = variables.get("phillips_curve_sensitivity", 0)
            pi = variables.get("inflation_rate", 0)
            
            explanation = (
                f"Inflation is calculated using the Phillips Curve relationship.\n"
                f"The unemployment gap (actual - natural) is {u:.2f} - {u_n:.2f} = {u-u_n:.2f}%.\n"
                f"With inflation expectations of {pi_e:.2f}% and Phillips curve sensitivity of {beta:.2f},\n"
                f"Inflation = Expected Inflation + β × (Natural Unemployment - Actual Unemployment)\n"
                f"Inflation = {pi_e:.2f} + {beta:.2f} × ({u_n:.2f} - {u:.2f}) = {pi:.2f}%"
            )
            return explanation
        
        elif calculation_name == "interest_rate_policy":
            i = variables.get("inflation_rate", 0)
            i_target = variables.get("inflation_target", 2.0)
            u = variables.get("unemployment_rate", 0)
            u_n = variables.get("natural_unemployment", 0)
            r_neutral = variables.get("neutral_interest_rate", 2.0)
            alpha_i = variables.get("inflation_response", 1.5)
            alpha_u = variables.get("unemployment_response", 0.5)
            r = variables.get("policy_rate", 0)
            
            explanation = (
                f"The policy interest rate is set according to a Taylor-type rule that responds to\n"
                f"inflation and unemployment gaps.\n"
                f"With inflation of {i:.2f}% (target: {i_target:.2f}%) and unemployment of {u:.2f}% (natural: {u_n:.2f}%),\n"
                f"Policy Rate = Neutral Rate + α_i × (Inflation - Target) - α_u × (Unemployment - Natural)\n"
                f"Policy Rate = {r_neutral:.2f} + {alpha_i:.2f} × ({i:.2f} - {i_target:.2f}) - {alpha_u:.2f} × ({u:.2f} - {u_n:.2f}) = {r:.2f}%"
            )
            return explanation
        
        elif calculation_name == "exchange_rate_determination":
            r_domestic = variables.get("interest_rate", 0)
            r_foreign = variables.get("foreign_interest_rate", 0)
            ca = variables.get("current_account", 0)
            e = variables.get("exchange_rate", 0)
            
            explanation = (
                f"The exchange rate is influenced by interest rate differentials and the current account balance.\n"
                f"With domestic interest rate of {r_domestic:.2f}%, foreign interest rate of {r_foreign:.2f}%,\n"
                f"and current account balance of {ca:.2f} billion,\n"
                f"a higher domestic interest rate tends to appreciate the currency (lower exchange rate value if quoted as domestic/foreign),\n"
                f"while a current account deficit tends to depreciate it.\n"
                f"The resulting exchange rate is {e:.4f}."
            )
            return explanation
        
        elif calculation_name == "cbdc_bank_disintermediation":
            cbdc_rate = variables.get("cbdc_interest_rate", 0)
            deposit_rate = variables.get("deposit_interest_rate", 0)
            disint_factor = variables.get("cbdc_disintermediation_factor", 0)
            deposits = variables.get("bank_deposits", 0)
            cbdc = variables.get("cbdc_supply", 0)
            
            explanation = (
                f"CBDC can cause bank disintermediation when its interest rate exceeds bank deposit rates.\n"
                f"With CBDC interest rate of {cbdc_rate:.2f}% and deposit interest rate of {deposit_rate:.2f}%,\n"
                f"the interest rate differential is {cbdc_rate-deposit_rate:.2f}%.\n"
                f"Given a disintermediation factor of {disint_factor:.2f}, this results in\n"
                f"bank deposits of {deposits:.2f} billion and CBDC holdings of {cbdc:.2f} billion."
            )
            return explanation
        
        # Default explanation
        return f"{calculation_name.replace('_', ' ').title()} is calculated based on economic relationships in the simulation model."
    
    def explain_parameter_change(self, parameter_name: str, old_value: float, new_value: float) -> str:
        """
        Generate an explanation for the impact of changing a parameter.
        
        Args:
            parameter_name: Name of the parameter being changed
            old_value: Previous parameter value
            new_value: New parameter value
            
        Returns:
            Natural language explanation of likely impacts
        """
        # CBDC interest rate
        if parameter_name == "cbdc_interest_rate":
            if new_value > old_value:
                return (
                    f"Increasing the CBDC interest rate from {old_value:.2f}% to {new_value:.2f}% will make CBDC more attractive as a store of value. "
                    f"This is likely to increase CBDC adoption but may cause bank disintermediation as funds flow from bank deposits to CBDC. "
                    f"Higher CBDC interest rates may also tighten monetary conditions, potentially reducing inflation but slowing economic growth."
                )
            else:
                return (
                    f"Decreasing the CBDC interest rate from {old_value:.2f}% to {new_value:.2f}% will make CBDC less attractive as a store of value. "
                    f"This may reduce CBDC adoption but support bank deposits and lending. "
                    f"Lower CBDC interest rates may also ease monetary conditions, potentially supporting economic growth but possibly increasing inflation."
                )
        
        # Programmable money validity
        elif parameter_name == "programmable_money_validity":
            if new_value < old_value:
                return (
                    f"Reducing the CBDC validity period from {old_value} days to {new_value} days will increase the velocity of money circulation. "
                    f"This encourages spending rather than saving, potentially stimulating economic activity but possibly increasing inflation. "
                    f"Shorter validity periods give the central bank more direct control over money velocity."
                )
            else:
                return (
                    f"Increasing the CBDC validity period from {old_value} days to {new_value} days will reduce pressure on money velocity. "
                    f"This allows more saving behavior, potentially reducing inflationary pressures but possibly reducing short-term economic activity. "
                    f"Longer validity periods give users more flexibility in their financial planning."
                )
        
        # Conditional spending constraints
        elif parameter_name == "conditional_spending_constraints":
            if new_value > old_value:
                return (
                    f"Increasing conditional spending constraints from {old_value:.2f} to {new_value:.2f} will direct more CBDC spending toward specific sectors or purposes. "
                    f"This enables more targeted economic stimulus and policy implementation but reduces user flexibility. "
                    f"Stronger constraints may reduce overall consumption in the short term but potentially improve policy effectiveness."
                )
            else:
                return (
                    f"Decreasing conditional spending constraints from {old_value:.2f} to {new_value:.2f} will give CBDC users more flexibility in how they spend. "
                    f"This increases user autonomy but reduces the central bank's ability to implement targeted policies. "
                    f"Weaker constraints may increase overall consumption in the short term but potentially reduce policy effectiveness."
                )
        
        # Automatic fiscal transfers
        elif parameter_name == "automatic_fiscal_transfers":
            if new_value > old_value:
                return (
                    f"Increasing automatic fiscal transfers from {old_value:.2f} to {new_value:.2f} will inject more money directly into the economy through CBDC. "
                    f"This provides direct stimulus, potentially increasing consumption and economic activity. "
                    f"Higher transfers may support growth and reduce unemployment but could increase inflation and government debt."
                )
            else:
                return (
                    f"Decreasing automatic fiscal transfers from {old_value:.2f} to {new_value:.2f} will reduce direct money injection into the economy. "
                    f"This reduces fiscal stimulus, potentially decreasing consumption and economic activity in the short term. "
                    f"Lower transfers may reduce inflation pressures and government debt but could slow growth and increase unemployment."
                )
        
        # Smart contract based lending
        elif parameter_name == "smart_contract_based_lending":
            if new_value > old_value:
                return (
                    f"Increasing smart contract based lending from {old_value:.2f} to {new_value:.2f} will expand automated lending through the CBDC system. "
                    f"This may increase credit availability, potentially bypassing traditional banking channels. "
                    f"Higher smart contract lending could support investment and growth but may introduce new financial stability risks."
                )
            else:
                return (
                    f"Decreasing smart contract based lending from {old_value:.2f} to {new_value:.2f} will reduce automated lending through the CBDC system. "
                    f"This may decrease credit availability outside traditional banking channels. "
                    f"Lower smart contract lending could reduce financial innovation but may enhance financial stability."
                )
        
        # Foreign exchange controls
        elif parameter_name == "foreign_exchange_controls":
            if new_value > old_value:
                return (
                    f"Increasing foreign exchange controls from {old_value:.2f} to {new_value:.2f} will restrict cross-border CBDC flows. "
                    f"This gives the central bank more control over capital movements and exchange rate management. "
                    f"Stronger controls may stabilize the domestic currency and reduce volatility but could reduce international integration."
                )
            else:
                return (
                    f"Decreasing foreign exchange controls from {old_value:.2f} to {new_value:.2f} will liberalize cross-border CBDC flows. "
                    f"This reduces central bank control over capital movements but increases international integration. "
                    f"Weaker controls may enhance cross-border trade and investment but could increase exchange rate volatility."
                )
        
        # Tariff rate
        elif parameter_name == "tariff_rate":
            if new_value > old_value:
                return (
                    f"Increasing the tariff rate from {old_value:.2f} to {new_value:.2f} will raise the cost of imported goods. "
                    f"This may protect domestic industries but increase prices for consumers and potentially trigger retaliatory measures. "
                    f"Higher tariffs typically reduce imports, improve the trade balance in the short term, but may reduce economic efficiency."
                )
            else:
                return (
                    f"Decreasing the tariff rate from {old_value:.2f} to {new_value:.2f} will reduce the cost of imported goods. "
                    f"This may increase competition for domestic industries but lower prices for consumers and improve international relations. "
                    f"Lower tariffs typically increase imports, potentially worsening the trade balance in the short term, but may improve economic efficiency."
                )
        
        # Capital requirement
        elif parameter_name == "capital_requirement":
            if new_value > old_value:
                return (
                    f"Increasing the capital requirement from {old_value:.2f} to {new_value:.2f} will require banks to hold more capital relative to their assets. "
                    f"This enhances financial stability and bank resilience to shocks but may reduce lending capacity. "
                    f"Higher capital requirements typically make the banking system safer but could constrain credit growth and economic activity."
                )
            else:
                return (
                    f"Decreasing the capital requirement from {old_value:.2f} to {new_value:.2f} will allow banks to hold less capital relative to their assets. "
                    f"This may increase lending capacity but reduces bank resilience to shocks. "
                    f"Lower capital requirements typically expand credit availability but could increase financial stability risks."
                )
        
        # Default explanation
        return (
            f"Changing {parameter_name.replace('_', ' ')} from {old_value} to {new_value} will affect the economy through various channels. "
            f"The simulation will show the combined effects of this change on economic variables like GDP, inflation, unemployment, and financial stability."
        )
    
    def explain_simulation_results(self, initial_state: Dict[str, float], final_state: Dict[str, float], time_horizon: int) -> str:
        """
        Generate a comprehensive explanation of simulation results.
        
        Args:
            initial_state: Dictionary of initial economic variables
            final_state: Dictionary of final economic variables
            time_horizon: Simulation time horizon in quarters
            
        Returns:
            Natural language explanation of simulation outcomes
        """
        # Calculate key changes
        gdp_growth = ((final_state.get("gdp", 0) / initial_state.get("gdp", 1)) - 1) * 100
        annual_gdp_growth = (((final_state.get("gdp", 0) / initial_state.get("gdp", 1)) ** (4 / time_horizon)) - 1) * 100
        inflation_change = final_state.get("inflation_rate", 0) - initial_state.get("inflation_rate", 0)
        unemployment_change = final_state.get("unemployment_rate", 0) - initial_state.get("unemployment_rate", 0)
        cbdc_adoption = (final_state.get("cbdc_supply", 0) / final_state.get("money_supply", 1)) * 100
        
        # Generate explanation
        explanation = [
            f"## Simulation Results Summary ({time_horizon} quarters)",
            "",
            f"### Economic Growth",
            f"The economy grew from ${initial_state.get('gdp', 0):.2f} billion to ${final_state.get('gdp', 0):.2f} billion, ",
            f"a total growth of {gdp_growth:.2f}% over {time_horizon} quarters ({annual_gdp_growth:.2f}% annualized).",
            "",
            f"### Inflation and Unemployment",
            f"Inflation {'increased' if inflation_change > 0 else 'decreased'} from {initial_state.get('inflation_rate', 0):.2f}% to {final_state.get('inflation_rate', 0):.2f}%, ",
            f"a change of {abs(inflation_change):.2f} percentage points.",
            f"Unemployment {'increased' if unemployment_change > 0 else 'decreased'} from {initial_state.get('unemployment_rate', 0):.2f}% to {final_state.get('unemployment_rate', 0):.2f}%, ",
            f"a change of {abs(unemployment_change):.2f} percentage points.",
            "",
            f"### CBDC Adoption",
            f"CBDC adoption reached {cbdc_adoption:.2f}% of the total money supply by the end of the simulation.",
            f"The CBDC supply grew from ${initial_state.get('cbdc_supply', 0):.2f} billion to ${final_state.get('cbdc_supply', 0):.2f} billion.",
            "",
            f"### Banking Sector",
            f"Bank deposits changed from ${initial_state.get('bank_deposits', 0):.2f} billion to ${final_state.get('bank_deposits', 0):.2f} billion, ",
            f"while bank loans changed from ${initial_state.get('bank_loans', 0):.2f} billion to ${final_state.get('bank_loans', 0):.2f} billion.",
            "",
            f"### International Position",
            f"The exchange rate moved from {initial_state.get('exchange_rate', 1):.4f} to {final_state.get('exchange_rate', 1):.4f}.",
            f"Net exports changed from ${initial_state.get('net_exports', 0):.2f} billion to ${final_state.get('net_exports', 0):.2f} billion.",
            "",
            f"### Financial Stability",
            f"The financial stress index changed from {initial_state.get('financial_stress_index', 0):.2f} to {final_state.get('financial_stress_index', 0):.2f}."
        ]
        
        return "\n".join(explanation)
    
    def generate_policy_recommendations(self, simulation_results: pd.DataFrame, cbdc_params: Dict[str, float]) -> str:
        """
        Generate policy recommendations based on simulation results.
        
        Args:
            simulation_results: DataFrame with simulation results
            cbdc_params: Dictionary of CBDC parameters used in the simulation
            
        Returns:
            Natural language policy recommendations
        """
        # Extract final values and calculate key metrics
        final_values = simulation_results.iloc[-1]
        
        gdp_growth = simulation_results["gdp"].pct_change().mean() * 400  # Annualized
        inflation = final_values.get("inflation_rate", 0)
        unemployment = final_values.get("unemployment_rate", 0)
        financial_stress = final_values.get("financial_stress_index", 0)
        
        # Generate recommendations
        recommendations = [
            "## Policy Recommendations Based on Simulation Results",
            ""
        ]
        
        # Growth recommendations
        recommendations.append("### Economic Growth")
        if gdp_growth < 1.0:
            recommendations.append("The simulation shows weak economic growth, suggesting stimulus measures may be needed:")
            recommendations.append("- Consider lowering CBDC interest rates to stimulate spending")
            recommendations.append("- Increase automatic fiscal transfers through CBDC")
            recommendations.append("- Reduce programmable money validity period to increase velocity")
        elif gdp_growth > 4.0:
            recommendations.append("The simulation shows strong economic growth, suggesting potential overheating:")
            recommendations.append("- Consider raising CBDC interest rates to moderate spending")
            recommendations.append("- Reduce automatic fiscal transfers")
            recommendations.append("- Implement targeted spending constraints to channel activity to productive sectors")
        else:
            recommendations.append("The simulation shows moderate, sustainable economic growth:")
            recommendations.append("- Maintain current CBDC parameters to support continued growth")
            recommendations.append("- Fine-tune automatic fiscal transfers to address specific sectors as needed")
        
        recommendations.append("")
        
        # Inflation recommendations
        recommendations.append("### Inflation Management")
        if inflation > 3.0:
            recommendations.append("The simulation shows above-target inflation:")
            recommendations.append("- Increase CBDC interest rates to reduce spending")
            recommendations.append("- Implement stronger conditional spending constraints")
            recommendations.append("- Consider using inflation-indexed CBDC instruments")
        elif inflation < 1.0:
            recommendations.append("The simulation shows below-target inflation:")
            recommendations.append("- Decrease CBDC interest rates to encourage spending")
            recommendations.append("- Increase automatic fiscal transfers")
            recommendations.append("- Reduce programmable money validity to increase velocity")
        else:
            recommendations.append("The simulation shows inflation near target levels:")
            recommendations.append("- Maintain current CBDC interest rate policy")
            recommendations.append("- Monitor inflation expectations closely")
        
        recommendations.append("")
        
        # Banking sector recommendations
        recommendations.append("### Banking Sector Stability")
        if financial_stress > 0.5:
            recommendations.append("The simulation shows elevated financial stress:")
            recommendations.append("- Adjust CBDC interest rates to reduce competition with bank deposits")
            recommendations.append("- Implement macroprudential tools through CBDC")
            recommendations.append("- Consider emergency liquidity provisions")
        else:
            recommendations.append("The simulation shows stable financial conditions:")
            recommendations.append("- Gradually increase CBDC adoption while monitoring bank disintermediation")
            recommendations.append("- Develop complementary roles for CBDC and bank deposits")
            recommendations.append("- Explore smart contract lending to enhance financial inclusion")
        
        recommendations.append("")
        
        # International recommendations
        recommendations.append("### International Position")
        exchange_rate_volatility = simulation_results["exchange_rate"].pct_change().std()
        if exchange_rate_volatility > 0.02:
            recommendations.append("The simulation shows significant exchange rate volatility:")
            recommendations.append("- Consider implementing foreign exchange controls for CBDC")
            recommendations.append("- Develop international CBDC coordination mechanisms")
            recommendations.append("- Use CBDC for trade settlement to reduce forex exposure")
        else:
            recommendations.append("The simulation shows stable international conditions:")
            recommendations.append("- Gradually increase CBDC use in international settlements")
            recommendations.append("- Develop cross-border CBDC protocols")
            recommendations.append("- Monitor capital flows as CBDC adoption increases")
        
        return "\n".join(recommendations)


# Example usage
if __name__ == "__main__":
    # Initialize data fetcher
    data_fetcher = WorldBankDataFetcher()
    
    # Get data for a country
    country_data = data_fetcher.get_country_data("USA")
    
    # Convert to simulation state
    simulation_state = data_fetcher.convert_to_simulation_state(country_data)
    
    # Print results
    print("Country Data:")
    for key, value in country_data.items():
        print(f"  {key}: {value}")
    
    print("\nSimulation State:")
    for key, value in simulation_state.items():
        print(f"  {key}: {value}")
    
    # Initialize data explainer
    explainer = DataExplainer(data_fetcher)
    
    # Generate explanations
    print("\nVariable Explanation:")
    print(explainer.explain_variable("inflation_rate"))
    
    print("\nCalculation Explanation:")
    variables = {
        "consumption": 12000,
        "investment": 4000,
        "government_spending": 3000,
        "net_exports": -500,
        "gdp": 18500
    }
    print(explainer.explain_calculation("gdp_components", variables))
    
    print("\nParameter Change Explanation:")
    print(explainer.explain_parameter_change("cbdc_interest_rate", 0.0, 2.0))
