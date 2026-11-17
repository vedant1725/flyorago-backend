import urllib.request
import urllib.parse
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache for location queries (max 500 recent queries)
_QUERY_CACHE = {}

def get_address_city_district(addr):
    return (
        addr.get('city') or 
        addr.get('town') or 
        addr.get('village') or 
        addr.get('suburb') or 
        addr.get('county') or 
        addr.get('state_district') or 
        ''
    )

class LocationSearchView(APIView):
    """
    All-India Exact Location Search API.
    Returns pinpoint accurate cities, towns, villages, localities,
    neighborhoods, roads, landmarks, and pin codes across all Indian states.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 1:
            return Response({'status': 'success', 'data': []})

        cache_key = query.lower()
        if cache_key in _QUERY_CACHE:
            return Response({'status': 'success', 'data': _QUERY_CACHE[cache_key]})

        results = []
        seen = set()

        # 1. Query OpenStreetMap Nominatim for exact Indian locations
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://nominatim.openstreetmap.org/search?format=json&countrycodes=in&addressdetails=1&limit=8&q={encoded}"
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'FlyoraGo-Location-Service/1.0 (contact@flyorago.com)'}
            )
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                for item in data:
                    addr = item.get('address', {})
                    display_name = item.get('display_name', '')
                    name = item.get('name') or addr.get('suburb') or addr.get('city') or query

                    city = get_address_city_district(addr)
                    state = addr.get('state') or 'India'
                    pincode = addr.get('postcode') or ''

                    # Build primary and secondary labels
                    primary = name
                    secondary_parts = [p for p in [city if city != name else None, state, pincode] if p]
                    secondary = ', '.join(secondary_parts)

                    # Build clean full address
                    full_parts = [p for p in [primary, secondary] if p]
                    formatted = ', '.join(full_parts)

                    key = formatted.lower()
                    if key not in seen:
                        seen.add(key)
                        results.append({
                            'id': f"nom-{item.get('place_id', len(results))}",
                            'name': primary,
                            'secondary': secondary,
                            'formatted': formatted,
                            'city': city or primary,
                            'state': state,
                            'pincode': pincode,
                            'type': item.get('type') or 'locality'
                        })
        except Exception as e:
            logger.warning(f"Nominatim geocoder note: {e}")

        # 2. Query Photon OSM Geocoder bounded to India coordinates
        if len(results) < 5:
            try:
                encoded = urllib.parse.quote(query)
                photon_url = f"https://photon.komoot.io/api/?q={encoded}&limit=6&bbox=68.1,6.5,97.4,35.5"
                req = urllib.request.Request(
                    photon_url, 
                    headers={'User-Agent': 'FlyoraGo-Location-Service/1.0'}
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    pdata = json.loads(resp.read().decode('utf-8'))
                    for f in pdata.get('features', []):
                        props = f.get('properties', {})
                        pname = props.get('name') or query
                        pcity = props.get('city') or props.get('district') or props.get('county') or ''
                        pstate = props.get('state') or 'India'
                        ppostcode = props.get('postcode') or ''

                        primary = pname
                        secondary_parts = [p for p in [pcity if pcity != primary else None, pstate, ppostcode] if p]
                        secondary = ', '.join(secondary_parts)

                        formatted = f"{primary}, {secondary}" if secondary else primary

                        key = formatted.lower()
                        if key not in seen:
                            seen.add(key)
                            results.append({
                                'id': f"phot-{props.get('osm_id', len(results))}",
                                'name': primary,
                                'secondary': secondary,
                                'formatted': formatted,
                                'city': pcity or primary,
                                'state': pstate,
                                'pincode': ppostcode,
                                'type': props.get('osm_value') or 'area'
                            })
            except Exception as pe:
                logger.warning(f"Photon geocoder note: {pe}")

        # Cache top results for speed
        if len(_QUERY_CACHE) > 500:
            _QUERY_CACHE.clear()
        _QUERY_CACHE[cache_key] = results

        return Response({'status': 'success', 'data': results})

