"""
Tableau Dashboard Generator
Automatically creates a Tableau Workbook (.twb) with visualizations based on data analysis.
"""
import os
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, List, Any, Optional
from datetime import datetime


class TableauDashboardGenerator:
    """
    Generates Tableau Workbook files (.twb) with automated visualizations
    based on data analysis.
    """
    
    def __init__(self, output_dir: str = "output/tableau"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def analyze_columns(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Categorize columns by type for visualization decisions."""
        analysis = {
            "numeric": [],
            "categorical": [],
            "datetime": [],
            "text": []
        }
        
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                analysis["datetime"].append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                analysis["numeric"].append(col)
            elif df[col].nunique() < 20:  # Low cardinality = categorical
                analysis["categorical"].append(col)
            else:
                analysis["text"].append(col)
        
        return analysis
    
    def generate_twb(self, excel_path: str, df: pd.DataFrame, filename: str) -> str:
        """
        Generate a Tableau Workbook (.twb) with automated visualizations.
        """
        print("📊 Generating Tableau Dashboard...")
        
        # Analyze columns
        col_analysis = self.analyze_columns(df)
        
        # Create TWB XML structure
        workbook = ET.Element('workbook')
        workbook.set('version', '18.1')
        workbook.set('xmlns:user', 'http://www.tableausoftware.com/xml/user')
        
        # Add datasource
        datasources = ET.SubElement(workbook, 'datasources')
        self._add_datasource(datasources, excel_path, df)
        
        # Add worksheets
        worksheets = ET.SubElement(workbook, 'worksheets')
        sheet_names = []
        
        # Create visualizations based on data types
        if col_analysis["categorical"] and col_analysis["numeric"]:
            sheet_name = self._add_bar_chart(
                worksheets, 
                col_analysis["categorical"][0], 
                col_analysis["numeric"][0],
                df
            )
            sheet_names.append(sheet_name)
        
        if col_analysis["datetime"] and col_analysis["numeric"]:
            sheet_name = self._add_line_chart(
                worksheets,
                col_analysis["datetime"][0],
                col_analysis["numeric"][0],
                df
            )
            sheet_names.append(sheet_name)
        
        if len(col_analysis["numeric"]) >= 2:
            sheet_name = self._add_scatter_plot(
                worksheets,
                col_analysis["numeric"][0],
                col_analysis["numeric"][1],
                df
            )
            sheet_names.append(sheet_name)
        
        # Add summary table
        sheet_name = self._add_summary_table(worksheets, df)
        sheet_names.append(sheet_name)
        
        # Add dashboard combining all sheets
        dashboards = ET.SubElement(workbook, 'dashboards')
        self._add_dashboard(dashboards, sheet_names)
        
        # Write to file
        twb_name = filename.replace('.csv', '').replace('.xlsx', '') + '_dashboard.twb'
        twb_path = os.path.join(self.output_dir, twb_name)
        
        # Pretty print XML
        xml_str = ET.tostring(workbook, encoding='unicode')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        with open(twb_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        print(f"✅ Dashboard saved: {twb_path}")
        return os.path.abspath(twb_path)
    
    def _add_datasource(self, parent: ET.Element, excel_path: str, df: pd.DataFrame):
        """Add data source definition."""
        datasource = ET.SubElement(parent, 'datasource')
        datasource.set('caption', 'Analyzed Data')
        datasource.set('inline', 'true')
        datasource.set('name', 'excel-direct.0')
        datasource.set('version', '18.1')
        
        # Connection
        connection = ET.SubElement(datasource, 'connection')
        connection.set('class', 'excel-direct')
        connection.set('cleaning', 'no')
        connection.set('compat', 'no')
        connection.set('dataRefreshTime', '')
        connection.set('filename', excel_path)
        connection.set('interpretationMode', '0')
        connection.set('password', '')
        connection.set('server', '')
        connection.set('validate', 'no')
        
        # Add column metadata
        metadata = ET.SubElement(datasource, 'column-instance-metadata')
        
        for col in df.columns:
            column = ET.SubElement(datasource, 'column')
            column.set('caption', col)
            column.set('datatype', self._get_tableau_type(df[col].dtype))
            column.set('name', f'[{col}]')
            
            if pd.api.types.is_numeric_dtype(df[col]):
                column.set('role', 'measure')
                column.set('type', 'quantitative')
            else:
                column.set('role', 'dimension')
                column.set('type', 'nominal')
    
    def _get_tableau_type(self, dtype) -> str:
        """Convert pandas dtype to Tableau type."""
        dtype_str = str(dtype)
        if 'int' in dtype_str:
            return 'integer'
        elif 'float' in dtype_str:
            return 'real'
        elif 'datetime' in dtype_str:
            return 'datetime'
        elif 'bool' in dtype_str:
            return 'boolean'
        else:
            return 'string'
    
    def _add_bar_chart(self, parent: ET.Element, cat_col: str, num_col: str, df: pd.DataFrame) -> str:
        """Create a bar chart worksheet."""
        sheet_name = f"Bar: {num_col} by {cat_col}"[:31]  # Tableau limit
        
        worksheet = ET.SubElement(parent, 'worksheet')
        worksheet.set('name', sheet_name)
        
        table = ET.SubElement(worksheet, 'table')
        
        # Rows (category)
        rows = ET.SubElement(table, 'rows')
        rows.text = f'[excel-direct.0].[{cat_col}]'
        
        # Cols (measure)
        cols = ET.SubElement(table, 'cols')
        cols.text = f'SUM([excel-direct.0].[{num_col}])'
        
        # Mark type
        panes = ET.SubElement(table, 'panes')
        pane = ET.SubElement(panes, 'pane')
        mark = ET.SubElement(pane, 'mark')
        mark.set('class', 'Bar')
        
        return sheet_name
    
    def _add_line_chart(self, parent: ET.Element, date_col: str, num_col: str, df: pd.DataFrame) -> str:
        """Create a line chart worksheet."""
        sheet_name = f"Trend: {num_col}"[:31]
        
        worksheet = ET.SubElement(parent, 'worksheet')
        worksheet.set('name', sheet_name)
        
        table = ET.SubElement(worksheet, 'table')
        
        # Cols (date)
        cols = ET.SubElement(table, 'cols')
        cols.text = f'[excel-direct.0].[{date_col}]'
        
        # Rows (measure)
        rows = ET.SubElement(table, 'rows')
        rows.text = f'SUM([excel-direct.0].[{num_col}])'
        
        # Mark type
        panes = ET.SubElement(table, 'panes')
        pane = ET.SubElement(panes, 'pane')
        mark = ET.SubElement(pane, 'mark')
        mark.set('class', 'Line')
        
        return sheet_name
    
    def _add_scatter_plot(self, parent: ET.Element, x_col: str, y_col: str, df: pd.DataFrame) -> str:
        """Create a scatter plot worksheet."""
        sheet_name = f"Scatter: {x_col} vs {y_col}"[:31]
        
        worksheet = ET.SubElement(parent, 'worksheet')
        worksheet.set('name', sheet_name)
        
        table = ET.SubElement(worksheet, 'table')
        
        # Cols (X)
        cols = ET.SubElement(table, 'cols')
        cols.text = f'SUM([excel-direct.0].[{x_col}])'
        
        # Rows (Y)
        rows = ET.SubElement(table, 'rows')
        rows.text = f'SUM([excel-direct.0].[{y_col}])'
        
        # Mark type
        panes = ET.SubElement(table, 'panes')
        pane = ET.SubElement(panes, 'pane')
        mark = ET.SubElement(pane, 'mark')
        mark.set('class', 'Circle')
        
        return sheet_name
    
    def _add_summary_table(self, parent: ET.Element, df: pd.DataFrame) -> str:
        """Create a summary table worksheet."""
        sheet_name = "Data Summary"
        
        worksheet = ET.SubElement(parent, 'worksheet')
        worksheet.set('name', sheet_name)
        
        table = ET.SubElement(worksheet, 'table')
        
        # Add all columns
        cols = ET.SubElement(table, 'cols')
        col_refs = ' '.join([f'[excel-direct.0].[{col}]' for col in df.columns[:5]])
        cols.text = col_refs
        
        # Mark type
        panes = ET.SubElement(table, 'panes')
        pane = ET.SubElement(panes, 'pane')
        mark = ET.SubElement(pane, 'mark')
        mark.set('class', 'Text')
        
        return sheet_name
    
    def _add_dashboard(self, parent: ET.Element, sheet_names: List[str]):
        """Create a dashboard combining all worksheets."""
        dashboard = ET.SubElement(parent, 'dashboard')
        dashboard.set('name', 'Auto-Generated Dashboard')
        
        # Size
        size = ET.SubElement(dashboard, 'size')
        size.set('maxheight', '800')
        size.set('maxwidth', '1200')
        size.set('minheight', '600')
        size.set('minwidth', '1000')
        
        # Layout zones
        zones = ET.SubElement(dashboard, 'zones')
        
        # Add each sheet as a zone
        y_pos = 0
        zone_height = 800 // max(len(sheet_names), 1)
        
        for i, sheet_name in enumerate(sheet_names):
            zone = ET.SubElement(zones, 'zone')
            zone.set('h', str(zone_height))
            zone.set('id', str(i + 1))
            zone.set('name', sheet_name)
            zone.set('w', '1200')
            zone.set('x', '0')
            zone.set('y', str(y_pos))
            zone.set('type', 'sheet')
            y_pos += zone_height
        
        return dashboard
