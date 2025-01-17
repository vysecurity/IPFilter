# IP Filter Tool

Author: Vincent Yiu (@vysecurity)

A Python tool for processing and filtering IP addresses from various formats, with geolocation capabilities.

## Features

- Extracts IP addresses from multiple formats:
  - Plain IP addresses (e.g., `1.1.1.1`)
  - IP:Port combinations (e.g., `1.1.1.1:80`)
  - URLs (e.g., `https://1.1.1.1`)
- Removes duplicates and provides unique IPs
- Geolocation support using MaxMind's GeoLite2 database
- ASN (Autonomous System Number) lookup support
- Country-based filtering
- CSV output option with detailed location information
- Ability to split output by country into separate files

## Installation

1. Clone the repository:
```bash
git clone https://github.com/vysecurity/IPFilter
cd IPFilter
```

2. Install required Python packages:
```bash
pip3 install -r requirements.txt
```

3. Download MaxMind GeoLite2 Databases:
   - Sign up at [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
   - Download the GeoLite2 City database and GeoLite2 ASN database
   - Place both `.mmdb` files in the same directory as the script
   - Rename them to `GeoLite2-City.mmdb` and `GeoLite2-ASN.mmdb` respectively

## Usage

### Input File Format
The tool accepts various formats in the input file. Each line can be in any of these formats:
```
1.1.1.1
1.1.1.1:80
https://1.1.1.1
http://1.1.1.1:8080
```

### Basic Operations

1. Extract unique IPs from a file:
```bash
python3 ipfilter.py -i input.txt -o output.txt
```

2. Filter IPs from a specific country (e.g., Hong Kong):
```bash
python3 ipfilter.py -i input.txt -o output.txt -f hk
```

3. Get detailed location information in CSV format:
```bash
python3 ipfilter.py -i input.txt -o output.txt -c
```

4. Include ASN information:
```bash
python3 ipfilter.py -i input.txt -o output.txt -a
```

5. Split output by country into separate files:
```bash
python3 ipfilter.py -i input.txt -o output.txt -s
```

### Real-World Example

Process a list of Fortinet IPs with all features enabled (CSV output, ASN information, and country-based splitting):
```bash
python3 ipfilter.py -i fortinet.txt -o output.txt -c -a -s
```

This command will:
- Read IPs from `fortinet.txt`
- Create CSV files for each country (e.g., `output_us.txt`, `output_sg.txt`)
- Include full geolocation data
- Add ASN information for each IP
- Split results by country

For example, if `fortinet.txt` contains IPs from US and Singapore, you'll get:
- `output_us.txt` with US-based Fortinet IPs
- `output_sg.txt` with Singapore-based Fortinet IPs

Each file will be in CSV format with full details:
```csv
ip,country_code,country_name,city,latitude,longitude,asn,asn_description
192.0.2.1,us,United States,Sunnyvale,37.3861,-122.0337,12345,Fortinet Inc
192.0.2.2,sg,Singapore,Singapore,1.3521,103.8198,45678,Fortinet Inc
```

### Example Input/Output

Input file (`input.txt`):
```
1.1.1.1
1.1.1.1:80
https://1.1.1.1
8.8.8.8
```

Basic output (`output.txt`):
```
1.1.1.1
8.8.8.8
```

Output with ASN (`-a` flag):
```
1.1.1.1 (ASN: 13335 - Cloudflare, Inc.)
8.8.8.8 (ASN: 15169 - Google LLC)
```

CSV output with `-c -a` flags:
```csv
ip,country_code,country_name,city,latitude,longitude,asn,asn_description
1.1.1.1,au,Australia,Research,-37.7,145.1833,13335,Cloudflare, Inc.
8.8.8.8,us,United States,Mountain View,37.386,-122.0838,15169,Google LLC
```

Split output with `-s` flag creates separate files for each country:
- `output_au.txt` (Australian IPs)
- `output_us.txt` (US IPs)

## Arguments

- `-i, --input`: Input file path (required)
- `-o, --output`: Output file path (required)
- `-f, --filter`: Filter by country code (e.g., hk for Hong Kong)
- `-c, --csv`: Output as CSV with location information
- `-a, --asn`: Include ASN information in the output
- `-s, --split`: Split output into separate files by country code

## CSV Output Format

When using the `-c` flag, the output CSV includes:
- IP address
- Country code
- Country name
- City
- Latitude
- Longitude

When adding `-a` flag:
- ASN (Autonomous System Number)
- ASN Description