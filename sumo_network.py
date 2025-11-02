#!/usr/bin/env python3
"""
SUMO Network Generator for Electronic City, Bangalore
Alternative method: Downloads from Geofabrik or BBBike instead of Overpass API
"""

import subprocess
import os
import sys

# Configuration
OSM_FILE = "electronic_city.osm"
SUMO_NET_FILE = "electronic_city.net.xml"

# Electronic City bounding box for filtering
BBOX = {
    'north': 12.8650,
    'south': 12.8300,
    'east': 77.6800,
    'west': 77.6400
}

def check_osmium():
    """Check if osmium-tool is installed"""
    try:
        result = subprocess.run(['osmium', '--version'], capture_output=True, text=True)
        return True
    except FileNotFoundError:
        return False

def method_manual_download():
    """
    Guide user to manually download OSM data
    """
    print("\n" + "=" * 70)
    print("MANUAL DOWNLOAD METHOD")
    print("=" * 70)
    print("\nSince Overpass API is overloaded, let's use a manual download:")
    print("\nOption 1 - BBBike Extract (Recommended - Small area):")
    print("  1. Go to: https://extract.bbbike.org/")
    print("  2. Search for 'Electronic City, Bangalore'")
    print("  3. Draw a box around Electronic City")
    print("  4. Select format: 'OSM XML'")
    print("  5. Enter your email")
    print("  6. Click 'extract' - you'll get a download link via email (5-10 min)")
    print("  7. Download the file and save it as 'electronic_city.osm'")
    
    print("\nOption 2 - Geofabrik (Faster - Larger area):")
    print("  1. Go to: https://download.geofabrik.de/asia/india.html")
    print("  2. Download 'Karnataka' (.osm.pbf file)")
    print("  3. Save it in this directory")
    print("  4. We'll extract Electronic City from it")
    
    print("\nOption 3 - OpenStreetMap Export (Quick - Very small area):")
    print("  1. Go to: https://www.openstreetmap.org/export")
    print("  2. Click 'Manually select a different area'")
    print("  3. Zoom to Electronic City, Bangalore")
    print("  4. Draw a box around the area you want")
    print("  5. Click 'Export' button")
    print("  6. Save as 'electronic_city.osm' in this directory")
    print("  Note: Limited to small areas only!")
    
    print("\n" + "=" * 70)
    print("After downloading, choose what to do:")
    print("=" * 70)
    
    choice = input("\nWhat did you download?\n  1. Already have electronic_city.osm\n  2. Have Karnataka .osm.pbf file\n  3. Want to exit and download first\nEnter choice (1/2/3): ").strip()
    
    return choice

def extract_from_pbf(pbf_file):
    """Extract Electronic City area from Karnataka PBF file"""
    print(f"\nExtracting Electronic City from {pbf_file}...")
    
    if not check_osmium():
        print("\n✗ osmium-tool not found!")
        print("Install it with: brew install osmium-tool")
        return False
    
    try:
        cmd = [
            'osmium', 'extract',
            '-b', f"{BBOX['west']},{BBOX['south']},{BBOX['east']},{BBOX['north']}",
            pbf_file,
            '-o', OSM_FILE,
            '--overwrite'
        ]
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0 and os.path.exists(OSM_FILE):
            print(f"✓ Successfully extracted to {OSM_FILE}")
            return True
        else:
            print(f"✗ Extraction failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def convert_to_sumo(osm_file, sumo_net_file):
    """
    Convert OSM XML to SUMO network using netconvert
    """
    print(f"\nConverting {osm_file} to SUMO network format...")
    
    # Check if OSM file exists
    if not os.path.exists(osm_file):
        print(f"✗ ERROR: {osm_file} not found!")
        return False
    
    file_size = os.path.getsize(osm_file) / (1024 * 1024)  # MB
    print(f"OSM file size: {file_size:.2f} MB")
    
    # Check if netconvert is available
    try:
        result = subprocess.run(
            ['netconvert', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Using netconvert version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("✗ ERROR: 'netconvert' command not found!")
        print("\nPlease install SUMO:")
        print("  macOS: brew install sumo")
        print("  Set SUMO_HOME and add to PATH")
        return False
    except Exception as e:
        print(f"✗ Error checking netconvert: {e}")
        return False
    
    # Convert OSM to SUMO network
    try:
        cmd = [
            'netconvert',
            '--osm-files', osm_file,
            '--output-file', sumo_net_file,
            '--geometry.remove',
            '--ramps.guess',
            '--junctions.join',
            '--tls.guess-signals',
            '--tls.discard-simple',
            '--tls.join',
            '--tls.default-type', 'actuated',
            '--remove-edges.isolated',
            '--keep-edges.by-vclass', 'passenger',
            '--verbose'
        ]
        
        print(f"\nRunning netconvert... (this may take a minute)")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout for large files
        )
        
        if result.returncode == 0:
            if os.path.exists(sumo_net_file):
                file_size = os.path.getsize(sumo_net_file) / 1024  # KB
                print(f"✓ SUMO network created successfully ({file_size:.2f} KB)")
                print(f"✓ Output file: {sumo_net_file}")
                return True
            else:
                print(f"✗ netconvert completed but output file not found")
                return False
        else:
            print(f"✗ netconvert failed with return code {result.returncode}")
            if result.stderr:
                print(f"\nError output:\n{result.stderr[:500]}")  # Show first 500 chars
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ netconvert timed out")
        return False
    except Exception as e:
        print(f"✗ Error running netconvert: {e}")
        return False

def main():
    """
    Main function
    """
    print("=" * 70)
    print("SUMO Network Generator for Electronic City, Bangalore")
    print("Alternative Method - Manual Download")
    print("=" * 70)
    print("\nThe Overpass API is currently overloaded.")
    print("This script will help you use alternative download methods.")
    
    try:
        choice = method_manual_download()
        
        if choice == '1':
            # User already has electronic_city.osm
            if not os.path.exists(OSM_FILE):
                print(f"\n✗ ERROR: {OSM_FILE} not found in current directory!")
                print("Please make sure the file is named exactly 'electronic_city.osm'")
                return 1
            print(f"\n✓ Found {OSM_FILE}")
            
        elif choice == '2':
            # User has Karnataka PBF file
            pbf_file = input("\nEnter the PBF filename (e.g., karnataka-latest.osm.pbf): ").strip()
            if not os.path.exists(pbf_file):
                print(f"✗ ERROR: {pbf_file} not found!")
                return 1
            if not extract_from_pbf(pbf_file):
                return 1
                
        elif choice == '3':
            print("\n👋 Okay! Download the OSM file first, then run this script again.")
            print("\nRecommended: Use OpenStreetMap Export for quick small area download")
            print("URL: https://www.openstreetmap.org/export")
            return 0
        else:
            print("Invalid choice!")
            return 1
        
        # Convert to SUMO
        if not convert_to_sumo(OSM_FILE, SUMO_NET_FILE):
            print("\n✗ Failed to convert to SUMO network.")
            return 1
        
        # Success!
        print("\n" + "=" * 70)
        print("✓ SUCCESS! SUMO network generation completed")
        print("=" * 70)
        print(f"\nGenerated files:")
        print(f"  1. {OSM_FILE} - OpenStreetMap XML file")
        print(f"  2. {SUMO_NET_FILE} - SUMO network file (ready for simulation)")
        
        print(f"\nNext steps:")
        print(f"  - View network: sumo-gui -n {SUMO_NET_FILE}")
        print(f"  - Generate traffic: randomTrips.py or activitygen")
        print(f"  - Create simulation config and run!")
        
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