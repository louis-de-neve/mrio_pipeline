# MRIO Agricultural Trade Analysis Pipeline - Python Version

This is a Python conversion of the R-based Multi-Regional Input-Output (MRIO) pipeline for analyzing agricultural trade and its impact on cropland use and species habitats.

## Original Publication

This code is part of the following publication:
**Schwarzmueller, F. & Kastner, T (2022), Agricultural trade and its impact on cropland use and the global loss of species' habitats. Sustainability Science, doi: 10.1007/s11625-022-01138-7**

Please cite appropriately when using this code.

## Files Overview

### Main Execution
- `execute.py` - Main execution script (equivalent to `_Execute.R`)

### Core Modules
- `calculating_trade_matrix.py` - Calculates apparent consumption and trade links (equivalent to `Calculating_Trade_Matrix.R`)
- `animal_products_to_feed.py` - Converts animal products into embedded feed items (equivalent to `animal_products_to_feed.R`)
- `calculate_area.py` - Converts traded tons into areas (equivalent to `calculate_area.R`)
- `unzip_data.py` - Utility for unzipping FAOSTAT data (equivalent to `Unzip data.R`)

### Configuration
- `requirements.txt` - Python package dependencies
- `README.md` - This documentation file

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup
1. Clone or download this repository
2. Navigate to the python directory
3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Start
1. Place your FAOSTAT data files in the working directory
2. Run the main script:
   ```bash
   python execute.py
   ```
3. Select your working directory when prompted
4. The pipeline will process all years from 1986-2013

### Configuration Options

You can modify the following options in `execute.py`:

#### Years to Process
```python
for_years = list(range(1986, 2014))  # Default: 1986-2013
```

#### Conversion Method
Choose from the following nutritional conversion methods:
- `"dry_matter"` (default)
- `"Energy"`
- `"Protein"`
- `"Fiber_TD"`
- `"Zinc"`
- `"Iron"`
- `"Calcium"`
- `"Folate_Tot"`
- `"Riboflavin"`
- `"Choline_Tot"`
- `"Potassium"`
- `"Vit_E"`
- `"Vit_B12"`
- `"Vit_K"`
- `"Vit_A"`

```python
conversion_opt = "dry_matter"
```

#### Import/Export Preference
Choose whether to prefer import or export data:
```python
prefer_import = "import"  # or "export"
```

### Manual Execution

You can also run individual modules:

```python
from calculating_trade_matrix import CalculatingTradeMatrix
from animal_products_to_feed import AnimalProductsToFeed
from calculate_area import CalculateArea

# Calculate trade matrix for 2013
trade_calc = CalculatingTradeMatrix(
    directory="/path/to/data",
    conversion_opt="dry_matter",
    included_years=2013,
    prefer_import="import"
)
trade_calc.run()

# Convert animal products to feed
feed_calc = AnimalProductsToFeed(
    directory="/path/to/data",
    conversion_opt="dry_matter", 
    included_years=2013,
    prefer_import="import"
)
feed_calc.run()

# Calculate areas
area_calc = CalculateArea(
    directory="/path/to/data",
    conversion_opt="dry_matter",
    included_years=2013,
    prefer_import="import"
)
area_calc.run()
```

## Required Data Files

The pipeline expects the following FAOSTAT data files in the working directory:

### Trade Data
- `Trade_DetailedTradeMatrix_E_All_Data_(Normalized).csv`

### Production Data
- `Production_Crops_E_All_Data_(Normalized).csv`
- `Production_LivestockPrimary_E_All_Data_(Normalized).csv`
- `CommodityBalances_LivestockFish_E_All_Data_(Normalized).csv`
- `CommodityBalances_Crops_E_All_Data_(Normalized).csv`

### Mapping and Conversion Files
- `primary_item_map_feed.csv`
- `CB_to_primary_items_map.csv`
- `CB_items_split.csv`
- `CB_code_FAO_code_for_conversion_factors.csv`
- `content_factors_per_100g.xlsx`
- `weighing_factors.csv`
- `Reporting_Dates.xls`

## Output Files

For each processed year, the pipeline generates:

### Trade Matrix Files
- `TradeMatrix_{import/export}_{conversion}_{year}.csv` - Main trade links for apparent consumption
- `logfile_TradeMatrix_{import/export}_{conversion}_{year}.txt` - Processing log

### Feed Matrix Files  
- `TradeMatrixFeed_{import/export}_{conversion}_{year}.csv` - Trade links with embedded feed
- `logfile_TradeMatrixFeed_{import/export}_{conversion}_{year}.txt` - Processing log
- `TradeMatrixFeed_{import/export}_{conversion}_{year}_nofeeddata.csv` - Countries without feed data
- `TradeMatrixFeed_{import/export}_{conversion}_{year}_noimportdata.csv` - Import data errors

### Area Files
- `TradeMatrixFeed_{import/export}_{conversion}_{year}_Area.csv` - Trade values converted to areas

## Performance Notes

- Processing time: ~40 minutes for all years (1986-2013) on a machine with 16GB RAM
- Memory usage is significant for large datasets
- Consider processing years individually for memory-constrained systems

## Error Handling

The pipeline includes comprehensive error handling and logging:
- Missing data is logged and handled gracefully
- Matrix singularity issues are resolved using pseudo-inverse
- All processing steps are logged to individual log files

## Differences from R Version

### Improvements
- Object-oriented design for better code organization
- Enhanced error handling and logging
- More memory-efficient processing
- Better documentation and type hints

### Dependencies
- Uses pandas instead of data.table for data manipulation
- Uses networkx instead of igraph for network analysis
- Uses scipy for linear algebra operations

## Troubleshooting

### Common Issues

1. **Missing data files**: Ensure all required FAOSTAT files are in the working directory
2. **Memory errors**: Try processing fewer years at once or increase system memory
3. **Import errors**: Make sure all required packages are installed via `pip install -r requirements.txt`

### Getting Help

- Check log files for detailed error messages
- Ensure input data files match expected format and naming
- Verify Python version compatibility (3.8+)

## License

Please refer to the original publication for licensing terms and cite appropriately when using this code.