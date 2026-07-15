import os
import requests
import json
from datetime import datetime, date
from django.core.cache import cache
from .models import Flight

class AeroDataBoxService:
    BASE_URL = "https://aerodatabox.p.rapidapi.com/flights/number"
    
    @classmethod
    def get_api_key(cls):
        return os.environ.get('AERODATABOX_API_KEY', '')
        
    @classmethod
    def fetch_flight(cls, flight_number, travel_date):
        """
        Fetches flight data from AeroDataBox, updates DB, caches, and returns data.
        """
        # Ensure travel_date is a string 'YYYY-MM-DD'
        if isinstance(travel_date, date):
            travel_date = travel_date.strftime('%Y-%m-%d')
            
        cache_key = f"flight_{flight_number}_{travel_date}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
            
        api_key = cls.get_api_key()
        if not api_key:
            raise Exception("AeroDataBox API Key is missing from environment variables.")
            
        url = f"{cls.BASE_URL}/{flight_number}/{travel_date}"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 404:
                return None  # Flight not found
            elif response.status_code == 429:
                raise Exception("AeroDataBox Rate Limit Exceeded")
            elif response.status_code != 200:
                raise Exception(f"AeroDataBox API Error: {response.status_code} - {response.text}")
                
            data = response.json()
            
            # The API returns a list of flights. We take the first one.
            if not isinstance(data, list) or len(data) == 0:
                return None
                
            flight_data = data[0]
            
            # Extract and map fields safely
            mapped_data = cls._map_response_to_model(flight_number, travel_date, flight_data)
            
            # Save or Update Database
            flight_instance, created = Flight.objects.update_or_create(
                flight_number=flight_number,
                travel_date=travel_date,
                defaults=mapped_data
            )
            
            # Cache for 6 hours (21600 seconds)
            cache.set(cache_key, mapped_data, timeout=21600)
            
            return mapped_data
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error connecting to AeroDataBox: {str(e)}")

    @classmethod
    def _map_response_to_model(cls, flight_number, travel_date, data):
        # Nested safe access helper
        def safe_get(d, *keys, default=None):
            for k in keys:
                if not isinstance(d, dict) or k not in d:
                    return default
                d = d[k]
            return d

        mapped = {
            'call_sign': safe_get(data, 'callSign'),
            'airline_name': safe_get(data, 'airline', 'name'),
            'airline_iata': safe_get(data, 'airline', 'iata'),
            'airline_icao': safe_get(data, 'airline', 'icao'),
            
            'aircraft_model': safe_get(data, 'aircraft', 'model'),
            'aircraft_registration': safe_get(data, 'aircraft', 'reg'),
            'aircraft_modes': safe_get(data, 'aircraft', 'modeS'),
            
            'flight_status': safe_get(data, 'status'),
            'cargo_status': safe_get(data, 'isCargo'),
            'codeshare_status': safe_get(data, 'isCodeshare'),
            
            'distance_km': safe_get(data, 'greatCircleDistance', 'km'),
            'distance_miles': safe_get(data, 'greatCircleDistance', 'mile'),
        }

        # Departure
        departure = safe_get(data, 'departure', default={})
        mapped.update({
            'departure_airport_name': safe_get(departure, 'airport', 'name'),
            'departure_airport_short_name': safe_get(departure, 'airport', 'shortName'),
            'departure_municipality': safe_get(departure, 'airport', 'municipalityName'),
            'departure_country': safe_get(departure, 'airport', 'countryCode'),
            'departure_icao': safe_get(departure, 'airport', 'icao'),
            'departure_iata': safe_get(departure, 'airport', 'iata'),
            'departure_latitude': safe_get(departure, 'airport', 'location', 'lat'),
            'departure_longitude': safe_get(departure, 'airport', 'location', 'lon'),
            'departure_timezone': safe_get(departure, 'airport', 'timeZone'),
            
            'departure_scheduled_utc': safe_get(departure, 'scheduledTimeUtc'),
            'departure_scheduled_local': safe_get(departure, 'scheduledTimeLocal'),
            'departure_revised_utc': safe_get(departure, 'revisedTimeUtc'),
            'departure_revised_local': safe_get(departure, 'revisedTimeLocal'),
            'departure_runway_time': safe_get(departure, 'runwayTimeUtc'),
            'departure_terminal': safe_get(departure, 'terminal'),
        })

        # Arrival
        arrival = safe_get(data, 'arrival', default={})
        mapped.update({
            'arrival_airport_name': safe_get(arrival, 'airport', 'name'),
            'arrival_short_name': safe_get(arrival, 'airport', 'shortName'),
            'arrival_municipality': safe_get(arrival, 'airport', 'municipalityName'),
            'arrival_country': safe_get(arrival, 'airport', 'countryCode'),
            'arrival_icao': safe_get(arrival, 'airport', 'icao'),
            'arrival_iata': safe_get(arrival, 'airport', 'iata'),
            'arrival_latitude': safe_get(arrival, 'airport', 'location', 'lat'),
            'arrival_longitude': safe_get(arrival, 'airport', 'location', 'lon'),
            'arrival_timezone': safe_get(arrival, 'airport', 'timeZone'),
            
            'arrival_scheduled_utc': safe_get(arrival, 'scheduledTimeUtc'),
            'arrival_scheduled_local': safe_get(arrival, 'scheduledTimeLocal'),
            'arrival_revised_utc': safe_get(arrival, 'revisedTimeUtc'),
            'arrival_revised_local': safe_get(arrival, 'revisedTimeLocal'),
            'arrival_runway_time': safe_get(arrival, 'runwayTimeUtc'),
            'arrival_runway': safe_get(arrival, 'runway'),
        })
        
        # Format datetimes
        for key, val in mapped.items():
            if 'time' in key.lower() or 'utc' in key.lower() or 'local' in key.lower():
                if isinstance(val, str) and len(val) > 10 and 'T' not in val and ' ' in val:
                    try:
                        # Convert basic string to ISO if necessary, or let DRF/Django parse it
                        # AeroDataBox typically returns "2026-07-10 12:30Z" or "2026-07-10 12:30"
                        pass
                    except Exception:
                        pass
        return mapped
