from flask import Flask, render_template_string
import folium
from folium import plugins
from collections import defaultdict
import branca.colormap as cm
import webbrowser
import threading
import time
import os

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>IP Filter - Visualization</title>
    <style>
        body { margin: 0; padding: 0; background-color: #0a0a0a; }
        #map { position: absolute; top: 0; bottom: 0; width: 100%; }
        .title {
            position: absolute;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1000;
            background-color: rgba(0, 0, 0, 0.7);
            color: #00ff00;
            padding: 10px 20px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            border: 1px solid #00ff00;
            text-align: center;
        }
        .stats {
            position: absolute;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            background-color: rgba(0, 0, 0, 0.7);
            color: #00ff00;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            border: 1px solid #00ff00;
        }
    </style>
</head>
<body>
    <div class="title">
        <h2 style="margin: 0;">🌐 IP Filter - Threat Intelligence Map 🔒</h2>
        <small>Visualization of infrastructure</small>
    </div>
    <div class="stats">
        <div>Total IPs: {{ total_ips }}</div>
        <div>Countries: {{ total_countries }}</div>
        <div>ASNs: {{ total_asns }}</div>
    </div>
    {{ map_html|safe }}
</body>
</html>
'''

def create_map(ip_data):
    # Create a map centered on the world
    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles='CartoDB dark_matter',  # Dark theme for cybersecurity feel
        prefer_canvas=True
    )

    # Group data by country
    country_data = defaultdict(lambda: {'count': 0, 'asns': defaultdict(set), 'ips': set(), 'cities': set()})
    
    # First pass: collect all data
    for ip in ip_data:
        if ip['latitude'] and ip['longitude']:
            key = (ip['country_code'], ip['country_name'])
            country_data[key]['ips'].add(ip['ip'])
            if ip['city'] != 'Unknown':
                country_data[key]['cities'].add(ip['city'])
            # Only add ASN if it exists and is not Unknown
            if 'asn' in ip and ip['asn'] != 'Unknown' and ip['asn_description'] != 'Unknown':
                asn_key = ip['asn']
                country_data[key]['asns'][asn_key].add(ip['asn_description'])

    # Create heat data
    heat_data = []
    
    # Calculate max count for scaling
    max_count = max([len(data['ips']) for data in country_data.values()]) if country_data else 1
    
    # Create color map for intensity
    colormap = cm.LinearColormap(
        colors=['#00ff00', '#ffff00', '#ff0000'],
        vmin=0,
        vmax=max_count
    )

    # Add markers and heat data
    for country_key, data in country_data.items():
        country_code, country_name = country_key
        unique_ips = len(data['ips'])
        
        # Get a representative location for the country
        country_location = None
        for ip in ip_data:
            if ip['country_code'] == country_code and ip['latitude'] and ip['longitude']:
                country_location = (ip['latitude'], ip['longitude'])
                break
        
        if not country_location:
            continue

        lat, lon = country_location
        
        # Add to heat map data
        heat_data.append([lat, lon, unique_ips])
        
        # Format ASN information
        asn_info = []
        for asn, descriptions in sorted(data['asns'].items()):
            desc = next(iter(descriptions))  # Get the first description (should be same for same ASN)
            asn_info.append(f"ASN {asn} - {desc}")

        # Create popup content with improved styling
        cities_list = sorted(list(data['cities']))
        cities_display = '<br>'.join(cities_list[:5])
        if len(cities_list) > 5:
            cities_display += f'<br>... ({len(cities_list)} total cities)'

        popup_content = f"""
        <div style="
            font-family: 'Courier New', monospace;
            background-color: rgba(0, 0, 0, 0.8);
            color: #00ff00;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #00ff00;
            min-width: 300px;
        ">
            <h4 style="margin: 0 0 10px 0; color: #fff;">{country_name} ({country_code.upper()})</h4>
            <div style="margin: 5px 0;">
                <strong>Unique IPs:</strong> {unique_ips}
            </div>
            <div style="margin: 5px 0;">
                <strong>Unique ASNs:</strong> {len(data['asns'])}
            </div>
            <div style="margin: 5px 0;">
                <strong>Cities:</strong><br>{cities_display}
            </div>
            <div style="
                margin: 10px 0 5px 0;
                max-height: 100px;
                overflow-y: auto;
                font-size: 12px;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 5px;
                border-radius: 3px;
            ">
                <strong>IPs:</strong><br>
                {('<br>'.join(sorted(list(data['ips'])[:10])) + f'<br>... ({len(data["ips"])} total IPs)' if len(data['ips']) > 10 else '<br>'.join(sorted(data['ips'])))}
            </div>
            <div style="
                margin: 10px 0 5px 0;
                max-height: 150px;
                overflow-y: auto;
                font-size: 12px;
                background-color: rgba(0, 0, 0, 0.5);
                padding: 5px;
                border-radius: 3px;
            ">
                <strong>ASNs:</strong><br>
                {('<br>'.join(asn_info[:10]) + f'<br>... ({len(asn_info)} total ASNs)' if len(asn_info) > 10 else '<br>'.join(asn_info))}
            </div>
        </div>
        """
        
        # Create a div with the count for the circle marker
        count_div = folium.DivIcon(
            html=f'<div style="font-family: \'Courier New\', monospace; '
                 f'background-color: rgba(0, 0, 0, 0.7); color: #00ff00; '
                 f'border: 1px solid #00ff00; border-radius: 50%; '
                 f'width: 40px; height: 40px; line-height: 40px; '
                 f'text-align: center; font-weight: bold;">{unique_ips}</div>',
            icon_size=(40, 40)
        )
        
        # Add circle marker
        folium.CircleMarker(
            location=[lat, lon],
            radius=min(unique_ips * 3, 20),
            popup=folium.Popup(popup_content, max_width=400),
            color='#00ff00',
            fill=True,
            fillColor=colormap(unique_ips),
            fillOpacity=0.7
        ).add_to(m)

        # Add count label
        folium.Marker(
            location=[lat, lon],
            icon=count_div,
            popup=folium.Popup(popup_content, max_width=400)
        ).add_to(m)

    # Add heat layer
    plugins.HeatMap(heat_data, min_opacity=0.3, radius=25).add_to(m)
    
    # Add legend
    colormap.add_to(m)
    colormap.caption = 'Number of Unique IPs per country'

    return m

def serve_map(ip_data):
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        m = create_map(ip_data)
        
        # Calculate statistics more accurately
        total_ips = len(set(ip['ip'] for ip in ip_data))
        total_countries = len(set(ip['country_code'] for ip in ip_data))
        
        # Count unique ASNs globally, excluding Unknown values
        asns = set()
        for ip in ip_data:
            if ('asn' in ip and 
                ip['asn'] != 'Unknown' and 
                'asn_description' in ip and 
                ip['asn_description'] != 'Unknown'):
                asns.add(ip['asn'])
        total_asns = len(asns)

        # Debug print for ASN counting
        print(f"Debug - Total ASNs found: {total_asns}")
        print(f"Debug - Unique ASNs: {asns}")
        
        return render_template_string(
            HTML_TEMPLATE,
            map_html=m.get_root().render(),
            total_ips=total_ips,
            total_countries=total_countries,
            total_asns=total_asns
        )

    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open('http://127.0.0.1:5000/')

    threading.Thread(target=open_browser).start()
    
    # Run the Flask app
    app.run(debug=False, use_reloader=False) 