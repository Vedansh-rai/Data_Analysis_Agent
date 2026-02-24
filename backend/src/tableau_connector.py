"""
Tableau Connector - Connects analyzed data to Tableau Desktop
Cleans data and converts to Excel format for Tableau compatibility.
"""
import os
import subprocess
import shutil
import pandas as pd
import numpy as np
from typing import Dict, Optional


class TableauConnector:
    """
    Connects data analysis output to Tableau Desktop on Mac.
    Cleans data and converts to Excel format for best compatibility.
    """
    
    def __init__(self, export_dir: str = "output/tableau"):
        self.export_dir = export_dir
        os.makedirs(export_dir, exist_ok=True)
        
        # Common Tableau Desktop paths on Mac
        self.tableau_paths = [
            "/Applications/Tableau Desktop.app",
            "/Applications/Tableau Desktop 2024.1.app",
            "/Applications/Tableau Desktop 2023.4.app",
            "/Applications/Tableau Desktop 2023.3.app",
            "/Applications/Tableau.app",
        ]
    
    def find_tableau(self) -> Optional[str]:
        """Find Tableau Desktop installation on Mac."""
        for path in self.tableau_paths:
            if os.path.exists(path):
                return path
        
        # Try to find any Tableau app
        apps_dir = "/Applications"
        if os.path.exists(apps_dir):
            for app in os.listdir(apps_dir):
                if "Tableau" in app and app.endswith(".app"):
                    return os.path.join(apps_dir, app)
        
        return None
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean the dataframe for Tableau:
        - Remove duplicate rows
        - Handle missing values
        - Clean column names (remove special chars)
        - Convert data types appropriately
        """
        print("🧹 Cleaning data for Tableau...")
        
        # Make a copy
        cleaned = df.copy()
        
        # 1. Remove duplicates
        initial_rows = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        removed_dupes = initial_rows - len(cleaned)
        if removed_dupes > 0:
            print(f"   Removed {removed_dupes} duplicate rows")
        
        # 2. Clean column names (Tableau prefers simple names)
        cleaned.columns = [
            col.strip()
               .replace(' ', '_')
               .replace('-', '_')
               .replace('.', '_')
               .replace('(', '')
               .replace(')', '')
            for col in cleaned.columns
        ]
        
        # 3. Handle missing values
        for col in cleaned.columns:
            if cleaned[col].isna().sum() > 0:
                if pd.api.types.is_numeric_dtype(cleaned[col]):
                    # Fill numeric with median
                    cleaned[col] = cleaned[col].fillna(cleaned[col].median())
                else:
                    # Fill categorical with 'Unknown'
                    cleaned[col] = cleaned[col].fillna('Unknown')
        
        # 4. Try to convert date-like columns
        for col in cleaned.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    cleaned[col] = pd.to_datetime(cleaned[col], errors='coerce')
                except:
                    pass
        
        print(f"   Cleaned: {len(cleaned)} rows, {len(cleaned.columns)} columns")
        return cleaned
    
    def convert_to_excel(self, source_path: str, filename: str) -> str:
        """
        Load CSV, clean it, and save as Excel for Tableau.
        Returns path to the Excel file.
        """
        print(f"📊 Converting {filename} to Excel for Tableau...")
        
        # Load the data
        if source_path.endswith('.csv'):
            df = pd.read_csv(source_path)
        elif source_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(source_path)
        else:
            df = pd.read_csv(source_path)  # Try CSV as default
        
        # Clean the data
        cleaned_df = self.clean_data(df)
        
        # Generate Excel filename
        base_name = filename.replace('.csv', '').replace('.xlsx', '').replace('.xls', '')
        excel_name = f"{base_name}_cleaned.xlsx"
        excel_path = os.path.join(self.export_dir, excel_name)
        
        # Save as Excel
        cleaned_df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"✅ Saved cleaned Excel: {excel_path}")
        
        return os.path.abspath(excel_path)
    
    def open_in_tableau(self, file_path: str) -> Dict[str, any]:
        """Open a data file directly in Tableau Desktop."""
        tableau_app = self.find_tableau()
        
        if not tableau_app:
            return {
                "success": False,
                "error": "Tableau Desktop not found. Please ensure it's installed in /Applications/"
            }
        
        try:
            abs_path = os.path.abspath(file_path)
            
            subprocess.Popen([
                "open",
                "-a", tableau_app,
                abs_path
            ])
            
            return {
                "success": True,
                "message": f"Opened {os.path.basename(file_path)} in Tableau Desktop",
                "tableau_path": tableau_app,
                "file_path": abs_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to launch Tableau: {str(e)}"
            }
    
    def export_and_open(self, source_path: str, filename: str) -> Dict[str, any]:
        """
        Clean data, convert to Excel, and open in Tableau Desktop.
        """
        # Convert to cleaned Excel
        excel_path = self.convert_to_excel(source_path, filename)
        
        # Open the cleaned Excel in Tableau
        result = self.open_in_tableau(excel_path)
        result["excel_path"] = excel_path
        result["message"] = f"Opened cleaned data in Tableau. Data cleaned: duplicates removed, missing values filled, column names standardized."
        
        return result
    
    def check_tableau_installed(self) -> Dict[str, any]:
        """Check if Tableau is installed and return info."""
        tableau_app = self.find_tableau()
        
        if tableau_app:
            return {
                "installed": True,
                "path": tableau_app,
                "name": os.path.basename(tableau_app).replace(".app", "")
            }
        else:
            return {
                "installed": False,
                "message": "Tableau Desktop not found in /Applications/"
            }
