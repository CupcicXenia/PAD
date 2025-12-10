from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import os
import logging
from datetime import datetime

app = FastAPI(title="Hotel Booking API Gateway", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Microservices URLs
HOTEL_SEARCH_SERVICE = os.getenv('HOTEL_SEARCH_SERVICE', 'http://hotel-search-service:5001')
BOOKING_SERVICE = os.getenv('BOOKING_SERVICE', 'http://booking-service:5002')
ROOM_SERVICE = os.getenv('ROOM_SERVICE', 'http://room-service:5003')
NOTIFICATION_SERVICE = os.getenv('NOTIFICATION_SERVICE', 'http://notification-service:5004')

# Pydantic models
class HotelSearchRequest(BaseModel):
    city: str
    check_in: str
    check_out: str

class BookingRequest(BaseModel):
    hotel_id: int
    hotel_name: str
    check_in: str
    check_out: str
    room_type: str
    quantity: int
    tariff: str
    guest_name: str
    guest_email: str
    guest_phone: str
    extras: List[str] = []

class PriceCalculationRequest(BaseModel):
    room_type: str
    days: int
    tariff: str = "Flexible"
    extras: List[str] = []

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway"}

@app.post("/api/search")
async def search_hotels(search_request: HotelSearchRequest):
    """Search hotels by city and dates"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{HOTEL_SEARCH_SERVICE}/api/search",
                json=search_request.dict()
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error searching hotels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hotel search service error: {str(e)}")

@app.get("/api/hotels/{hotel_id}")
async def get_hotel(hotel_id: int):
    """Get hotel details by ID"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{HOTEL_SEARCH_SERVICE}/api/hotels/{hotel_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting hotel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hotel search service error: {str(e)}")

@app.get("/api/rooms/types")
async def get_room_types():
    """Get all available room types"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ROOM_SERVICE}/api/rooms/types")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting room types: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Room service error: {str(e)}")

@app.get("/api/rooms/types/{room_type}")
async def get_room_type(room_type: str):
    """Get specific room type details"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ROOM_SERVICE}/api/rooms/types/{room_type}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting room type: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Room service error: {str(e)}")

@app.get("/api/pricing/tariffs")
async def get_tariffs():
    """Get all pricing tariffs"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ROOM_SERVICE}/api/pricing/tariffs")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting tariffs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Room service error: {str(e)}")

@app.get("/api/services/extra")
async def get_extra_services():
    """Get all extra services"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ROOM_SERVICE}/api/services/extra")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting extra services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Room service error: {str(e)}")

@app.post("/api/pricing/calculate")
async def calculate_price(price_request: PriceCalculationRequest):
    """Calculate total price"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{ROOM_SERVICE}/api/pricing/calculate",
                json=price_request.dict()
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error calculating price: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Room service error: {str(e)}")

@app.get("/api/rooms/availability")
async def get_room_availability():
    """Get room availability"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BOOKING_SERVICE}/api/rooms/availability")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting room availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Booking service error: {str(e)}")

@app.post("/api/bookings")
async def create_booking(booking_request: BookingRequest):
    """Create a new booking"""
    try:
        # Calculate days
        check_in = datetime.strptime(booking_request.check_in, '%Y-%m-%d')
        check_out = datetime.strptime(booking_request.check_out, '%Y-%m-%d')
        days = (check_out - check_in).days

        if days < 1:
            raise HTTPException(status_code=400, detail="Invalid dates")

        # Calculate price
        async with httpx.AsyncClient(timeout=10.0) as client:
            price_response = await client.post(
                f"{ROOM_SERVICE}/api/pricing/calculate",
                json={
                    "room_type": booking_request.room_type,
                    "days": days,
                    "tariff": booking_request.tariff,
                    "extras": booking_request.extras
                }
            )
            price_response.raise_for_status()
            price_data = price_response.json()
            total_price = price_data['total_price'] * booking_request.quantity

            # Create booking
            booking_response = await client.post(
                f"{BOOKING_SERVICE}/api/bookings",
                json={
                    "hotel_id": booking_request.hotel_id,
                    "hotel_name": booking_request.hotel_name,
                    "check_in": booking_request.check_in,
                    "check_out": booking_request.check_out,
                    "room_type": booking_request.room_type,
                    "quantity": booking_request.quantity,
                    "tariff": booking_request.tariff,
                    "guest_name": booking_request.guest_name,
                    "guest_email": booking_request.guest_email,
                    "guest_phone": booking_request.guest_phone,
                    "total_price": total_price,
                    "extras": booking_request.extras
                }
            )
            booking_response.raise_for_status()
            booking_data = booking_response.json()

            # Send notification
            try:
                await client.post(
                    f"{NOTIFICATION_SERVICE}/api/notifications/send",
                    json={
                        "booking_id": booking_data['booking_ids'][0] if booking_data.get('booking_ids') else 'N/A',
                        "recipient_email": booking_request.guest_email,
                        "recipient_phone": booking_request.guest_phone,
                        "notification_type": "booking_confirmation",
                        "message": f"Бронирование подтверждено! Отель: {booking_request.hotel_name}, Номер: {booking_request.room_type}"
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {str(e)}")

            return {
                "success": True,
                "booking_data": booking_data,
                "price_data": price_data,
                "total_price": total_price
            }

    except httpx.HTTPError as e:
        logger.error(f"Error creating booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Booking error: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid date format")

@app.get("/api/bookings/{booking_id}")
async def get_booking(booking_id: str):
    """Get booking details"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{BOOKING_SERVICE}/api/bookings/{booking_id}")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Error getting booking: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Booking service error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

