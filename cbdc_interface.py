"""
CBDC Economic Simulation Interface

This module provides a graphical user interface for the CBDC economic simulation system.
It allows users to configure simulation parameters, run scenarios, and visualize results.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import threading
import time

# Import the simulation system
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cbdc_simulation import (
    SimulationConfig, CBDCParameters, TradeParameters, 
    BankingParameters, MacroParameters, EconomicState,
    CBDCSimulation, create_default_config,
    create_cbdc_adoption_scenario,
    create_trade_war_scenario,
    create_banking_crisis_scenario
)

# Ensure Tkinter main loop runs even if matplotlib is imported
import matplotlib
matplotlib.use('TkAgg')

class ScrollableFrame(ttk.Frame):
    """A scrollable frame widget."""
    
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # Create the scrollable frame
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        # Add the scrollable frame to the canvas
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # Configure the canvas to use the scrollbar
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack the canvas and scrollbar
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind canvas size changes to adjust the inner frame
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        # Bind mouse wheel to scrolling
        self.bind_mousewheel()
    
    def _on_canvas_configure(self, event):
        """Adjust the width of the inner frame to fill the canvas."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_frame, width=canvas_width)
    
    def bind_mousewheel(self):
        """Bind mouse wheel events to the canvas."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def unbind_mousewheel(self):
        """Unbind mouse wheel events from the canvas."""
        self.canvas.unbind_all("<MouseWheel>")

class ParameterSection:
    """A section of related parameters in the UI."""
    
    def __init__(self, parent, title, parameters, initial_values=None):
        """
        Initialize a parameter section.
        
        Args:
            parent: Parent widget
            title: Section title
            parameters: Dict of parameter names and their metadata
            initial_values: Dict of initial values for parameters
        """
        self.parent = parent
        self.title = title
        self.parameters = parameters
        self.initial_values = initial_values or {}
        self.controls = {}
        
        self._create_section()
    
    def _create_section(self):
        """Create the section UI elements."""
        # Create a labeled frame for the section
        self.frame = ttk.LabelFrame(self.parent, text=self.title)
        self.frame.pack(fill="x", padx=10, pady=5)
        
        # Create controls for each parameter
        for i, (param_name, param_meta) in enumerate(self.parameters.items()):
            # Create a frame for this parameter
            param_frame = ttk.Frame(self.frame)
            param_frame.pack(fill="x", padx=5, pady=2)
            
            # Add label
            label = ttk.Label(param_frame, text=param_meta.get("label", param_name), width=30, anchor="w")
            label.pack(side="left", padx=5)
            
            # Get initial value
            initial_value = self.initial_values.get(param_name, param_meta.get("default", 0.0))
            
            # Create appropriate control based on parameter type
            param_type = param_meta.get("type", "float")
            
            if param_type == "float" or param_type == "int":
                # Create a scale for numeric parameters
                min_val = param_meta.get("min", 0.0)
                max_val = param_meta.get("max", 10.0)
                resolution = param_meta.get("resolution", 0.1 if param_type == "float" else 1)
                
                var = tk.DoubleVar(value=float(initial_value))
                scale = ttk.Scale(
                    param_frame, 
                    from_=min_val, 
                    to=max_val, 
                    variable=var,
                    orient="horizontal"
                )
                scale.pack(side="left", fill="x", expand=True, padx=5)
                
                # Add a label to show the current value
                value_label = ttk.Label(param_frame, width=8)
                value_label.pack(side="left", padx=5)
                
                # Update the value label when the scale changes
                def update_value_label(var_name=None, index=None, mode=None):
                    value = var.get()
                    if param_type == "int":
                        value_label.config(text=f"{int(value)}")
                    else:
                        value_label.config(text=f"{value:.2f}")
                
                var.trace_add("write", update_value_label)
                update_value_label()  # Initial update
                
                self.controls[param_name] = {
                    "var": var,
                    "widget": scale,
                    "value_label": value_label,
                    "type": param_type
                }
                
            elif param_type == "choice":
                # Create a combobox for choice parameters
                choices = param_meta.get("choices", [])
                
                var = tk.StringVar(value=str(initial_value))
                combo = ttk.Combobox(
                    param_frame, 
                    textvariable=var,
                    values=choices,
                    state="readonly",
                    width=20
                )
                combo.pack(side="left", fill="x", expand=True, padx=5)
                
                self.controls[param_name] = {
                    "var": var,
                    "widget": combo,
                    "type": param_type
                }
                
            elif param_type == "boolean":
                # Create a checkbox for boolean parameters
                var = tk.BooleanVar(value=bool(initial_value))
                check = ttk.Checkbutton(
                    param_frame,
                    variable=var
                )
                check.pack(side="left", padx=5)
                
                self.controls[param_name] = {
                    "var": var,
                    "widget": check,
                    "type": param_type
                }
            
            # Add tooltip if provided
            if "tooltip" in param_meta:
                self._add_tooltip(label, param_meta["tooltip"])
                
    def _add_tooltip(self, widget, text):
        """Add a tooltip to a widget."""
        tooltip = tk.Label(
            widget, 
            text=text, 
            background="#FFFFEA", 
            relief="solid", 
            borderwidth=1,
            wraplength=300
        )
        tooltip.place_forget()
        
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            tooltip.place(x=x, y=y)
        
        def leave(event):
            tooltip.place_forget()
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def get_values(self):
        """Get the current values of all parameters in this section."""
        values = {}
        for param_name, control in self.controls.items():
            var = control["var"]
            param_type = control["type"]
            
            if param_type == "float":
                values[param_name] = float(var.get())
            elif param_type == "int":
                values[param_name] = int(var.get())
            elif param_type == "choice":
                values[param_name] = var.get()
            elif param_type == "boolean":
                values[param_name] = bool(var.get())
        
        return values
    
    def set_values(self, values):
        """Set the values of parameters from a dictionary."""
        for param_name, value in values.items():
            if param_name in self.controls:
                control = self.controls[param_name]
                var = control["var"]
                
                try:
                    var.set(value)
                except Exception as e:
                    print(f"Error setting {param_name} to {value}: {e}")

class CBDCSimulationApp(tk.Tk):
    """Main application for the CBDC economic simulation."""
    
    def __init__(self):
        super().__init__()
        
        # Configure the main window
        self.title("CBDC Economic Simulation")
        self.geometry("1600x900")
        self.minsize(1200, 800)
        
        # Initialize simulation state
        self.simulation = None
        self.simulation_thread = None
        self.simulation_running = False
        self.results = None
        
        # Create the main UI
        self.create_widgets()
        
        # Load default configuration
        self.load_default_config()
    
    def create_widgets(self):
        """Create the main UI widgets."""
        # Create main frame
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)
        
        # Create left panel for controls
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="y", padx=10, pady=10)
        
        # Create right panel for visualization
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame for parameters
        self.param_scroll = ScrollableFrame(left_panel)
        self.param_scroll.pack(fill="both", expand=True, pady=10)
        
        # Create control buttons
        control_frame = ttk.Frame(left_panel)
        control_frame.pack(fill="x", pady=10)
        
        # Add scenario selection
        scenario_frame = ttk.Frame(control_frame)
        scenario_frame.pack(fill="x", pady=5)
        
        ttk.Label(scenario_frame, text="Scenario:").pack(side="left", padx=5)
        
        self.scenario_var = tk.StringVar(value="Default")
        scenario_combo = ttk.Combobox(
            scenario_frame,
            textvariable=self.scenario_var,
            values=["Default", "CBDC Adoption", "Trade War", "Banking Crisis", "Custom"],
            state="readonly",
            width=20
        )
        scenario_combo.pack(side="left", fill="x", expand=True, padx=5)
        scenario_combo.bind("<<ComboboxSelected>>", self.on_scenario_selected)
        
        # Add load/save buttons
        file_frame = ttk.Frame(control_frame)
        file_frame.pack(fill="x", pady=5)
        
        ttk.Button(file_frame, text="Load Config", command=self.load_config).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Save Config", command=self.save_config).pack(side="left", padx=5)
        
        # Add run button
        run_frame = ttk.Frame(control_frame)
        run_frame.pack(fill="x", pady=5)
        
        self.run_button = ttk.Button(run_frame, text="Run Simulation", command=self.run_simulation)
        self.run_button.pack(fill="x", pady=5)
        
        # Create tabs for visualization
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self.results_tab = ttk.Frame(self.notebook)
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.details_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.details_tab, text="Details")
        
        # Create dashboard content
        self.create_dashboard()
        
        # Create results content
        self.create_results_view()
        
        # Create details content
        self.create_details_view()
        
        # Create parameter sections
        self.create_parameter_sections()
    
    def create_dashboard(self):
        """Create the dashboard tab content."""
        # Create a frame for the dashboard
        dashboard_frame = ttk.Frame(self.dashboard_tab)
        dashboard_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a frame for the charts
        charts_frame = ttk.Frame(dashboard_frame)
        charts_frame.pack(fill="both", expand=True)
        
        # Create placeholder for charts
        self.dashboard_figures = []
        self.dashboard_canvases = []
        
        # Create 2x2 grid of charts
        for i in range(4):
            frame = ttk.Frame(charts_frame)
            frame.grid(row=i//2, column=i%2, sticky="nsew", padx=5, pady=5)
            
            fig = plt.Figure(figsize=(6, 4), dpi=100)
            ax = fig.add_subplot(111)
            ax.set_title(f"Chart {i+1}")
            ax.text(0.5, 0.5, "No data available", ha="center", va="center")
            
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
            self.dashboard_figures.append(fig)
            self.dashboard_canvases.append(canvas)
        
        # Configure grid
        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        charts_frame.rowconfigure(0, weight=1)
        charts_frame.rowconfigure(1, weight=1)
        
        # Create a frame for key metrics
        metrics_frame = ttk.LabelFrame(dashboard_frame, text="Key Metrics")
        metrics_frame.pack(fill="x", pady=10)
        
        # Create placeholders for metrics
        self.metrics_labels = {}
        metrics = [
            "GDP Growth", "Inflation Rate", "Unemployment Rate", 
            "Interest Rate", "CBDC Adoption", "Financial Stability"
        ]
        
        for i, metric in enumerate(metrics):
            frame = ttk.Frame(metrics_frame)
            frame.grid(row=i//3, column=i%3, sticky="nsew", padx=10, pady=5)
            
            ttk.Label(frame, text=f"{metric}:").pack(anchor="w")
            value_label = ttk.Label(frame, text="N/A", font=("Arial", 12, "bold"))
            value_label.pack(anchor="w")
            
            self.metrics_labels[metric] = value_label
        
        # Configure grid
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)
    
    def create_results_view(self):
        """Create the results tab content."""
        # Create a frame for the results
        results_frame = ttk.Frame(self.results_tab)
        results_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create controls for selecting variables to plot
        controls_frame = ttk.Frame(results_frame)
        controls_frame.pack(fill="x", pady=10)
        
        ttk.Label(controls_frame, text="Select variables to plot:").pack(side="left", padx=5)
        
        self.var_listbox = tk.Listbox(controls_frame, selectmode="multiple", height=5)
        self.var_listbox.pack(side="left", fill="x", expand=True, padx=5)
        
        # Add a scrollbar to the listbox
        var_scrollbar = ttk.Scrollbar(controls_frame, orient="vertical", command=self.var_listbox.yview)
        var_scrollbar.pack(side="left", fill="y")
        self.var_listbox.config(yscrollcommand=var_scrollbar.set)
        
        # Add plot button
        ttk.Button(controls_frame, text="Plot Selected", command=self.plot_selected_variables).pack(side="left", padx=5)
        
        # Create a frame for the plot
        plot_frame = ttk.Frame(results_frame)
        plot_frame.pack(fill="both", expand=True, pady=10)
        
        # Create placeholder for plot
        self.results_figure = plt.Figure(figsize=(10, 6), dpi=100)
        self.results_canvas = FigureCanvasTkAgg(self.results_figure, master=plot_frame)
        self.results_canvas.draw()
        self.results_canvas.get_tk_widget().pack(fill="both", expand=True)
    
    def create_details_view(self):
        """Create the details tab content."""
        # Create a frame for the details
        details_frame = ttk.Frame(self.details_tab)
        details_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a text widget for displaying details
        self.details_text = tk.Text(details_frame, wrap="word", height=20)
        self.details_text.pack(fill="both", expand=True, pady=10)
        
        # Add a scrollbar to the text widget
        details_scrollbar = ttk.Scrollbar(self.details_text, orient="vertical", command=self.details_text.yview)
        details_scrollbar.pack(side="right", fill="y")
        self.details_text.config(yscrollcommand=details_scrollbar.set)
        
        # Make the text widget read-only
        self.details_text.config(state="disabled")
    
    def create_parameter_sections(self):
        """Create the parameter sections."""
        # Define parameter metadata
        simulation_params = {
            "time_horizon": {
                "label": "Time Horizon (quarters)",
                "type": "int",
                "min": 4,
                "max": 100,
                "default": 20,
                "tooltip": "Number of quarters to simulate"
            },
            "random_seed": {
                "label": "Random Seed",
                "type": "int",
                "min": 0,
                "max": 1000,
                "default": 42,
                "tooltip": "Seed for random number generation"
            }
        }
        
        macro_params = {
            "autonomous_consumption": {
                "label": "Autonomous Consumption",
                "type": "float",
                "min": 500,
                "max": 5000,
                "default": 1500,
                "tooltip": "Base level of consumption independent of income"
            },
            "marginal_propensity_to_consume": {
                "label": "Marginal Propensity to Consume",
                "type": "float",
                "min": 0.1,
                "max": 0.9,
                "default": 0.6,
                "tooltip": "Fraction of additional income that is consumed"
            },
            "autonomous_investment": {
                "label": "Autonomous Investment",
                "type": "float",
                "min": 500,
                "max": 5000,
                "default": 2000,
                "tooltip": "Base level of investment independent of interest rates"
            },
            "investment_interest_sensitivity": {
                "label": "Investment Interest Sensitivity",
                "type": "float",
                "min": 10,
                "max": 500,
                "default": 100,
                "tooltip": "How much investment changes with interest rates"
            },
            "phillips_curve_sensitivity": {
                "label": "Phillips Curve Sensitivity",
                "type": "float",
                "min": 0.1,
                "max": 2.0,
                "default": 0.5,
                "tooltip": "Relationship between unemployment and inflation"
            },
            "natural_unemployment": {
                "label": "Natural Unemployment Rate (%)",
                "type": "float",
                "min": 2.0,
                "max": 10.0,
                "default": 4.0,
                "tooltip": "Unemployment rate consistent with stable inflation"
            },
            "potential_output_growth": {
                "label": "Potential Output Growth (%)",
                "type": "float",
                "min": 0.0,
                "max": 10.0,
                "default": 2.5,
                "tooltip": "Annual growth rate of potential GDP"
            }
        }
        
        cbdc_params = {
            "cbdc_interest_rate": {
                "label": "CBDC Interest Rate (%)",
                "type": "float",
                "min": -2.0,
                "max": 5.0,
                "default": 0.0,
                "tooltip": "Interest rate paid on CBDC balances"
            },
            "programmable_money_validity": {
                "label": "Money Validity Period (days)",
                "type": "int",
                "min": 30,
                "max": 365,
                "default": 365,
                "tooltip": "How long CBDC remains valid before expiring"
            },
            "conditional_spending_constraints": {
                "label": "Spending Constraints",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "tooltip": "Restrictions on how CBDC can be spent (0-1)"
            },
            "automatic_fiscal_transfers": {
                "label": "Automatic Fiscal Transfers",
                "type": "float",
                "min": 0.0,
                "max": 1000.0,
                "default": 0.0,
                "tooltip": "Automatic payments through CBDC"
            },
            "smart_contract_based_lending": {
                "label": "Smart Contract Lending",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "tooltip": "Automated lending through smart contracts (0-1)"
            },
            "foreign_exchange_controls": {
                "label": "Foreign Exchange Controls",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "tooltip": "Restrictions on cross-border flows (0-1)"
            },
            "macroprudential_tools": {
                "label": "Macroprudential Tools",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "tooltip": "System-wide financial stability tools (0-1)"
            },
            "emergency_override_mechanisms": {
                "label": "Emergency Override",
                "type": "float",
                "min": -5.0,
                "max": 5.0,
                "default": 0.0,
                "tooltip": "Emergency policy adjustments (-5 to +5)"
            },
            "programmable_asset_purchases": {
                "label": "Programmable Asset Purchases",
                "type": "float",
                "min": 0.0,
                "max": 1000.0,
                "default": 0.0,
                "tooltip": "Central bank asset purchases via CBDC"
            }
        }
        
        trade_params = {
            "tariff_rate": {
                "label": "Tariff Rate",
                "type": "float",
                "min": 0.0,
                "max": 0.5,
                "default": 0.05,
                "tooltip": "Average tariff rate on imports (0-0.5)"
            },
            "customs_efficiency": {
                "label": "Customs Efficiency",
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.8,
                "tooltip": "Efficiency of customs processing (0-1)"
            },
            "exchange_rate_regime": {
                "label": "Exchange Rate Regime",
                "type": "choice",
                "choices": ["floating", "managed", "fixed"],
                "default": "floating",
                "tooltip": "Type of exchange rate system"
            },
            "exchange_rate_target": {
                "label": "Exchange Rate Target",
                "type": "float",
                "min": 0.5,
                "max": 2.0,
                "default": 1.0,
                "tooltip": "Target exchange rate for managed/fixed regimes"
            },
            "capital_flow_controls": {
                "label": "Capital Flow Controls",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "tooltip": "Restrictions on capital flows (0-1)"
            },
            "cbdc_trade_settlement": {
                "label": "CBDC Trade Settlement",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.0,
                "tooltip": "Use of CBDC for international settlement (0-1)"
            }
        }
        
        banking_params = {
            "capital_requirement": {
                "label": "Capital Requirement",
                "type": "float",
                "min": 0.04,
                "max": 0.2,
                "default": 0.08,
                "tooltip": "Minimum capital ratio for banks"
            },
            "reserve_requirement": {
                "label": "Reserve Requirement",
                "type": "float",
                "min": 0.0,
                "max": 0.2,
                "default": 0.02,
                "tooltip": "Required reserves as fraction of deposits"
            },
            "lending_risk_appetite": {
                "label": "Lending Risk Appetite",
                "type": "float",
                "min": 0.1,
                "max": 1.0,
                "default": 0.5,
                "tooltip": "Banks' willingness to take lending risks (0-1)"
            },
            "cbdc_disintermediation_factor": {
                "label": "CBDC Disintermediation Factor",
                "type": "float",
                "min": 0.0,
                "max": 1.0,
                "default": 0.2,
                "tooltip": "How much CBDC competes with bank deposits (0-1)"
            },
            "quantitative_easing": {
                "label": "Quantitative Easing (% of GDP)",
                "type": "float",
                "min": 0.0,
                "max": 0.2,
                "default": 0.0,
                "tooltip": "Central bank asset purchases as % of GDP"
            }
        }
        
        initial_state_params = {
            "gdp": {
                "label": "Initial GDP",
                "type": "float",
                "min": 10000,
                "max": 30000,
                "default": 20000,
                "tooltip": "Starting level of GDP"
            },
            "inflation_rate": {
                "label": "Initial Inflation Rate (%)",
                "type": "float",
                "min": 0.0,
                "max": 10.0,
                "default": 2.0,
                "tooltip": "Starting inflation rate"
            },
            "unemployment_rate": {
                "label": "Initial Unemployment Rate (%)",
                "type": "float",
                "min": 2.0,
                "max": 10.0,
                "default": 4.0,
                "tooltip": "Starting unemployment rate"
            },
            "interest_rate": {
                "label": "Initial Interest Rate (%)",
                "type": "float",
                "min": 0.0,
                "max": 10.0,
                "default": 2.5,
                "tooltip": "Starting interest rate"
            },
            "government_spending": {
                "label": "Government Spending",
                "type": "float",
                "min": 2000,
                "max": 6000,
                "default": 4000,
                "tooltip": "Initial government spending level"
            },
            "tax_revenue": {
                "label": "Tax Revenue",
                "type": "float",
                "min": 2000,
                "max": 5000,
                "default": 3500,
                "tooltip": "Initial tax revenue level"
            },
            "cbdc_supply": {
                "label": "Initial CBDC Supply",
                "type": "float",
                "min": 0,
                "max": 5000,
                "default": 0,
                "tooltip": "Starting amount of CBDC in circulation"
            }
        }
        
        # Create parameter sections
        self.param_sections = {}
        
        self.param_sections["simulation"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Simulation Settings",
            simulation_params
        )
        
        self.param_sections["initial_state"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Initial Economic State",
            initial_state_params
        )
        
        self.param_sections["macro"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Macroeconomic Parameters",
            macro_params
        )
        
        self.param_sections["cbdc"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "CBDC Parameters",
            cbdc_params
        )
        
        self.param_sections["trade"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "International Trade Parameters",
            trade_params
        )
        
        self.param_sections["banking"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Banking Sector Parameters",
            banking_params
        )
    
    def load_default_config(self):
        """Load the default configuration."""
        config = create_default_config()
        self.apply_config(config)
    
    def apply_config(self, config):
        """Apply a configuration to the UI."""
        # Apply simulation parameters
        sim_values = {
            "time_horizon": config.time_horizon,
            "random_seed": config.random_seed
        }
        self.param_sections["simulation"].set_values(sim_values)
        
        # Apply initial state parameters
        state_dict = config.initial_state.as_dict()
        self.param_sections["initial_state"].set_values(state_dict)
        
        # Apply macro parameters
        macro_dict = config.macro_parameters.as_dict()
        self.param_sections["macro"].set_values(macro_dict)
        
        # Apply CBDC parameters
        cbdc_dict = config.cbdc_parameters.as_dict()
        self.param_sections["cbdc"].set_values(cbdc_dict)
        
        # Apply trade parameters
        trade_dict = config.trade_parameters.as_dict()
        self.param_sections["trade"].set_values(trade_dict)
        
        # Apply banking parameters
        banking_dict = config.banking_parameters.as_dict()
        self.param_sections["banking"].set_values(banking_dict)
    
    def get_config_from_ui(self):
        """Create a configuration object from the UI settings."""
        # Get values from UI
        sim_values = self.param_sections["simulation"].get_values()
        initial_state_values = self.param_sections["initial_state"].get_values()
        macro_values = self.param_sections["macro"].get_values()
        cbdc_values = self.param_sections["cbdc"].get_values()
        trade_values = self.param_sections["trade"].get_values()
        banking_values = self.param_sections["banking"].get_values()
        
        # Create configuration
        config = SimulationConfig(
            time_horizon=sim_values.get("time_horizon", 20),
            random_seed=sim_values.get("random_seed", 42)
        )
        
        # Set initial state
        state = EconomicState()
        for key, value in initial_state_values.items():
            if hasattr(state, key):
                setattr(state, key, value)
            else:
                state.additional_variables[key] = value
        config.initial_state = state
        
        # Set parameter objects
        macro_params = MacroParameters()
        for key, value in macro_values.items():
            if hasattr(macro_params, key):
                setattr(macro_params, key, value)
            else:
                macro_params.additional_parameters[key] = value
        config.macro_parameters = macro_params
        
        cbdc_params = CBDCParameters()
        for key, value in cbdc_values.items():
            if hasattr(cbdc_params, key):
                setattr(cbdc_params, key, value)
            else:
                cbdc_params.additional_parameters[key] = value
        config.cbdc_parameters = cbdc_params
        
        trade_params = TradeParameters()
        for key, value in trade_values.items():
            if hasattr(trade_params, key):
                setattr(trade_params, key, value)
            else:
                trade_params.additional_parameters[key] = value
        config.trade_parameters = trade_params
        
        banking_params = BankingParameters()
        for key, value in banking_values.items():
            if hasattr(banking_params, key):
                setattr(banking_params, key, value)
            else:
                banking_params.additional_parameters[key] = value
        config.banking_parameters = banking_params
        
        return config
    
    def on_scenario_selected(self, event):
        """Handle scenario selection."""
        scenario = self.scenario_var.get()
        
        if scenario == "Default":
            config = create_default_config()
        elif scenario == "CBDC Adoption":
            config = create_cbdc_adoption_scenario()
        elif scenario == "Trade War":
            config = create_trade_war_scenario()
        elif scenario == "Banking Crisis":
            config = create_banking_crisis_scenario()
        else:  # Custom - keep current settings
            return
        
        self.apply_config(config)
    
    def load_config(self):
        """Load configuration from a file."""
        filepath = filedialog.askopenfilename(
            title="Load Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            config = SimulationConfig.from_json(filepath)
            self.apply_config(config)
            messagebox.showinfo("Success", "Configuration loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_config(self):
        """Save configuration to a file."""
        filepath = filedialog.asksaveasfilename(
            title="Save Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            config = self.get_config_from_ui()
            config.to_json(filepath)
            messagebox.showinfo("Success", "Configuration saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def run_simulation(self):
        """Run the simulation with the current configuration."""
        if self.simulation_running:
            messagebox.showinfo("Simulation Running", "A simulation is already running.")
            return
        
        # Get configuration from UI
        config = self.get_config_from_ui()
        
        # Update UI
        self.run_button.config(text="Running...", state="disabled")
        self.simulation_running = True
        
        # Run simulation in a separate thread
        self.simulation_thread = threading.Thread(target=self._run_simulation_thread, args=(config,))
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
    
    def _run_simulation_thread(self, config):
        """Run the simulation in a separate thread."""
        try:
            # Initialize simulation
            self.simulation = CBDCSimulation(config)
            
            # Run simulation
            self.results = self.simulation.run()
            
            # Update UI on the main thread
            self.after(0, self._update_ui_after_simulation)
            
        except Exception as e:
            # Handle errors
            self.after(0, lambda: messagebox.showerror("Simulation Error", f"An error occurred: {e}"))
            self.after(0, self._reset_run_button)
    
    def _update_ui_after_simulation(self):
        """Update the UI after the simulation completes."""
        # Reset run button
        self._reset_run_button()
        
        # Update variable list
        self._update_variable_list()
        
        # Update dashboard
        self._update_dashboard()
        
        # Update details
        self._update_details()
        
        # Show success message
        messagebox.showinfo("Simulation Complete", "The simulation has completed successfully.")
    
    def _reset_run_button(self):
        """Reset the run button state."""
        self.run_button.config(text="Run Simulation", state="normal")
        self.simulation_running = False
    
    def _update_variable_list(self):
        """Update the list of available variables."""
        if self.results is None:
            return
        
        # Clear current list
        self.var_listbox.delete(0, tk.END)
        
        # Add all columns from results
        for col in self.results.columns:
            self.var_listbox.insert(tk.END, col)
    
    def _update_dashboard(self):
        """Update the dashboard with simulation results."""
        if self.results is None:
            return
        
        # Update key metrics
        self._update_metrics()
        
        # Update charts
        self._update_dashboard_charts()
    
    def _update_metrics(self):
        """Update the key metrics display."""
        if self.results is None or len(self.results) == 0:
            return
        
        # Get the latest values
        latest = self.results.iloc[-1]
        
        # Calculate GDP growth
        if len(self.results) > 1:
            gdp_growth = (latest["gdp"] / self.results.iloc[-2]["gdp"] - 1) * 100
        else:
            gdp_growth = 0.0
        
        # Update labels
        metrics = {
            "GDP Growth": f"{gdp_growth:.2f}%",
            "Inflation Rate": f"{latest.get('inflation_rate', 0.0):.2f}%",
            "Unemployment Rate": f"{latest.get('unemployment_rate', 0.0):.2f}%",
            "Interest Rate": f"{latest.get('interest_rate', 0.0):.2f}%",
            "CBDC Adoption": f"{latest.get('cbdc_supply', 0.0) / latest.get('money_supply', 1.0) * 100:.2f}%",
            "Financial Stability": f"{(1 - latest.get('financial_stress_index', 0.0)) * 100:.2f}%"
        }
        
        for metric, value in metrics.items():
            if metric in self.metrics_labels:
                self.metrics_labels[metric].config(text=value)
    
    def _update_dashboard_charts(self):
        """Update the dashboard charts with simulation results."""
        if self.results is None or len(self.results) < 2:
            return
        
        # Define chart configurations
        chart_configs = [
            {
                "title": "GDP and Potential GDP",
                "variables": ["gdp", "potential_gdp"],
                "labels": ["GDP", "Potential GDP"],
                "colors": ["blue", "red"],
                "ylabel": "Billions $"
            },
            {
                "title": "Inflation and Unemployment",
                "variables": ["inflation_rate", "unemployment_rate"],
                "labels": ["Inflation Rate", "Unemployment Rate"],
                "colors": ["red", "green"],
                "ylabel": "Percent (%)"
            },
            {
                "title": "Interest Rates",
                "variables": ["interest_rate", "policy_rate", "loan_interest_rate"],
                "labels": ["Market Rate", "Policy Rate", "Loan Rate"],
                "colors": ["blue", "red", "green"],
                "ylabel": "Percent (%)"
            },
            {
                "title": "CBDC and Banking",
                "variables": ["cbdc_supply", "bank_deposits", "money_supply"],
                "labels": ["CBDC Supply", "Bank Deposits", "Money Supply"],
                "colors": ["purple", "blue", "green"],
                "ylabel": "Billions $"
            }
        ]
        
        # Update each chart
        for i, config in enumerate(chart_configs):
            if i < len(self.dashboard_figures):
                fig = self.dashboard_figures[i]
                fig.clear()
                
                ax = fig.add_subplot(111)
                ax.set_title(config["title"])
                ax.set_xlabel("Time (quarters)")
                ax.set_ylabel(config["ylabel"])
                
                x = range(len(self.results))
                
                for j, var in enumerate(config["variables"]):
                    if var in self.results.columns:
                        ax.plot(x, self.results[var], 
                               label=config["labels"][j], 
                               color=config["colors"][j])
                
                ax.legend()
                ax.grid(True)
                
                # Redraw canvas
                self.dashboard_canvases[i].draw()
    
    def _update_details(self):
        """Update the details view with simulation information."""
        if self.simulation is None:
            return
        
        # Enable text widget for editing
        self.details_text.config(state="normal")
        
        # Clear current content
        self.details_text.delete(1.0, tk.END)
        
        # Add simulation details
        config = self.simulation.config
        
        details = [
            "CBDC Economic Simulation Results",
            "================================",
            "",
            f"Time Horizon: {config.time_horizon} quarters",
            f"Start Date: {config.start_date}",
            f"Random Seed: {config.random_seed}",
            "",
            "Key Parameters:",
            f"- Natural Unemployment Rate: {config.macro_parameters.natural_unemployment:.2f}%",
            f"- Potential Output Growth: {config.macro_parameters.potential_output_growth * 100:.2f}%",
            f"- CBDC Interest Rate: {config.cbdc_parameters.cbdc_interest_rate:.2f}%",
            f"- Programmable Money Validity: {config.cbdc_parameters.programmable_money_validity} days",
            f"- Tariff Rate: {config.trade_parameters.tariff_rate * 100:.2f}%",
            f"- Capital Requirement: {config.banking_parameters.capital_requirement * 100:.2f}%",
            "",
            "Simulation Results:",
            f"- Final GDP: {self.results.iloc[-1].get('gdp', 0.0):.2f} billion $",
            f"- Final Inflation Rate: {self.results.iloc[-1].get('inflation_rate', 0.0):.2f}%",
            f"- Final Unemployment Rate: {self.results.iloc[-1].get('unemployment_rate', 0.0):.2f}%",
            f"- Final Interest Rate: {self.results.iloc[-1].get('interest_rate', 0.0):.2f}%",
            f"- Final CBDC Supply: {self.results.iloc[-1].get('cbdc_supply', 0.0):.2f} billion $",
            f"- Final Bank Deposits: {self.results.iloc[-1].get('bank_deposits', 0.0):.2f} billion $",
            "",
            "CBDC Impact Analysis:",
            "- The simulation shows how CBDC and programmable monetary policy affect:",
            "  * Economic growth and stability",
            "  * Inflation and unemployment dynamics",
            "  * Banking sector and financial intermediation",
            "  * International trade and capital flows",
            "",
            "For detailed analysis, use the Results tab to plot specific variables."
        ]
        
        self.details_text.insert(tk.END, "\n".join(details))
        
        # Make text widget read-only again
        self.details_text.config(state="disabled")
    
    def plot_selected_variables(self):
        """Plot the selected variables from the results."""
        if self.results is None:
            messagebox.showinfo("No Data", "Run a simulation first to generate data.")
            return
        
        # Get selected variables
        selected_indices = self.var_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select at least one variable to plot.")
            return
        
        selected_vars = [self.var_listbox.get(i) for i in selected_indices]
        
        # Create plot
        self.results_figure.clear()
        ax = self.results_figure.add_subplot(111)
        
        x = range(len(self.results))
        
        for var in selected_vars:
            if var in self.results.columns:
                ax.plot(x, self.results[var], label=var)
        
        ax.set_title("Selected Variables")
        ax.set_xlabel("Time (quarters)")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True)
        
        # Redraw canvas
        self.results_canvas.draw()

def main():
    """Main function to run the application."""
    app = CBDCSimulationApp()
    app.mainloop()

if __name__ == "__main__":
    main()
