"""
CBDC Economic Simulation - Enhanced Interface with Real-World Data Integration

This module provides an enhanced graphical user interface for the CBDC economic simulation system
with real-world data integration, calculation transparency, and natural language explanations.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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
import datetime

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
from data_integration import WorldBankDataFetcher, DataExplainer

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
    
    def __init__(self, parent, title, parameters, initial_values=None, data_explainer=None):
        """
        Initialize a parameter section.
        
        Args:
            parent: Parent widget
            title: Section title
            parameters: Dict of parameter names and their metadata
            initial_values: Dict of initial values for parameters
            data_explainer: Optional DataExplainer for parameter explanations
        """
        self.parent = parent
        self.title = title
        self.parameters = parameters
        self.initial_values = initial_values or {}
        self.controls = {}
        self.data_explainer = data_explainer
        
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
                
                # Add info button for parameter explanation
                if self.data_explainer:
                    info_button = ttk.Button(
                        param_frame, 
                        text="?", 
                        width=2,
                        command=lambda p=param_name: self._show_parameter_info(p)
                    )
                    info_button.pack(side="left", padx=2)
                
                self.controls[param_name] = {
                    "var": var,
                    "widget": scale,
                    "value_label": value_label,
                    "type": param_type,
                    "old_value": initial_value  # Track for explanation of changes
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
                
                # Add info button for parameter explanation
                if self.data_explainer:
                    info_button = ttk.Button(
                        param_frame, 
                        text="?", 
                        width=2,
                        command=lambda p=param_name: self._show_parameter_info(p)
                    )
                    info_button.pack(side="left", padx=2)
                
                self.controls[param_name] = {
                    "var": var,
                    "widget": combo,
                    "type": param_type,
                    "old_value": initial_value  # Track for explanation of changes
                }
                
            elif param_type == "boolean":
                # Create a checkbox for boolean parameters
                var = tk.BooleanVar(value=bool(initial_value))
                check = ttk.Checkbutton(
                    param_frame,
                    variable=var
                )
                check.pack(side="left", padx=5)
                
                # Add info button for parameter explanation
                if self.data_explainer:
                    info_button = ttk.Button(
                        param_frame, 
                        text="?", 
                        width=2,
                        command=lambda p=param_name: self._show_parameter_info(p)
                    )
                    info_button.pack(side="left", padx=2)
                
                self.controls[param_name] = {
                    "var": var,
                    "widget": check,
                    "type": param_type,
                    "old_value": initial_value  # Track for explanation of changes
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
    
    def _show_parameter_info(self, param_name):
        """Show detailed information about a parameter."""
        if not self.data_explainer:
            return
        
        # Get current and old values
        control = self.controls[param_name]
        current_value = self._get_param_value(param_name)
        old_value = control["old_value"]
        
        # Get parameter metadata
        param_meta = self.parameters.get(param_name, {})
        
        # Create explanation text
        if param_name.startswith("cbdc_"):
            explanation = self.data_explainer.explain_cbdc_parameter(param_name)
        else:
            explanation = param_meta.get("tooltip", f"Parameter: {param_name}")
        
        # Add explanation of change impact if values differ
        if abs(float(current_value) - float(old_value)) > 0.001:
            change_explanation = self.data_explainer.explain_parameter_change(
                param_name, old_value, current_value
            )
            explanation += "\n\n" + change_explanation
        
        # Show in dialog
        messagebox.showinfo(f"Parameter Information: {param_meta.get('label', param_name)}", explanation)
    
    def get_values(self):
        """Get the current values of all parameters in this section."""
        values = {}
        for param_name, control in self.controls.items():
            values[param_name] = self._get_param_value(param_name)
        
        return values
    
    def _get_param_value(self, param_name):
        """Get the current value of a specific parameter."""
        control = self.controls[param_name]
        var = control["var"]
        param_type = control["type"]
        
        if param_type == "float":
            return float(var.get())
        elif param_type == "int":
            return int(var.get())
        elif param_type == "choice":
            return var.get()
        elif param_type == "boolean":
            return bool(var.get())
    
    def set_values(self, values):
        """Set the values of parameters from a dictionary."""
        for param_name, value in values.items():
            if param_name in self.controls:
                control = self.controls[param_name]
                var = control["var"]
                
                # Store old value for change explanation
                control["old_value"] = self._get_param_value(param_name)
                
                try:
                    var.set(value)
                except Exception as e:
                    print(f"Error setting {param_name} to {value}: {e}")

class EnhancedCBDCSimulationApp(tk.Tk):
    """Enhanced application for the CBDC economic simulation with real-world data integration."""
    
    def __init__(self):
        super().__init__()
        
        # Configure the main window
        self.title("Enhanced CBDC Economic Simulation")
        self.geometry("1800x1000")
        self.minsize(1400, 900)
        
        # Initialize data integration components
        self.data_fetcher = WorldBankDataFetcher()
        self.data_explainer = DataExplainer(self.data_fetcher)
        
        # Initialize simulation state
        self.simulation = None
        self.simulation_thread = None
        self.simulation_running = False
        self.results = None
        self.calculation_logs = []
        self.selected_country = None
        self.country_data = None
        
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
        left_panel.pack(side="left", fill="y", padx=10, pady=10, expand=False)
        
        # Create right panel for visualization
        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Create scrollable frame for parameters
        self.param_scroll = ScrollableFrame(left_panel)
        self.param_scroll.pack(fill="both", expand=True, pady=10)
        
        # Create real-world data integration section
        self.create_data_integration_section()
        
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
        self.dashboard_tab = ttk.Frame(self.notebook)
        self.results_tab = ttk.Frame(self.notebook)
        self.details_tab = ttk.Frame(self.notebook)
        self.calculations_tab = ttk.Frame(self.notebook)
        self.explanations_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.dashboard_tab, text="Dashboard")
        self.notebook.add(self.results_tab, text="Results")
        self.notebook.add(self.details_tab, text="Details")
        self.notebook.add(self.calculations_tab, text="Calculations")
        self.notebook.add(self.explanations_tab, text="Explanations")
        
        # Create dashboard content
        self.create_dashboard()
        
        # Create results content
        self.create_results_view()
        
        # Create details content
        self.create_details_view()
        
        # Create calculations content
        self.create_calculations_view()
        
        # Create explanations content
        self.create_explanations_view()
        
        # Create parameter sections
        self.create_parameter_sections()
    
    def create_data_integration_section(self):
        """Create the real-world data integration section."""
        # Create a frame for the data integration controls
        data_frame = ttk.LabelFrame(self.param_scroll.scrollable_frame, text="Real-World Data Integration")
        data_frame.pack(fill="x", padx=10, pady=5)
        
        # Country selection
        country_frame = ttk.Frame(data_frame)
        country_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(country_frame, text="Country:").pack(side="left", padx=5)
        
        self.country_var = tk.StringVar()
        self.country_entry = ttk.Combobox(
            country_frame,
            textvariable=self.country_var,
            values=["United States", "United Kingdom", "Germany", "Japan", "China", "India", "Brazil"],
            width=20
        )
        self.country_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        search_button = ttk.Button(country_frame, text="Search", command=self.search_country)
        search_button.pack(side="left", padx=5)
        
        # Year selection
        year_frame = ttk.Frame(data_frame)
        year_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(year_frame, text="Data Year:").pack(side="left", padx=5)
        
        current_year = datetime.datetime.now().year
        years = list(range(current_year - 10, current_year))
        
        self.year_var = tk.StringVar(value=str(current_year - 1))
        year_combo = ttk.Combobox(
            year_frame,
            textvariable=self.year_var,
            values=[str(y) for y in years],
            width=10
        )
        year_combo.pack(side="left", padx=5)
        
        # Load data button
        load_data_button = ttk.Button(data_frame, text="Load Country Data", command=self.load_country_data)
        load_data_button.pack(fill="x", padx=5, pady=5)
        
        # Status label
        self.data_status_var = tk.StringVar(value="No country data loaded")
        status_label = ttk.Label(data_frame, textvariable=self.data_status_var, wraplength=250)
        status_label.pack(fill="x", padx=5, pady=5)
    
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
        
        # Add natural language summary
        summary_frame = ttk.LabelFrame(dashboard_frame, text="Simulation Summary")
        summary_frame.pack(fill="x", pady=10)
        
        self.summary_text = tk.Text(summary_frame, wrap="word", height=6)
        self.summary_text.pack(fill="x", padx=5, pady=5)
        self.summary_text.insert("1.0", "Run a simulation to see a summary of results.")
        self.summary_text.config(state="disabled")
    
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
        
        # Add projection controls
        projection_frame = ttk.Frame(results_frame)
        projection_frame.pack(fill="x", pady=5)
        
        ttk.Label(projection_frame, text="Projection Quarters:").pack(side="left", padx=5)
        
        self.projection_var = tk.IntVar(value=0)
        projection_spin = ttk.Spinbox(
            projection_frame,
            from_=0,
            to=20,
            textvariable=self.projection_var,
            width=5
        )
        projection_spin.pack(side="left", padx=5)
        
        ttk.Button(projection_frame, text="Project Future", command=self.project_future).pack(side="left", padx=5)
        
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
        self.details_text = scrolledtext.ScrolledText(details_frame, wrap="word", height=20)
        self.details_text.pack(fill="both", expand=True, pady=10)
        
        # Make the text widget read-only
        self.details_text.config(state="disabled")
    
    def create_calculations_view(self):
        """Create the calculations tab content."""
        # Create a frame for the calculations
        calc_frame = ttk.Frame(self.calculations_tab)
        calc_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create a text widget for displaying calculation details
        self.calc_text = scrolledtext.ScrolledText(calc_frame, wrap="word", height=20, font=("Courier", 10))
        self.calc_text.pack(fill="both", expand=True, pady=10)
        
        # Make the text widget read-only
        self.calc_text.config(state="disabled")
    
    def create_explanations_view(self):
        """Create the explanations tab content."""
        # Create a frame for the explanations
        explanations_frame = ttk.Frame(self.explanations_tab)
        explanations_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create controls for selecting what to explain
        controls_frame = ttk.Frame(explanations_frame)
        controls_frame.pack(fill="x", pady=5)
        
        ttk.Label(controls_frame, text="Explain:").pack(side="left", padx=5)
        
        self.explain_var = tk.StringVar(value="Variables")
        explain_combo = ttk.Combobox(
            controls_frame,
            textvariable=self.explain_var,
            values=["Variables", "Calculations", "Parameter Changes", "Policy Recommendations"],
            state="readonly",
            width=20
        )
        explain_combo.pack(side="left", padx=5)
        explain_combo.bind("<<ComboboxSelected>>", self.update_explanation_options)
        
        # Create frame for specific options
        self.options_frame = ttk.Frame(explanations_frame)
        self.options_frame.pack(fill="x", pady=5)
        
        # Create variable selection by default
        self.create_variable_selection()
        
        # Create a text widget for displaying explanations
        self.explanation_text = scrolledtext.ScrolledText(explanations_frame, wrap="word", height=20)
        self.explanation_text.pack(fill="both", expand=True, pady=10)
        
        # Make the text widget read-only
        self.explanation_text.config(state="disabled")
    
    def create_variable_selection(self):
        """Create controls for selecting variables to explain."""
        # Clear existing widgets
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Create variable selection
        ttk.Label(self.options_frame, text="Variable:").pack(side="left", padx=5)
        
        variables = [
            "gdp", "inflation_rate", "unemployment_rate", "interest_rate", 
            "exchange_rate", "cbdc_supply", "bank_deposits", "financial_stress_index"
        ]
        
        self.variable_var = tk.StringVar(value=variables[0])
        variable_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.variable_var,
            values=variables,
            width=20
        )
        variable_combo.pack(side="left", padx=5)
        
        explain_button = ttk.Button(self.options_frame, text="Explain", command=self.explain_selected)
        explain_button.pack(side="left", padx=5)
    
    def create_calculation_selection(self):
        """Create controls for selecting calculations to explain."""
        # Clear existing widgets
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Create calculation selection
        ttk.Label(self.options_frame, text="Calculation:").pack(side="left", padx=5)
        
        calculations = [
            "gdp_components", "inflation_phillips_curve", "interest_rate_policy", 
            "exchange_rate_determination", "cbdc_bank_disintermediation"
        ]
        
        self.calculation_var = tk.StringVar(value=calculations[0])
        calculation_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.calculation_var,
            values=calculations,
            width=20
        )
        calculation_combo.pack(side="left", padx=5)
        
        explain_button = ttk.Button(self.options_frame, text="Explain", command=self.explain_selected)
        explain_button.pack(side="left", padx=5)
    
    def create_parameter_selection(self):
        """Create controls for selecting parameter changes to explain."""
        # Clear existing widgets
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Create parameter selection
        ttk.Label(self.options_frame, text="Parameter:").pack(side="left", padx=5)
        
        parameters = [
            "cbdc_interest_rate", "programmable_money_validity", "conditional_spending_constraints",
            "automatic_fiscal_transfers", "smart_contract_based_lending", "foreign_exchange_controls",
            "tariff_rate", "capital_requirement"
        ]
        
        self.parameter_var = tk.StringVar(value=parameters[0])
        parameter_combo = ttk.Combobox(
            self.options_frame,
            textvariable=self.parameter_var,
            values=parameters,
            width=25
        )
        parameter_combo.pack(side="left", padx=5)
        
        explain_button = ttk.Button(self.options_frame, text="Explain", command=self.explain_selected)
        explain_button.pack(side="left", padx=5)
    
    def create_policy_recommendation_controls(self):
        """Create controls for generating policy recommendations."""
        # Clear existing widgets
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        
        # Create generate button
        generate_button = ttk.Button(
            self.options_frame, 
            text="Generate Policy Recommendations", 
            command=self.generate_policy_recommendations
        )
        generate_button.pack(side="left", padx=5)
    
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
            simulation_params,
            data_explainer=self.data_explainer
        )
        
        self.param_sections["initial_state"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Initial Economic State",
            initial_state_params,
            data_explainer=self.data_explainer
        )
        
        self.param_sections["macro"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Macroeconomic Parameters",
            macro_params,
            data_explainer=self.data_explainer
        )
        
        self.param_sections["cbdc"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "CBDC Parameters",
            cbdc_params,
            data_explainer=self.data_explainer
        )
        
        self.param_sections["trade"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "International Trade Parameters",
            trade_params,
            data_explainer=self.data_explainer
        )
        
        self.param_sections["banking"] = ParameterSection(
            self.param_scroll.scrollable_frame,
            "Banking Sector Parameters",
            banking_params,
            data_explainer=self.data_explainer
        )
    
    def search_country(self):
        """Search for a country and update the dropdown."""
        query = self.country_var.get()
        if not query:
            return
        
        try:
            # Search for countries
            countries = self.data_fetcher.search_countries(query)
            
            if not countries:
                messagebox.showinfo("Country Search", "No matching countries found.")
                return
            
            # Update dropdown values
            country_names = [country["name"] for country in countries]
            self.country_entry["values"] = country_names
            
            # If exact match, select it
            if query in country_names:
                self.country_var.set(query)
            else:
                # Otherwise select first match
                self.country_var.set(country_names[0])
            
        except Exception as e:
            messagebox.showerror("Error", f"Error searching for country: {e}")
    
    def load_country_data(self):
        """Load real-world data for the selected country."""
        country_name = self.country_var.get()
        if not country_name:
            messagebox.showinfo("Country Data", "Please select a country first.")
            return
        
        try:
            # Find country code
            countries = self.data_fetcher.search_countries(country_name)
            if not countries:
                messagebox.showinfo("Country Data", f"Could not find country code for {country_name}.")
                return
            
            # Use first matching country
            country_code = countries[0]["code"]
            self.selected_country = countries[0]
            
            # Get year if specified
            year = None
            if self.year_var.get():
                try:
                    year = int(self.year_var.get())
                except ValueError:
                    pass
            
            # Show loading message
            self.data_status_var.set(f"Loading data for {country_name}...")
            self.update_idletasks()
            
            # Get country data
            self.country_data = self.data_fetcher.get_country_data(country_code, year)
            
            # Convert to simulation state
            simulation_state = self.data_fetcher.convert_to_simulation_state(self.country_data)
            
            # Update initial state parameters
            self.param_sections["initial_state"].set_values(simulation_state)
            
            # Update status
            data_year = max([self.country_data.get(f"{ind}_year", 0) for ind in self.data_fetcher.common_indicators.keys()])
            self.data_status_var.set(f"Loaded data for {country_name} ({data_year})")
            
            # Show success message
            messagebox.showinfo("Country Data", f"Successfully loaded economic data for {country_name}.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error loading country data: {e}")
            self.data_status_var.set(f"Error loading data for {country_name}")
    
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
        
        # Clear calculation logs
        self.calculation_logs = []
        
        # Run simulation in a separate thread
        self.simulation_thread = threading.Thread(target=self._run_simulation_thread, args=(config,))
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
    
    def _run_simulation_thread(self, config):
        """Run the simulation in a separate thread."""
        try:
            # Initialize simulation with calculation logging
            self.simulation = EnhancedCBDCSimulation(config, self.calculation_logs)
            
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
        
        # Update calculations
        self._update_calculations()
        
        # Update explanations
        self._update_explanations()
        
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
        
        # Update natural language summary
        self._update_summary()
    
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
    
    def _update_summary(self):
        """Update the natural language summary of simulation results."""
        if self.results is None or len(self.results) == 0 or self.simulation is None:
            return
        
        # Get initial and final states
        initial_state = self.results.iloc[0].to_dict()
        final_state = self.results.iloc[-1].to_dict()
        time_horizon = self.simulation.config.time_horizon
        
        # Generate explanation
        explanation = self.data_explainer.explain_simulation_results(
            initial_state, final_state, time_horizon
        )
        
        # Update text widget
        self.summary_text.config(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", explanation)
        self.summary_text.config(state="disabled")
    
    def _update_details(self):
        """Update the details view with simulation information."""
        if self.simulation is None:
            return
        
        # Enable text widget for editing
        self.details_text.config(state="normal")
        
        # Clear current content
        self.details_text.delete("1.0", tk.END)
        
        # Add simulation details
        config = self.simulation.config
        
        details = [
            "# CBDC Economic Simulation Results",
            "",
            f"## Configuration",
            f"Time Horizon: {config.time_horizon} quarters",
            f"Start Date: {config.start_date}",
            f"Random Seed: {config.random_seed}",
            "",
            f"## Initial Economic State",
            f"GDP: ${config.initial_state.gdp:.2f} billion",
            f"Inflation Rate: {config.initial_state.inflation_rate:.2f}%",
            f"Unemployment Rate: {config.initial_state.unemployment_rate:.2f}%",
            f"Interest Rate: {config.initial_state.interest_rate:.2f}%",
            f"Exchange Rate: {config.initial_state.exchange_rate:.4f}",
            f"Government Spending: ${config.initial_state.government_spending:.2f} billion",
            f"Tax Revenue: ${config.initial_state.tax_revenue:.2f} billion",
            f"CBDC Supply: ${config.initial_state.cbdc_supply:.2f} billion",
            "",
            f"## Key Parameters",
            f"### Macroeconomic Parameters",
            f"Natural Unemployment Rate: {config.macro_parameters.natural_unemployment:.2f}%",
            f"Potential Output Growth: {config.macro_parameters.potential_output_growth * 100:.2f}%",
            f"Marginal Propensity to Consume: {config.macro_parameters.marginal_propensity_to_consume:.2f}",
            f"Investment Interest Sensitivity: {config.macro_parameters.investment_interest_sensitivity:.2f}",
            f"Phillips Curve Sensitivity: {config.macro_parameters.phillips_curve_sensitivity:.2f}",
            "",
            f"### CBDC Parameters",
            f"CBDC Interest Rate: {config.cbdc_parameters.cbdc_interest_rate:.2f}%",
            f"Programmable Money Validity: {config.cbdc_parameters.programmable_money_validity} days",
            f"Conditional Spending Constraints: {config.cbdc_parameters.conditional_spending_constraints:.2f}",
            f"Automatic Fiscal Transfers: ${config.cbdc_parameters.automatic_fiscal_transfers:.2f} billion",
            f"Smart Contract Based Lending: {config.cbdc_parameters.smart_contract_based_lending:.2f}",
            f"Foreign Exchange Controls: {config.cbdc_parameters.foreign_exchange_controls:.2f}",
            "",
            f"### International Trade Parameters",
            f"Tariff Rate: {config.trade_parameters.tariff_rate * 100:.2f}%",
            f"Exchange Rate Regime: {config.trade_parameters.exchange_rate_regime}",
            f"Capital Flow Controls: {config.trade_parameters.capital_flow_controls:.2f}",
            f"CBDC Trade Settlement: {config.trade_parameters.cbdc_trade_settlement:.2f}",
            "",
            f"### Banking Sector Parameters",
            f"Capital Requirement: {config.banking_parameters.capital_requirement * 100:.2f}%",
            f"Reserve Requirement: {config.banking_parameters.reserve_requirement * 100:.2f}%",
            f"CBDC Disintermediation Factor: {config.banking_parameters.cbdc_disintermediation_factor:.2f}",
            "",
            f"## Final Results",
            f"GDP: ${self.results.iloc[-1].get('gdp', 0.0):.2f} billion",
            f"Inflation Rate: {self.results.iloc[-1].get('inflation_rate', 0.0):.2f}%",
            f"Unemployment Rate: {self.results.iloc[-1].get('unemployment_rate', 0.0):.2f}%",
            f"Interest Rate: {self.results.iloc[-1].get('interest_rate', 0.0):.2f}%",
            f"Exchange Rate: {self.results.iloc[-1].get('exchange_rate', 1.0):.4f}",
            f"CBDC Supply: ${self.results.iloc[-1].get('cbdc_supply', 0.0):.2f} billion",
            f"Bank Deposits: ${self.results.iloc[-1].get('bank_deposits', 0.0):.2f} billion",
            f"Financial Stress Index: {self.results.iloc[-1].get('financial_stress_index', 0.0):.2f}",
            "",
            f"## Data Source",
        ]
        
        # Add country data source if available
        if self.selected_country:
            details.extend([
                f"Country: {self.selected_country['name']} ({self.selected_country['code']})",
                f"Data Source: World Bank Development Indicators",
                f"Data Year: {max([self.country_data.get(f'{ind}_year', 0) for ind in self.data_fetcher.common_indicators.keys()])}"
            ])
        else:
            details.append("Simulation initialized with default values")
        
        self.details_text.insert("1.0", "\n".join(details))
        
        # Make text widget read-only again
        self.details_text.config(state="disabled")
    
    def _update_calculations(self):
        """Update the calculations view with detailed calculation logs."""
        # Enable text widget for editing
        self.calc_text.config(state="normal")
        
        # Clear current content
        self.calc_text.delete("1.0", tk.END)
        
        # Add calculation logs
        if self.calculation_logs:
            for log in self.calculation_logs:
                self.calc_text.insert(tk.END, f"{log}\n\n")
        else:
            self.calc_text.insert(tk.END, "No calculation logs available. Run a simulation to see detailed calculations.")
        
        # Make text widget read-only again
        self.calc_text.config(state="disabled")
    
    def _update_explanations(self):
        """Update the explanations tab with available options."""
        # Update explanation options based on simulation results
        if self.results is not None:
            # Update variable selection
            if hasattr(self, 'variable_var'):
                variables = list(self.results.columns)
                if variables:
                    self.variable_var.set(variables[0])
                    if hasattr(self, 'variable_combo'):
                        self.variable_combo["values"] = variables
    
    def update_explanation_options(self, event):
        """Update explanation options based on selected explanation type."""
        explanation_type = self.explain_var.get()
        
        if explanation_type == "Variables":
            self.create_variable_selection()
        elif explanation_type == "Calculations":
            self.create_calculation_selection()
        elif explanation_type == "Parameter Changes":
            self.create_parameter_selection()
        elif explanation_type == "Policy Recommendations":
            self.create_policy_recommendation_controls()
    
    def explain_selected(self):
        """Generate and display explanation for the selected item."""
        explanation_type = self.explain_var.get()
        
        # Enable text widget for editing
        self.explanation_text.config(state="normal")
        
        # Clear current content
        self.explanation_text.delete("1.0", tk.END)
        
        if explanation_type == "Variables":
            variable = self.variable_var.get()
            explanation = self.data_explainer.explain_variable(variable)
            
            # Add current value if available
            if self.results is not None and variable in self.results.columns:
                latest_value = self.results[variable].iloc[-1]
                explanation += f"\n\nCurrent value: {latest_value:.4f}"
                
                # Add trend information
                if len(self.results) > 1:
                    first_value = self.results[variable].iloc[0]
                    change = latest_value - first_value
                    pct_change = (change / first_value) * 100 if first_value != 0 else float('inf')
                    
                    trend = "increased" if change > 0 else "decreased"
                    explanation += f"\n\nTrend: {trend} by {abs(change):.4f} ({abs(pct_change):.2f}%) over the simulation period."
            
        elif explanation_type == "Calculations":
            calculation = self.calculation_var.get()
            
            # Get variables for the calculation
            variables = {}
            if self.results is not None and len(self.results) > 0:
                latest = self.results.iloc[-1].to_dict()
                
                # Add specific variables needed for each calculation
                if calculation == "gdp_components":
                    variables = {
                        "consumption": latest.get("consumption", 0),
                        "investment": latest.get("investment", 0),
                        "government_spending": latest.get("government_spending", 0),
                        "net_exports": latest.get("net_exports", 0),
                        "gdp": latest.get("gdp", 0)
                    }
                elif calculation == "inflation_phillips_curve":
                    variables = {
                        "unemployment_rate": latest.get("unemployment_rate", 0),
                        "natural_unemployment": self.simulation.config.macro_parameters.natural_unemployment,
                        "inflation_expectations": latest.get("inflation_expectations", 0),
                        "phillips_curve_sensitivity": self.simulation.config.macro_parameters.phillips_curve_sensitivity,
                        "inflation_rate": latest.get("inflation_rate", 0)
                    }
                elif calculation == "interest_rate_policy":
                    variables = {
                        "inflation_rate": latest.get("inflation_rate", 0),
                        "inflation_target": 2.0,
                        "unemployment_rate": latest.get("unemployment_rate", 0),
                        "natural_unemployment": self.simulation.config.macro_parameters.natural_unemployment,
                        "neutral_interest_rate": 2.0,
                        "inflation_response": 1.5,
                        "unemployment_response": 0.5,
                        "policy_rate": latest.get("policy_rate", 0)
                    }
                elif calculation == "exchange_rate_determination":
                    variables = {
                        "interest_rate": latest.get("interest_rate", 0),
                        "foreign_interest_rate": 2.0,
                        "current_account": latest.get("current_account", 0),
                        "exchange_rate": latest.get("exchange_rate", 0)
                    }
                elif calculation == "cbdc_bank_disintermediation":
                    variables = {
                        "cbdc_interest_rate": self.simulation.config.cbdc_parameters.cbdc_interest_rate,
                        "deposit_interest_rate": latest.get("deposit_interest_rate", 0),
                        "cbdc_disintermediation_factor": self.simulation.config.banking_parameters.cbdc_disintermediation_factor,
                        "bank_deposits": latest.get("bank_deposits", 0),
                        "cbdc_supply": latest.get("cbdc_supply", 0)
                    }
            
            explanation = self.data_explainer.explain_calculation(calculation, variables)
            
        elif explanation_type == "Parameter Changes":
            parameter = self.parameter_var.get()
            
            # Get current and initial values
            current_value = 0
            initial_value = 0
            
            # Find the parameter in the appropriate section
            for section_name, section in self.param_sections.items():
                if parameter in section.controls:
                    control = section.controls[parameter]
                    current_value = section._get_param_value(parameter)
                    initial_value = control["old_value"]
                    break
            
            explanation = self.data_explainer.explain_parameter_change(parameter, initial_value, current_value)
        
        # Insert explanation
        self.explanation_text.insert("1.0", explanation)
        
        # Make text widget read-only again
        self.explanation_text.config(state="disabled")
    
    def generate_policy_recommendations(self):
        """Generate and display policy recommendations based on simulation results."""
        if self.results is None:
            messagebox.showinfo("Policy Recommendations", "Run a simulation first to generate policy recommendations.")
            return
        
        # Get CBDC parameters
        cbdc_params = {}
        if self.simulation:
            cbdc_params = self.simulation.config.cbdc_parameters.as_dict()
        
        # Generate recommendations
        recommendations = self.data_explainer.generate_policy_recommendations(self.results, cbdc_params)
        
        # Display recommendations
        self.explanation_text.config(state="normal")
        self.explanation_text.delete("1.0", tk.END)
        self.explanation_text.insert("1.0", recommendations)
        self.explanation_text.config(state="disabled")
    
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
    
    def project_future(self):
        """Project future values based on current simulation results."""
        if self.results is None:
            messagebox.showinfo("No Data", "Run a simulation first before projecting future values.")
            return
        
        # Get projection quarters
        projection_quarters = self.projection_var.get()
        if projection_quarters <= 0:
            messagebox.showinfo("Invalid Input", "Please enter a positive number of quarters to project.")
            return
        
        # Get selected variables
        selected_indices = self.var_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select at least one variable to project.")
            return
        
        selected_vars = [self.var_listbox.get(i) for i in selected_indices]
        
        try:
            # Create projection
            projected_results = self._create_projection(self.results, selected_vars, projection_quarters)
            
            # Plot original and projected data
            self.results_figure.clear()
            ax = self.results_figure.add_subplot(111)
            
            original_x = range(len(self.results))
            projected_x = range(len(self.results), len(self.results) + projection_quarters)
            
            for var in selected_vars:
                if var in self.results.columns:
                    # Plot original data
                    ax.plot(original_x, self.results[var], label=f"{var} (Actual)")
                    
                    # Plot projected data
                    if var in projected_results.columns:
                        ax.plot(projected_x, projected_results[var], 
                               label=f"{var} (Projected)", 
                               linestyle='--')
            
            # Add vertical line to separate actual from projected
            ax.axvline(x=len(self.results)-1, color='gray', linestyle='--')
            
            ax.set_title(f"Projection for Next {projection_quarters} Quarters")
            ax.set_xlabel("Time (quarters)")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid(True)
            
            # Redraw canvas
            self.results_canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Projection Error", f"An error occurred during projection: {e}")
    
    def _create_projection(self, results, variables, quarters):
        """
        Create a simple projection of future values.
        
        Args:
            results: DataFrame with simulation results
            variables: List of variables to project
            quarters: Number of quarters to project
            
        Returns:
            DataFrame with projected values
        """
        # Create empty DataFrame for projections
        projected = pd.DataFrame(index=range(quarters))
        
        # For each variable, create a projection
        for var in variables:
            if var not in results.columns:
                continue
            
            # Get historical data
            historical = results[var].values
            
            if len(historical) < 4:
                # Not enough data for trend analysis, use last value
                projected[var] = [historical[-1]] * quarters
            else:
                # Use simple trend extrapolation
                # Calculate average growth rate over last 4 quarters
                recent = historical[-4:]
                growth_rates = [(recent[i] / recent[i-1]) - 1 for i in range(1, len(recent))]
                avg_growth = np.mean(growth_rates) if growth_rates else 0
                
                # Project forward
                last_value = historical[-1]
                projected_values = []
                
                for i in range(quarters):
                    next_value = last_value * (1 + avg_growth)
                    projected_values.append(next_value)
                    last_value = next_value
                
                projected[var] = projected_values
        
        return projected


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


def main():
    """Main function to run the application."""
    app = EnhancedCBDCSimulationApp()
    app.mainloop()

if __name__ == "__main__":
    main()
