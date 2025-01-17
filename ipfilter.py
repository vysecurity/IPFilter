#!/usr/bin/env python3

def print_banner():
    banner = """
╔══════════════════════════════════════════╗
║             IP Filter Tool               ║
║      Author: Vincent Yiu (@vysecurity)   ║
║                                          ║
║  Filters and Geolocates IP Addresses     ║
║  from various formats including URLs     ║
╚══════════════════════════════════════════╝
"""
    print(banner)

import argparse
import re
import csv
from urllib.parse import urlparse
import geoip2.database
import os
import sys

def get_ip_info(ip, reader):
    try:
        response = reader.city(ip)
        return {
            'ip': ip,
            'country_code': response.country.iso_code.lower() if response.country.iso_code else 'unknown',
            'country_name': response.country.name if response.country.name else 'Unknown',
            'city': response.city.name if response.city.name else 'Unknown',
            'latitude': response.location.latitude if response.location else None,
            'longitude': response.location.longitude if response.location else None
        }
    except:
        return {
            'ip': ip,
            'country_code': 'unknown',
            'country_name': 'Unknown',
            'city': 'Unknown',
            'latitude': None,
            'longitude': None
        }
def extract_ip(line):
    # Regular expression for matching IPv4 addresses
    ip_pattern = r'(?:\d{1,3}\.){3}\d{1,3}'
    
    # Remove any whitespace and newlines
    line = line.strip()
    
    # Try to parse as URL first
    try:
        parsed = urlparse(line)
        if parsed.netloc:
            # Extract hostname from URL
            hostname = parsed.netloc.split(':')[0]
            if re.match(ip_pattern, hostname):
                return hostname
    except:
        pass
    
    # Try to match IP:Port pattern
    if ':' in line:
        potential_ip = line.split(':')[0]
        if re.match(ip_pattern, potential_ip):
            return potential_ip
    
    # Try to match plain IP
    if re.match(ip_pattern, line):
        return line
    
    return None

def main():
    print_banner()
    parser = argparse.ArgumentParser(description='Extract and filter IP addresses from a file.')
    parser.add_argument('-i', '--input', required=True, help='Input file path')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('-f', '--filter', help='Filter by country code (e.g., hk for Hong Kong)')
    parser.add_argument('-c', '--csv', action='store_true', help='Output as CSV with location information')
    
    args = parser.parse_args()

    # Check if GeoLite2 database exists
    db_path = 'GeoLite2-City.mmdb'
    if not os.path.exists(db_path):
        print("Error: GeoLite2 database not found. Please download it from MaxMind and place it in the same directory.")
        sys.exit(1)

    unique_ips = set()
    ip_info_list = []
    
    try:
        # Initialize GeoIP2 reader
        reader = geoip2.database.Reader(db_path)

        # Read and process input file
        with open(args.input, 'r') as infile:
            for line in infile:
                ip = extract_ip(line)
                if ip:
                    unique_ips.add(ip)

        # Process IPs with geolocation
        for ip in sorted(unique_ips):
            ip_info = get_ip_info(ip, reader)
            ip_info_list.append(ip_info)

        # Filter by country code if specified
        if args.filter:
            ip_info_list = [info for info in ip_info_list if info['country_code'] == args.filter.lower()]

        # Write output
        with open(args.output, 'w', newline='') as outfile:
            if args.csv:
                writer = csv.DictWriter(outfile, fieldnames=['ip', 'country_code', 'country_name', 'city', 'latitude', 'longitude'])
                writer.writeheader()
                writer.writerows(ip_info_list)
            else:
                for info in ip_info_list:
                    outfile.write(f"{info['ip']}\n")

        print(f"Successfully processed {len(ip_info_list)} IP addresses.")
        reader.close()

    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
    except PermissionError:
        print("Error: Permission denied when accessing files.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 