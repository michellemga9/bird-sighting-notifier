#!/usr/bin/env python3
"""
Rare Bird Sighting Alerts
Monitors eBird for rare/notable bird sightings near your location
"""

import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class BirdNotifier:
    def __init__(self):
        # eBird API configuration
        self.ebird_api_key = os.getenv('EBIRD_API_KEY')
        self.base_url = "https://api.ebird.org/v2"
        
        # Your location (Märsta, Stockholm as default)
        self.latitude = float(os.getenv('LATITUDE', '59.6167'))
        self.longitude = float(os.getenv('LONGITUDE', '17.8667'))
        self.radius_km = int(os.getenv('RADIUS_KM', '25'))  # Search radius
        
        # How many days back to check
        self.days_back = int(os.getenv('DAYS_BACK', '3'))
        
    def get_notable_sightings(self) -> List[Dict]:
        """Fetch notable/rare bird sightings from eBird"""
        try:
            # Notable observations endpoint
            url = f"{self.base_url}/data/obs/geo/recent/notable"
            
            headers = {
                'x-ebirdapitoken': self.ebird_api_key
            }
            
            params = {
                'lat': self.latitude,
                'lng': self.longitude,
                'dist': self.radius_km,
                'back': self.days_back,
                'detail': 'full'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            sightings = response.json()
            print(f"Found {len(sightings)} notable bird sightings")
            
            return sightings
            
        except Exception as e:
            print(f"Error fetching bird sightings: {e}")
            return []
    
    def get_species_info(self, species_code: str) -> Optional[Dict]:
        """Get additional info about a species"""
        try:
            # Get taxonomy info
            url = f"{self.base_url}/ref/taxonomy/ebird"
            headers = {'x-ebirdapitoken': self.ebird_api_key}
            params = {'species': species_code, 'fmt': 'json'}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.ok:
                data = response.json()
                return data[0] if data else None
            return None
        except:
            return None
    
    def filter_new_sightings(self, sightings: List[Dict]) -> List[Dict]:
        """Filter out sightings we've already notified about"""
        # In production, you'd store notified sightings in a file/database
        # For now, we'll just return all sightings
        # You can add a simple JSON file to track what's been sent
        
        return sightings
    
    def send_email_notification(self, sightings: List[Dict]):
        """Send email notification about rare bird sightings"""
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        receiver_emails = os.getenv('RECEIVER_EMAIL')
        
        if not all([sender_email, sender_password, receiver_emails]):
            print("Email credentials not configured")
            return
        
        if not sightings:
            print("No sightings to notify about")
            return
        
        receiver_list = [email.strip() for email in receiver_emails.split(',')]
        
        subject = f"🐦 {len(sightings)} Rare Bird Sighting{'s' if len(sightings) > 1 else ''} Alert!"
        body = self._format_email_body(sightings)
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ', '.join(receiver_list)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            print(f"Email notification sent to {len(receiver_list)} recipient(s)!")
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def _format_email_body(self, sightings: List[Dict]) -> str:
        """Format HTML email body"""
        
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #4CAF50;">🐦 Rare Bird Sightings Alert!</h2>
            <p><strong>{len(sightings)} notable bird{'s' if len(sightings) > 1 else ''} spotted within {self.radius_km}km of your location!</strong></p>
            <p style="color: #666;"><em>Märsta, Stockholm area</em></p>
            
            <div style="margin: 20px 0;">
        """
        
        for sighting in sightings[:10]:  # Limit to 10 most recent
            species_name = sighting.get('comName', 'Unknown species')
            scientific_name = sighting.get('sciName', '')
            location = sighting.get('locName', 'Unknown location')
            obs_date = sighting.get('obsDt', '')
            how_many = sighting.get('howMany', 1)
            lat = sighting.get('lat', 0)
            lng = sighting.get('lng', 0)
            
            # Format date
            try:
                dt = datetime.fromisoformat(obs_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = obs_date
            
            # Google Maps link
            maps_url = f"https://www.google.com/maps?q={lat},{lng}"
            
            html += f"""
                <div style="background: #f9f9f9; border-left: 4px solid #4CAF50; padding: 15px; margin: 15px 0; border-radius: 5px;">
                    <h3 style="color: #333; margin: 0 0 10px 0;">{species_name}</h3>
                    <p style="color: #666; font-style: italic; margin: 5px 0;">{scientific_name}</p>
                    <p style="margin: 5px 0;"><strong>📍 Location:</strong> {location}</p>
                    <p style="margin: 5px 0;"><strong>🕐 When:</strong> {formatted_date}</p>
                    <p style="margin: 5px 0;"><strong>🔢 Count:</strong> {how_many} individual{'s' if how_many != 1 else ''}</p>
                    <p style="margin: 10px 0;">
                        <a href="{maps_url}" style="background: #4CAF50; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            📍 View on Map
                        </a>
                        <a href="https://ebird.org/map" style="background: #2196F3; color: white; padding: 8px 16px; text-decoration: none; border-radius: 5px; display: inline-block; margin-left: 10px;">
                            🐦 View on eBird
                        </a>
                    </p>
                </div>
            """
        
        html += """
            </div>
            
            <div style="background: #e8f5e9; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h3 style="color: #2e7d32;">🔍 Birding Tips:</h3>
                <ul style="color: #333;">
                    <li>Bring binoculars and a field guide</li>
                    <li>Visit early morning (5-9 AM) or late afternoon (4-7 PM)</li>
                    <li>Be quiet and patient</li>
                    <li>Check weather conditions before going</li>
                    <li>Respect private property and wildlife</li>
                </ul>
            </div>
            
            <p style="margin-top: 20px; color: #666; font-size: 0.9em;">
                <em>Happy birding! 🐦 Data from eBird</em>
            </p>
        </body>
        </html>
        """
        return html
    
    def run(self):
        """Main execution"""
        print(f"Checking for rare bird sightings within {self.radius_km}km...")
        print(f"Location: {self.latitude}, {self.longitude}")
        
        # Get notable sightings
        sightings = self.get_notable_sightings()
        
        if not sightings:
            print("No notable bird sightings found")
            return {
                'alert': False,
                'sightings_count': 0,
                'sightings': []
            }
        
        # Filter new sightings (ones we haven't notified about)
        new_sightings = self.filter_new_sightings(sightings)
        
        if new_sightings:
            print(f"⚡ BIRD ALERT! Found {len(new_sightings)} new notable sightings!")
            
            # Send notifications
            self.send_email_notification(new_sightings)
            
            return {
                'alert': True,
                'sightings_count': len(new_sightings),
                'sightings': new_sightings
            }
        else:
            print("All sightings have been notified about previously")
            return {
                'alert': False,
                'sightings_count': 0,
                'sightings': []
            }


if __name__ == "__main__":
    notifier = BirdNotifier()
    result = notifier.run()
    
    print("\n" + "="*50)
    print(f"Alert: {result['alert']}")
    print(f"Notable sightings found: {result['sightings_count']}")
    if result['sightings']:
        print("\nSpecies found:")
        for s in result['sightings'][:5]:
            print(f"  - {s.get('comName', 'Unknown')}")
    print("="*50)
