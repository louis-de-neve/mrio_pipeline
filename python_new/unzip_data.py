"""
Unzip data module for MRIO pipeline
"""

import os
import zipfile

from pathlib import Path

def unzip_data(path='.'):
    """
    Unzip FAOSTAT data files
    This function should be executed to unzip the data from FAOSTAT if not already done
    """
    
    # Look for zip files in the path directory
    zip_files = list(Path(path).glob('*.zip'))
    
    if not zip_files:
        print("No zip files found to extract")
        return
    
    for zip_file in zip_files:
        try:
            print(f"Extracting {zip_file}...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall('.')
            print(f"Successfully extracted {zip_file}")
        except Exception as e:
            print(f"Error extracting {zip_file}: {e}")
    
    print("Data extraction completed")