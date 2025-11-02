#!/usr/bin/env python3
"""
Traffic Generator for Electronic City SUMO Network
Generates random trips and creates a complete simulation configuration
"""

import subprocess
import os
import sys

# Configuration
NETWORK_FILE = "electronic_city.net.xml"
ROUTE_FILE = "electronic_city.rou.xml"
TRIPS_FILE = "electronic_city.trips.xml"
CONFIG_FILE = "electronic_city.sumocfg"
ADDITIONAL_FILE = "electronic_city.add.xml"

# Traffic generation parameters
TRAFFIC_CONFIG = {
    'begin': 0,           # Simulation start time (seconds)
    'end': 7200,          # Simulation end time (1 hour = 3600 seconds)
    'period': 1,          # Average time between vehicle insertions (seconds)
    'trip_attributes': 'departLane="best" departSpeed="max"',
    'vehicle_class': 'passenger',
    'fringe_factor': 10,  # Prefer starting/ending at network edges
}

def check_files():
    """Check if required files exist"""
    if not os.path.exists(NETWORK_FILE):
        print(f"✗ ERROR: {NETWORK_FILE} not found!")
        print("Please run sumo_network.py first to generate the network.")
        return False
    print(f"✓ Found {NETWORK_FILE}")
    return True

def generate_random_trips():
    """Generate random trips using randomTrips.py"""
    print("\n" + "=" * 70)
    print("STEP 1: Generating Random Trips")
    print("=" * 70)
    
    try:
        # Find randomTrips.py in SUMO tools
        sumo_home = os.environ.get('SUMO_HOME', '/usr/local/share/sumo')
        randomtrips_script = os.path.join(sumo_home, 'tools', 'randomTrips.py')
        
        if not os.path.exists(randomtrips_script):
            print(f"✗ ERROR: randomTrips.py not found at {randomtrips_script}")
            print("Make sure SUMO_HOME is set correctly.")
            return False
        
        cmd = [
            'python3', randomtrips_script,
            '-n', NETWORK_FILE,
            '-o', TRIPS_FILE,
            '-b', str(TRAFFIC_CONFIG['begin']),
            '-e', str(TRAFFIC_CONFIG['end']),
            '-p', str(TRAFFIC_CONFIG['period']),
            '--fringe-factor', str(TRAFFIC_CONFIG['fringe_factor']),
            '--trip-attributes', TRAFFIC_CONFIG['trip_attributes'],
            '--vehicle-class', TRAFFIC_CONFIG['vehicle_class'],
            '--validate'
        ]
        
        print(f"\nGenerating trips...")
        print(f"  - Time period: {TRAFFIC_CONFIG['begin']}s to {TRAFFIC_CONFIG['end']}s")
        print(f"  - Vehicle insertion period: {TRAFFIC_CONFIG['period']}s")
        print(f"  - Estimated vehicles: ~{int(TRAFFIC_CONFIG['end'] / TRAFFIC_CONFIG['period'])}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(TRIPS_FILE):
            file_size = os.path.getsize(TRIPS_FILE) / 1024
            print(f"✓ Trips file generated: {TRIPS_FILE} ({file_size:.2f} KB)")
            return True
        else:
            print(f"✗ Failed to generate trips")
            if result.stderr:
                print(f"Error: {result.stderr[:300]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Trip generation timed out")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def generate_routes():
    """Convert trips to routes using duarouter"""
    print("\n" + "=" * 70)
    print("STEP 2: Converting Trips to Routes")
    print("=" * 70)
    
    try:
        cmd = [
            'duarouter',
            '-n', NETWORK_FILE,
            '-t', TRIPS_FILE,
            '-o', ROUTE_FILE,
            '--ignore-errors',
            '--no-warnings',
            '--begin', str(TRAFFIC_CONFIG['begin']),
            '--end', str(TRAFFIC_CONFIG['end'])
        ]
        
        print("\nComputing routes...")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(ROUTE_FILE):
            file_size = os.path.getsize(ROUTE_FILE) / 1024
            print(f"✓ Route file generated: {ROUTE_FILE} ({file_size:.2f} KB)")
            return True
        else:
            print(f"✗ Failed to generate routes")
            if result.stderr:
                print(f"Error: {result.stderr[:300]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Route generation timed out")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def create_additional_file():
    """Create additional file with traffic lights and detectors"""
    print("\n" + "=" * 70)
    print("STEP 3: Creating Additional Files")
    print("=" * 70)
    
    try:
        # Create a basic additional file with detectors
        content = """<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!-- Add detectors, traffic lights, or other additional elements here -->
</additional>
"""
        
        with open(ADDITIONAL_FILE, 'w') as f:
            f.write(content)
        
        print(f"✓ Additional file created: {ADDITIONAL_FILE}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating additional file: {e}")
        return False

def create_config_file():
    """Create SUMO configuration file"""
    print("\n" + "=" * 70)
    print("STEP 4: Creating Simulation Configuration")
    print("=" * 70)
    
    try:
        config_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    
    <input>
        <net-file value="{NETWORK_FILE}"/>
        <route-files value="{ROUTE_FILE}"/>
        <additional-files value="{ADDITIONAL_FILE}"/>
    </input>
    
    <time>
        <begin value="{TRAFFIC_CONFIG['begin']}"/>
        <end value="{TRAFFIC_CONFIG['end']}"/>
        <step-length value="1"/>
    </time>
    
    <processing>
        <time-to-teleport value="300"/>
        <max-depart-delay value="900"/>
        <default.speeddev value="0.1"/>
    </processing>
    
    <routing>
        <device.rerouting.adaptation-steps value="18"/>
        <device.rerouting.adaptation-interval value="10"/>
    </routing>
    
    <report>
        <verbose value="true"/>
        <no-step-log value="true"/>
    </report>
    
    <gui_only>
        <gui-settings-file value=""/>
    </gui_only>
    
</configuration>
"""
        
        with open(CONFIG_FILE, 'w') as f:
            f.write(config_content)
        
        print(f"✓ Configuration file created: {CONFIG_FILE}")
        return True
        
    except Exception as e:
        print(f"✗ Error creating config file: {e}")
        return False

def print_summary():
    """Print summary and next steps"""
    print("\n" + "=" * 70)
    print("✓ SUCCESS! Traffic Generation Complete")
    print("=" * 70)
    
    print("\nGenerated files:")
    print(f"  1. {TRIPS_FILE} - Random trip definitions")
    print(f"  2. {ROUTE_FILE} - Computed vehicle routes")
    print(f"  3. {ADDITIONAL_FILE} - Additional infrastructure")
    print(f"  4. {CONFIG_FILE} - SUMO simulation configuration")
    
    print("\nSimulation parameters:")
    print(f"  - Duration: {TRAFFIC_CONFIG['end']} seconds ({TRAFFIC_CONFIG['end']/60:.1f} minutes)")
    print(f"  - Vehicles: ~{int(TRAFFIC_CONFIG['end'] / TRAFFIC_CONFIG['period'])} vehicles")
    print(f"  - Insertion rate: Every {TRAFFIC_CONFIG['period']} seconds")
    
    print("\n" + "=" * 70)
    print("RUN YOUR SIMULATION:")
    print("=" * 70)
    
    print(f"\n1. Run with GUI (visual):")
    print(f"   sumo-gui -c {CONFIG_FILE}")
    
    print(f"\n2. Run without GUI (faster):")
    print(f"   sumo -c {CONFIG_FILE}")
    
    print(f"\n3. Run with output statistics:")
    print(f"   sumo -c {CONFIG_FILE} --tripinfo-output tripinfo.xml --summary-output summary.xml")
    
    print("\n" + "=" * 70)
    print("CUSTOMIZATION:")
    print("=" * 70)
    print("\nTo change traffic parameters, edit this script and modify:")
    print("  - 'period': Vehicle insertion frequency (lower = more traffic)")
    print("  - 'end': Simulation duration in seconds")
    print("  - 'fringe_factor': Prefer edges (higher = more edge trips)")
    
    print("\n" + "=" * 70)

def main():
    """Main function"""
    print("=" * 70)
    print("Traffic Generator for Electronic City SUMO Network")
    print("=" * 70)
    
    try:
        # Check required files
        if not check_files():
            return 1
        
        # Step 1: Generate random trips
        if not generate_random_trips():
            print("\n✗ Failed at trip generation stage")
            return 1
        
        # Step 2: Generate routes
        if not generate_routes():
            print("\n✗ Failed at route generation stage")
            return 1
        
        # Step 3: Create additional file
        if not create_additional_file():
            print("\n✗ Failed to create additional file")
            return 1
        
        # Step 4: Create config file
        if not create_config_file():
            print("\n✗ Failed to create configuration file")
            return 1
        
        # Print summary
        print_summary()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n✗ Process interrupted by user")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())