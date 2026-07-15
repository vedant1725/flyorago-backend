from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import AeroDataBoxService
import logging

logger = logging.getLogger(__name__)

class FlightSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        flight_number = request.query_params.get('flight')
        travel_date = request.query_params.get('date')

        if not flight_number or not travel_date:
            return Response(
                {"error": "Both 'flight' and 'date' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            flight_data = AeroDataBoxService.fetch_flight(flight_number, travel_date)
            
            if not flight_data:
                return Response(
                    {"error": "Flight not found for the given date."},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            return Response(flight_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"FlightSearchView Error: {error_msg}")
            
            if "Rate Limit Exceeded" in error_msg:
                return Response(
                    {"error": "Flight API rate limit exceeded. Please try again later."},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            elif "Network error" in error_msg:
                return Response(
                    {"error": "Network timeout while fetching flight data. Please try again."},
                    status=status.HTTP_504_GATEWAY_TIMEOUT
                )
            else:
                return Response(
                    {"error": f"An internal API error occurred: {error_msg}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
