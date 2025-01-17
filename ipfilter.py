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
from live_map import serve_map

def get_asn_info(ip, asn_reader):
    try:
        response = asn_reader.asn(ip)
        return {
            'asn': str(response.autonomous_system_number),
            'asn_description': response.autonomous_system_organization
        }
    except:
        return {
            'asn': 'Unknown',
            'asn_description': 'Unknown'
        }

def get_ip_info(ip, city_reader, asn_reader=None, include_asn=False):
    try:
        response = city_reader.city(ip)
        info = {
            'ip': ip,
            'country_code': response.country.iso_code.lower() if response.country.iso_code else 'unknown',
            'country_name': response.country.name if response.country.name else 'Unknown',
            'city': response.city.name if response.city.name else 'Unknown',
            'latitude': response.location.latitude if response.location else None,
            'longitude': response.location.longitude if response.location else None
        }
        
        if include_asn and asn_reader:
            asn_info = get_asn_info(ip, asn_reader)
            info.update({
                'asn': asn_info['asn'],
                'asn_description': asn_info['asn_description']
            })
        return info
    except:
        info = {
            'ip': ip,
            'country_code': 'unknown',
            'country_name': 'Unknown',
            'city': 'Unknown',
            'latitude': None,
            'longitude': None
        }
        if include_asn:
            info.update({
                'asn': 'Unknown',
                'asn_description': 'Unknown'
            })
        return info

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
    parser.add_argument('-f', '--filter', help='Filter by country code(s) (e.g., hk for Hong Kong, or sg,hk for multiple)')
    parser.add_argument('-c', '--country', action='store_true', help='Include country information in output')
    parser.add_argument('-a', '--asn', action='store_true', help='Include ASN information')
    parser.add_argument('-s', '--split', action='store_true', help='Split output into separate files by country code')
    parser.add_argument('--live', action='store_true', help='Show live visualization in web browser')
    
    args = parser.parse_args()

    # Check if GeoLite2 databases exist
    city_db_path = 'GeoLite2-City.mmdb'
    asn_db_path = 'GeoLite2-ASN.mmdb'
    
    if not os.path.exists(city_db_path):
        print("Error: GeoLite2-City database not found. Please download it from MaxMind and place it in the same directory.")
        sys.exit(1)

    if args.asn and not os.path.exists(asn_db_path):
        print("Error: GeoLite2-ASN database not found. Please download it from MaxMind and place it in the same directory.")
        sys.exit(1)

    unique_ips = set()
    ip_info_list = []
    
    try:
        # Initialize GeoIP2 readers
        city_reader = geoip2.database.Reader(city_db_path)
        asn_reader = geoip2.database.Reader(asn_db_path) if args.asn else None

        # Read and process input file
        with open(args.input, 'r') as infile:
            for line in infile:
                ip = extract_ip(line)
                if ip:
                    unique_ips.add(ip)

        # Process IPs with geolocation
        for ip in sorted(unique_ips):
            ip_info = get_ip_info(ip, city_reader, asn_reader, args.asn or args.live)
            ip_info_list.append(ip_info)

        # Filter by country code if specified
        if args.filter:
            # Split filter into list of country codes
            country_codes = [code.strip().lower() for code in args.filter.split(',')]
            ip_info_list = [info for info in ip_info_list if info['country_code'] in country_codes]

        # Launch live visualization if requested
        if args.live:
            print("Launching live visualization in your web browser...")
            serve_map(ip_info_list)
            return

        # Write output
        if args.split:
            # Group IPs by country code
            country_groups = {}
            for info in ip_info_list:
                country_code = info['country_code']
                if country_code not in country_groups:
                    country_groups[country_code] = []
                country_groups[country_code].append(info)

            # Write separate files for each country
            output_base = os.path.splitext(args.output)[0]
            for country_code, country_ips in country_groups.items():
                output_file = f"{output_base}_{country_code}.csv"
                with open(output_file, 'w', newline='') as outfile:
                    # Prepare fieldnames based on included information
                    fieldnames = ['ip']
                    if args.country:
                        fieldnames.extend(['country_code', 'country_name', 'city', 'latitude', 'longitude'])
                    if args.asn:
                        fieldnames.extend(['asn', 'asn_description'])
                    
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Write only selected fields
                    for info in country_ips:
                        row = {'ip': info['ip']}
                        if args.country:
                            row.update({
                                'country_code': info['country_code'],
                                'country_name': info['country_name'],
                                'city': info['city'],
                                'latitude': info['latitude'],
                                'longitude': info['longitude']
                            })
                        if args.asn:
                            row.update({
                                'asn': info['asn'],
                                'asn_description': info['asn_description']
                            })
                        writer.writerow(row)
            print(f"Successfully processed {len(ip_info_list)} IP addresses into {len(country_groups)} country-specific CSV files.")
        else:
            with open(args.output, 'w', newline='') as outfile:
                # Prepare fieldnames based on included information
                fieldnames = ['ip']
                if args.country:
                    fieldnames.extend(['country_code', 'country_name', 'city', 'latitude', 'longitude'])
                if args.asn:
                    fieldnames.extend(['asn', 'asn_description'])
                
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write only selected fields
                for info in ip_info_list:
                    row = {'ip': info['ip']}
                    if args.country:
                        row.update({
                            'country_code': info['country_code'],
                            'country_name': info['country_name'],
                            'city': info['city'],
                            'latitude': info['latitude'],
                            'longitude': info['longitude']
                        })
                    if args.asn:
                        row.update({
                            'asn': info['asn'],
                            'asn_description': info['asn_description']
                        })
                    writer.writerow(row)
            print(f"Successfully processed {len(ip_info_list)} IP addresses.")

        city_reader.close()
        if asn_reader:
            asn_reader.close()

    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found.")
    except PermissionError:
        print("Error: Permission denied when accessing files.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main() 