# DXF to Shapefile Converter (DXFtoSHP)

A robust Python tool designed to convert AutoCAD DXF drawing entities into geospatial ESRI Shapefiles (`.shp`), organized by layer and entity type, with comprehensive error handling, CRS reprojection support, and automated reporting.

---

## Features

- **Entity Extraction**: Supports `POINT`, `LINE`, `LWPOLYLINE`, `POLYLINE`, `ARC`, `TEXT`, `MTEXT`, `CIRCLE`, and `INSERT` (block references with attributes).
- **Layer-Based Organization**: Automatically classifies and exports entities into separate Shapefiles per layer and geometry type.
- **Robust Error Handling**: Element-level `try-except` blocks ensure that if a single entity or layer encounters an issue, the process catches the error, logs it, and continues exporting the remaining valid elements.
- **Detailed Terminal Output**: Real-time progress indicators showing layer names, successfully exported counts, and error summaries.
- **Automated Execution Reports**: Generates a timestamped `report.txt` file in the output folder containing summary statistics, input/output CRS details, and precise coordinates of any problematic elements.
- **Spatial Reprojection**: Optional CRS transformation (defaulting to EPSG:4326 if Enter is pressed).

---

## Project Structure

- `main.py`: Entry point script to run the conversion process.
- `dxf_to_shp.py`: Core `DXFtoSHP` class containing DXF parsing, classification, reprojection, and export logic.
- `clic.py`: Utility module for colored terminal output (`green`, `red`).
- `create_venv.bat`: Batch script to create the Python virtual environment.
- `install_requirements.bat`: Batch script to install project dependencies.
- `run.bat`: Batch script to activate the environment and execute `main.py`.
- `requirements.txt`: List of Python package dependencies.
- `IN/`: Input directory for source DXF files.
- `OUT/`: Output directory where timestamped export folders are created.

---

## Requirements (`requirements.txt`)

The project relies on geospatial and CAD processing libraries:
- `ezdxf` (CAD file parsing)
- `geopandas` & `shapely` (Geospatial data handling and shapefile generation)
- `pyproj` (Coordinate Reference System transformations)
- `pandas`, `pyogrio`, and other supporting libraries.

---

## Setup & Installation

1. Place your input DXF files inside the `IN/` folder.
2. Run `create_venv.bat` to set up your Python virtual environment (`venv`).
3. Run `install_requirements.bat` to install all dependencies from `requirements.txt`.

---

## How to Execute

You can run the tool easily using the provided batch script:

```cmd
run.bat
```

Alternatively, activate the virtual environment manually and run `main.py`:

```cmd
call .venv\Scripts\activate
python main.py
```

During execution, the program will prompt you for:
1. The DXF filename located in the `IN/` directory.
2. Whether you want to reproject to a specific Coordinate Reference System (CRS). If yes, enter the source CRS and target CRS (press **Enter** to use `4326` as the default output CRS).
