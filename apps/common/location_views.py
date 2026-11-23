import json
import urllib.request
import urllib.parse
from rest_framework import views, permissions, status
from rest_framework.response import Response
from common.responses import success_response, failure_response

class LocationSearchView(views.APIView):
    """
    Search All-India locations, cities, towns, transit hubs, and pin codes dynamically.
    Returns live geocoded Indian locations formatted as:
    '{City/Area}, {State}, {Pincode}' matching Web frontend & backend format exactly.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query or len(query) < 2:
            return success_response(data=[], message="Query too short")

        results = []
        seen = set()

        # 1. First, check if input is a 6-digit Indian PIN code
        if query.isdigit() and len(query) == 6:
            try:
                pin_url = f"https://api.postalpincode.in/pincode/{query}"
                req = urllib.request.Request(pin_url, headers={'User-Agent': 'FlyoraGo/1.0'})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    pin_data = json.loads(resp.read().decode('utf-8'))
                    if pin_data and pin_data[0].get('Status') == 'Success':
                        post_offices = pin_data[0].get('PostOffice', [])
                        for po in post_offices[:5]:
                            name = po.get('Name')
                            state = po.get('State')
                            district = po.get('District')
                            pincode = po.get('Pincode')
                            formatted = f"{name}, {state}, {pincode}"
                            if formatted.lower() not in seen:
                                seen.add(formatted.lower())
                                results.append({
                                    "id": f"pin-{pincode}-{name}",
                                    "name": name,
                                    "secondary": f"{district}, {state} · {pincode}",
                                    "formatted": formatted,
                                    "city": name,
                                    "state": state,
                                    "pincode": pincode,
                                    "type": "pincode"
                                })
            except Exception as e:
                print("Postal PIN API lookup error:", e)

        # 2. Query OpenStreetMap Nominatim for exact Indian cities, towns, localities & pincodes
        try:
            encoded_q = urllib.parse.quote(query)
            osm_url = f"https://nominatim.openstreetmap.org/search?q={encoded_q}&format=json&countrycodes=in&addressdetails=1&limit=8"
            req = urllib.request.Request(osm_url, headers={'User-Agent': 'FlyoraGo-LocationSearch/1.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                osm_data = json.loads(resp.read().decode('utf-8'))
                for item in osm_data:
                    addr = item.get('address', {})
                    city = (
                        addr.get('city') or
                        addr.get('town') or
                        addr.get('village') or
                        addr.get('suburb') or
                        addr.get('county') or
                        item.get('name')
                    )
                    state = addr.get('state') or 'India'
                    pincode = addr.get('postcode') or ''

                    if pincode:
                        formatted = f"{city}, {state}, {pincode}"
                        secondary = f"{state}, India · {pincode}"
                    else:
                        formatted = f"{city}, {state}"
                        secondary = f"{state}, India"

                    if formatted.lower() not in seen:
                        seen.add(formatted.lower())
                        results.append({
                            "id": f"osm-{item.get('place_id', len(results))}",
                            "name": city,
                            "secondary": secondary,
                            "formatted": formatted,
                            "city": city,
                            "state": state,
                            "pincode": pincode,
                            "type": item.get('type', 'locality')
                        })
        except Exception as e:
            print("OSM Location lookup error:", e)

        return success_response(data=results, message="Locations fetched successfully")
