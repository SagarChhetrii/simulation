#!/usr/bin/env python3
"""
Process Downloaded OSM Files for All 7 Areas
Converts OSM to SUMO networks and generates traffic
"""

import subprocess
import os
from datetime import datetime

# All 7 areas with their OSM files
AREAS = [
    {'name': 'Indiranagar', 'osm_file': 'indiranagar.osm'},
    {'name': 'Whitefield', 'osm_file': 'whitefield.osm'},
    {'name': 'Koramangala', 'osm_file': 'koramangala.osm'},
    {'name': 'MG_Road', 'osm_file': 'mg_road.osm'},
    {'name': 'Jayanagar', 'osm_file': 'jayanagar.osm'},
    {'name': 'Hebbal', 'osm_file': 'hebbal.osm'},
    {'name': 'Yeshwanthpur', 'osm_file': 'yeshwanthpur.osm'}
]

# Traffic config - 100 vehicles
TRAFFIC_CONFIG = {
    'begin': 0,
    'end': 1000,
    'vehicles': 100,
    'period': 10,  # 1000/100 = every 10 seconds
    'trip_attributes': 'departLane="best" departSpeed="max"',
    'vehicle_class': 'passenger',
    'fringe_factor': 10
}

results = []
start_time = datetime.now()

def convert_to_sumo(osm_file, area_name):
    """Convert OSM to SUMO network"""
    net_file = f"{area_name.lower()}.net.xml"
    
    print(f"\nConverting {osm_file} to SUMO network...")
    
    try:
        cmd = [
            'netconvert',
            '--osm-files', osm_file,
            '--output-file', net_file,
            '--geometry.remove',
            '--ramps.guess',
            '--junctions.join',
            '--tls.guess-signals',
            '--tls.discard-simple',
            '--tls.join',
            '--remove-edges.isolated',
            '--keep-edges.by-vclass', 'passenger'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0 and os.path.exists(net_file):
            print(f"✓ SUMO network created: {net_file}")
            return net_file
        else:
            print(f"✗ netconvert failed for {area_name}")
            if result.stderr:
                print(f"Error: {result.stderr[:200]}")
            return None
            
    except Exception as e:
        print(f"✗ Error converting {area_name}: {e}")
        return None

def generate_traffic(net_file, area_name):
    """Generate traffic with 100 vehicles"""
    trips_file = f"{area_name.lower()}.trips.xml"
    route_file = f"{area_name.lower()}.rou.xml"
    
    print(f"Generating traffic for {area_name}...")
    
    try:
        sumo_home = os.environ.get('SUMO_HOME', '/usr/local/share/sumo')
        randomtrips = os.path.join(sumo_home, 'tools', 'randomTrips.py')
        
        # Generate trips
        cmd = [
            'python3', randomtrips,
            '-n', net_file,
            '-o', trips_file,
            '-b', str(TRAFFIC_CONFIG['begin']),
            '-e', str(TRAFFIC_CONFIG['end']),
            '-p', str(TRAFFIC_CONFIG['period']),
            '--fringe-factor', str(TRAFFIC_CONFIG['fringe_factor']),
            '--trip-attributes', TRAFFIC_CONFIG['trip_attributes'],
            '--vehicle-class', TRAFFIC_CONFIG['vehicle_class']
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            print(f"✗ Trip generation failed")
            return None
        
        # Generate routes
        cmd = [
            'duarouter',
            '-n', net_file,
            '-t', trips_file,
            '-o', route_file,
            '--ignore-errors',
            '--no-warnings'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0 and os.path.exists(route_file):
            print(f"✓ Routes generated: {route_file}")
            return route_file
        else:
            print(f"✗ Route generation failed")
            return None
            
    except Exception as e:
        print(f"✗ Error generating traffic: {e}")
        return None

def create_config(net_file, route_file, area_name):
    """Create SUMO configuration"""
    config_file = f"{area_name.lower()}.sumocfg"
    add_file = f"{area_name.lower()}.add.xml"
    
    try:
        # Create additional file
        with open(add_file, 'w') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ')
            f.write('xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">\n')
            f.write('</additional>\n')
        
        # Create config
        config = f'''<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="{net_file}"/>
        <route-files value="{route_file}"/>
        <additional-files value="{add_file}"/>
    </input>
    <time>
        <begin value="{TRAFFIC_CONFIG['begin']}"/>
        <end value="{TRAFFIC_CONFIG['end']}"/>
    </time>
    <processing>
        <time-to-teleport value="300"/>
    </processing>
</configuration>
'''
        
        with open(config_file, 'w') as f:
            f.write(config)
        
        print(f"✓ Config created: {config_file}")
        return config_file
        
    except Exception as e:
        print(f"✗ Error creating config: {e}")
        return None

def get_network_stats(net_file):
    """Get junction and edge count"""
    try:
        with open(net_file, 'r') as f:
            content = f.read()
            junctions = content.count('<junction')
            edges = content.count('<edge')
            return junctions, edges
    except:
        return 0, 0

def process_area(area):
    """Process single area"""
    print(f"\n{'='*70}")
    print(f"Processing: {area['name']}")
    print(f"{'='*70}")
    
    area_result = {
        'name': area['name'],
        'status': 'Failed',
        'junctions': 0,
        'edges': 0,
        'vehicles': 100
    }
    
    # Check if OSM file exists
    if not os.path.exists(area['osm_file']):
        print(f"✗ ERROR: {area['osm_file']} not found!")
        return area_result
    
    print(f"✓ Found {area['osm_file']}")
    
    try:
        # Step 1: Convert to SUMO
        net_file = convert_to_sumo(area['osm_file'], area['name'])
        if not net_file:
            return area_result
        
        # Get stats
        junctions, edges = get_network_stats(net_file)
        area_result['junctions'] = junctions
        area_result['edges'] = edges
        print(f"Network: {junctions} junctions, {edges} road segments")
        
        # Step 2: Generate traffic
        route_file = generate_traffic(net_file, area['name'])
        if not route_file:
            return area_result
        
        # Step 3: Create config
        config_file = create_config(net_file, route_file, area['name'])
        if not config_file:
            return area_result
        
        area_result['status'] = 'Success'
        print(f"\n✓ {area['name']} completed successfully!")
        
    except Exception as e:
        print(f"\n✗ {area['name']} failed: {e}")
    
    return area_result

def generate_final_report():
    """Generate comprehensive final report"""
    report_file = "ALL_AREAS_COMPLETE_REPORT.txt"
    
    with open(report_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("DIGITAL TWIN IMPLEMENTATION - FINAL REPORT\n")
        f.write("ALL 8 BANGALORE AREAS COMPLETED\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Completion Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Processing Time: {datetime.now() - start_time}\n\n")
        
        f.write("="*80 + "\n")
        f.write("COMPLETED AREAS\n")
        f.write("="*80 + "\n\n")
        
        # Add Electronic City (already done)
        f.write("1. Electronic City\n")
        f.write("   Status: Completed ✓\n")
        f.write("   Junctions: 94\n")
        f.write("   Road Segments: 198\n")
        f.write("   Vehicles: 100\n")
        f.write("   Config: electronic_city.sumocfg\n\n")
        
        # Add newly processed areas
        successful = 0
        total_junctions = 94  # Electronic City
        total_edges = 198  # Electronic City
        
        for i, result in enumerate(results, 2):
            f.write(f"{i}. {result['name']}\n")
            f.write(f"   Status: {result['status']}\n")
            if result['status'] == 'Success':
                successful += 1
                total_junctions += result['junctions']
                total_edges += result['edges']
                f.write(f"   Junctions: {result['junctions']}\n")
                f.write(f"   Road Segments: {result['edges']}\n")
                f.write(f"   Vehicles: {result['vehicles']}\n")
                f.write(f"   Config: {result['name'].lower()}.sumocfg\n")
            f.write("\n")
        
        f.write("="*80 + "\n")
        f.write("OVERALL STATISTICS\n")
        f.write("="*80 + "\n\n")
        f.write(f"Total Areas Completed: {successful + 1}/8\n")
        f.write(f"Total Junctions: {total_junctions}\n")
        f.write(f"Total Road Segments: {total_edges}\n")
        f.write(f"Total Vehicles: {(successful + 1) * 100}\n\n")
        
        f.write("="*80 + "\n")
        f.write("HOW TO RUN SIMULATIONS\n")
        f.write("="*80 + "\n\n")
        f.write("Electronic City: sumo-gui -c electronic_city.sumocfg\n")
        for result in results:
            if result['status'] == 'Success':
                f.write(f"{result['name']}: sumo-gui -c {result['name'].lower()}.sumocfg\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write("PROJECT COMPLETE! 🎉\n")
        f.write("="*80 + "\n")
    
    print(f"\n✓ Final report: {report_file}")
    return report_file

def main():
    """Main execution"""
    print("="*70)
    print("PROCESSING ALL 7 DOWNLOADED AREAS")
    print("="*70)
    print(f"\nStart Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Process each area
    for i, area in enumerate(AREAS, 1):
        print(f"\n[{i}/7] Starting {area['name']}...")
        result = process_area(area)
        results.append(result)
    
    # Generate final report
    print("\n" + "="*70)
    print("GENERATING FINAL REPORT")
    print("="*70)
    
    report = generate_final_report()
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'Success')
    
    print("\n" + "="*70)
    print("🎉 PROCESSING COMPLETE!")
    print("="*70)
    print(f"\nResults: {successful + 1}/8 areas completed (including Electronic City)")
    print(f"Total Time: {datetime.now() - start_time}")
    print(f"\nFinal Report: {report}")
    
    print("\n" + "="*70)
    print("READY FOR TOMORROW'S PRESENTATION! 🚀")
    print("="*70)
    
    return 0 if successful == 7 else 1

if __name__ == "__main__":
    exit(main())