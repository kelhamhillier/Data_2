# Copyright (C) 2018 Garth N. Wells
#
# SPDX-License-Identifier: MIT
"""This module collects water level data from all monitoring stations over 28 days.

It provides functionality to collect data from either the live Environment Agency API
or a mock dataset stored locally. Configure the USE_LIVE_DATA variable to switch between modes.
"""

import datetime
import json
import os
import time
from pathlib import Path

from floodsystem.datafetcher import fetch_measure_levels
from floodsystem.stationdata import build_station_list, update_water_levels

# ============================================================================
# CONFIGURATION: Toggle between live API data and mock dataset
# ============================================================================
# Set to True to use live data from the Environment Agency API
# Set to False to use the mock dataset stored locally
USE_LIVE_DATA = False
# ============================================================================

# Storage paths
DATA_DIR = 'collected_data'
LIVE_DATA_FILE = os.path.join(DATA_DIR, 'live_data_28days.json')
MOCK_DATA_FILE = os.path.join(DATA_DIR, 'mock_data_28days.json')


def ensure_data_directory():
    """Create data directory if it doesn't exist."""
    Path(DATA_DIR).mkdir(parents=True, exist_ok=True)


def collect_live_data(duration_days=28):
    """
    Collect water level data from the live Environment Agency API for all stations
    over the specified duration.
    
    Args:
        duration_days (int): Number of days to collect data for (default: 28)
    
    Returns:
        dict: Collected data with structure:
              {
                  'timestamp': ISO format datetime,
                  'duration_days': int,
                  'stations': [
                      {
                          'station_id': str,
                          'measure_id': str,
                          'name': str,
                          'river': str,
                          'town': str,
                          'coord': (lat, long),
                          'typical_range': (low, high),
                          'readings': [
                              {'datetime': ISO format, 'value': float},
                              ...
                          ]
                      },
                      ...
                  ]
              }
    """
    print("=" * 70)
    print("COLLECTING LIVE DATA FROM ENVIRONMENT AGENCY API")
    print("=" * 70)
    
    ensure_data_directory()
    
    # Build list of all stations
    print("\nBuilding station list...")
    stations = build_station_list(use_cache=True)
    print(f"Found {len(stations)} stations\n")
    
    # Update with latest water levels
    print("Fetching latest water levels...")
    update_water_levels(stations)
    
    # Time range for data collection
    dt = datetime.timedelta(days=duration_days)
    
    # Collect data from each station
    collected_data = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'duration_days': duration_days,
        'data_source': 'live_api',
        'stations': []
    }
    
    total_stations = len(stations)
    for idx, station in enumerate(stations):
        try:
            print(f"[{idx+1}/{total_stations}] Fetching data for {station.name}...", end=' ')
            
            # Fetch historical data for the station
            dates, levels = fetch_measure_levels(station.measure_id, dt)
            
            station_data = {
                'station_id': station.station_id,
                'measure_id': station.measure_id,
                'name': station.name,
                'river': station.river,
                'town': station.town,
                'coord': station.coord,
                'typical_range': station.typical_range,
                'readings': [
                    {
                        'datetime': d.isoformat(),
                        'value': v
                    }
                    for d, v in zip(dates, levels)
                ]
            }
            collected_data['stations'].append(station_data)
            print(f"✓ ({len(dates)} readings)")
            
            # Add a small delay to avoid overwhelming the API
            time.sleep(0.5)
            
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Save collected data
    print(f"\nSaving {len(collected_data['stations'])} stations to {LIVE_DATA_FILE}...")
    with open(LIVE_DATA_FILE, 'w') as f:
        json.dump(collected_data, f, indent=2)
    
    print("✓ Data collection complete!")
    return collected_data


def generate_mock_data(num_stations=50, duration_days=28):
    """
    Generate mock water level data for testing and demonstration purposes.
    
    Args:
        num_stations (int): Number of mock stations to create (default: 50)
        duration_days (int): Number of days of mock data to generate (default: 28)
    
    Returns:
        dict: Mock data with same structure as live data
    """
    print("=" * 70)
    print("GENERATING MOCK DATA")
    print("=" * 70)
    
    ensure_data_directory()
    
    import random
    
    mock_data = {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'duration_days': duration_days,
        'data_source': 'mock',
        'stations': []
    }
    
    # Sample station names, rivers, and towns
    sample_names = [
        'Thames at Richmond', 'Severn at Shrewsbury', 'Trent at Nottingham',
        'Avon at Evesham', 'Ouse at Bedford', 'Dee at Llangollen',
        'Spey at Ballindalloch', 'Tweed at Peebles', 'Exe at Exeter',
        'Mersey at Stockport', 'Ribble at Samlesbury', 'Lune at Caton',
        'Wear at Sunderland', 'Tyne at Corbridge', 'Eden at Sheepmount',
        'Derwent at Derbyshire', 'Midlands Avon at Evesham', 'Great Ouse at Bedford',
        'Blyth at Wylam', 'Coquet at Rothbury'
    ]
    
    rivers = ['Thames', 'Severn', 'Trent', 'Avon', 'Ouse', 'Dee', 'Spey', 
              'Tweed', 'Exe', 'Mersey', 'Ribble', 'Lune', 'Wear', 'Tyne', 'Eden']
    
    towns = ['London', 'Birmingham', 'Manchester', 'Leeds', 'Liverpool', 
             'Bristol', 'York', 'Bath', 'Oxford', 'Cambridge']
    
    # Generate mock stations
    for i in range(num_stations):
        station_name = f"{random.choice(sample_names)} #{i+1}"
        river = random.choice(rivers)
        town = random.choice(towns)
        lat = random.uniform(50.0, 55.0)
        lon = random.uniform(-3.0, 2.0)
        typical_low = random.uniform(0.5, 1.5)
        typical_high = typical_low + random.uniform(1.0, 3.0)
        
        # Generate readings over 28 days (assuming readings every 15 minutes)
        readings = []
        current_time = datetime.datetime.utcnow() - datetime.timedelta(days=duration_days)
        base_level = random.uniform(1.0, 2.0)
        
        while current_time < datetime.datetime.utcnow():
            # Simulate water level with noise and trend
            noise = random.gauss(0, 0.1)
            trend = 0.001 * (datetime.datetime.utcnow() - current_time).total_seconds() / 86400
            level = base_level + noise + trend
            
            readings.append({
                'datetime': current_time.isoformat(),
                'value': round(level, 4)
            })
            
            # Increment by 15 minutes
            current_time += datetime.timedelta(minutes=15)
        
        station_data = {
            'station_id': f'station_{i+1:04d}',
            'measure_id': f'measure_{i+1:04d}',
            'name': station_name,
            'river': river,
            'town': town,
            'coord': [lat, lon],
            'typical_range': [typical_low, typical_high],
            'readings': readings
        }
        mock_data['stations'].append(station_data)
    
    # Save mock data
    print(f"Generating data for {num_stations} mock stations...")
    print(f"Saving to {MOCK_DATA_FILE}...")
    with open(MOCK_DATA_FILE, 'w') as f:
        json.dump(mock_data, f, indent=2)
    
    print("✓ Mock data generation complete!")
    return mock_data


def load_data(use_live_data=None):
    """
    Load collected data from file.
    
    Args:
        use_live_data (bool): If True, load live data. If False, load mock data.
                             If None, uses the global USE_LIVE_DATA setting.
    
    Returns:
        dict: Loaded data, or None if file not found
    """
    if use_live_data is None:
        use_live_data = USE_LIVE_DATA
    
    data_file = LIVE_DATA_FILE if use_live_data else MOCK_DATA_FILE
    
    if not os.path.exists(data_file):
        print(f"Data file not found: {data_file}")
        return None
    
    print(f"Loading data from {data_file}...")
    with open(data_file, 'r') as f:
        data = json.load(f)
    
    print(f"✓ Loaded data from {data['data_source']} (collected at {data['timestamp']})")
    print(f"  Stations: {len(data['stations'])}")
    return data


def get_data(use_live_data=None):
    """
    Get 28-day data, collecting fresh data or using mock if necessary.
    
    Args:
        use_live_data (bool): If True, use/collect live data. If False, use mock data.
                             If None, uses the global USE_LIVE_DATA setting.
    
    Returns:
        dict: 28-day water level data for all stations
    """
    if use_live_data is None:
        use_live_data = USE_LIVE_DATA
    
    if use_live_data:
        print(f"Mode: LIVE DATA (using Environment Agency API)")
        # Try to load existing live data first
        data = load_data(use_live_data=True)
        if data is None:
            print("No existing live data found. Collecting fresh data...")
            data = collect_live_data()
        return data
    else:
        print(f"Mode: MOCK DATA (using generated dataset)")
        # Try to load existing mock data first
        data = load_data(use_live_data=False)
        if data is None:
            print("No existing mock data found. Generating new mock data...")
            data = generate_mock_data()
        return data


def print_data_summary(data):
    """Print a summary of the collected data."""
    print("\n" + "=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)
    print(f"Data Source: {data['data_source']}")
    print(f"Collected: {data['timestamp']}")
    print(f"Duration: {data['duration_days']} days")
    print(f"Total Stations: {len(data['stations'])}")
    
    if data['stations']:
        total_readings = sum(len(s['readings']) for s in data['stations'])
        avg_readings = total_readings / len(data['stations'])
        print(f"Total Readings: {total_readings}")
        print(f"Average Readings per Station: {avg_readings:.0f}")
        
        print("\nSample Stations:")
        for station in data['stations'][:3]:
            print(f"  - {station['name']} ({station['river']})")
            print(f"    Readings: {len(station['readings'])}")
            if station['readings']:
                print(f"    Date Range: {station['readings'][0]['datetime']} to {station['readings'][-1]['datetime']}")


def run():
    """Main entry point for data collection."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  28-Day Water Level Data Collection Tool".center(68) + "║")
    print("║" + f"  Mode: {'LIVE DATA' if USE_LIVE_DATA else 'MOCK DATA'}".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Get data (live or mock based on configuration)
    data = get_data(use_live_data=USE_LIVE_DATA)
    
    # Print summary
    print_data_summary(data)
    
    print("\n" + "=" * 70)
    print("To change between live and mock data, edit the USE_LIVE_DATA")
    print("variable at the top of this file (currently set to {})".format(USE_LIVE_DATA))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run()
