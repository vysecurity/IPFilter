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
- Country-based filtering
- CSV output option with detailed location information

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

3. Download MaxMind GeoLite2 Database:
   - Sign up at [MaxMind GeoLite2](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data)
   - Download the GeoLite2 City database
   - Place the `.mmdb` file in the same directory as the script
   - Rename it to `GeoLite2-City.mmdb`

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
python ipfilter.py -i input.txt -o output.txt
```

2. Filter IPs from a specific country (e.g., Hong Kong):
```bash
python ipfilter.py -i input.txt -o output.txt -f hk
```

3. Get detailed location information in CSV format:
```bash
python ipfilter.py -i input.txt -o output.txt -c
```

4. Combine filtering and CSV output:
```bash
python ipfilter.py -i input.txt -o output.txt -f hk -c
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

CSV output with `-c` flag:
```csv
ip,country_code,country_name,city,latitude,longitude
1.1.1.1,au,Australia,Research,-37.7,145.1833
8.8.8.8,us,United States,Mountain View,37.386,-122.0838
```

## Arguments

- `-i, --input`: Input file path (required)
- `-o, --output`: Output file path (required)
- `-f, --filter`: Filter by country code (e.g., hk for Hong Kong)
- `-c, --csv`: Output as CSV with location information

## CSV Output Format

When using the `-c` flag, the output CSV includes:
- IP address
- Country code
- Country name
- City
- Latitude
- Longitude