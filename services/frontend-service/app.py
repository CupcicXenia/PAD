from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import os
import logging
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'supersecretkey')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Gateway URL
API_GATEWAY = os.getenv('API_GATEWAY', 'http://api-gateway:8000')

@app.route('/')
def index():
    """Main page with search form"""
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Search hotels"""
    city = request.form.get('city')
    check_in = request.form.get('check_in')
    check_out = request.form.get('check_out')
    
    if not all([city, check_in, check_out]):
        flash('Пожалуйста, заполните все поля!')
        return redirect(url_for('index'))
    
    try:
        # Validate dates
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        
        if check_out_date <= check_in_date:
            flash('Дата выезда должна быть позже даты заезда!')
            return redirect(url_for('index'))
        
        # Search hotels via API Gateway
        response = requests.post(
            f'{API_GATEWAY}/api/search',
            json={
                'city': city,
                'check_in': check_in,
                'check_out': check_out
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            hotels = data.get('hotels', [])
            
            if not hotels:
                flash(f'Отели в городе {city} не найдены!')
                return redirect(url_for('index'))
            
            return render_template('hotels.html', 
                                 hotels=hotels, 
                                 city=city,
                                 check_in=check_in,
                                 check_out=check_out)
        else:
            flash('Ошибка при поиске отелей!')
            return redirect(url_for('index'))
            
    except ValueError:
        flash('Неверный формат даты!')
        return redirect(url_for('index'))
    except requests.RequestException as e:
        logger.error(f"Error searching hotels: {str(e)}")
        flash('Ошибка соединения с сервером!')
        return redirect(url_for('index'))

@app.route('/book/<int:hotel_id>/<hotel_name>')
def book(hotel_id, hotel_name):
    """Booking form"""
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    hotel_type = request.args.get('hotel_type', 'Отель')
    
    if not check_in or not check_out:
        flash('Отсутствуют даты бронирования!')
        return redirect(url_for('index'))
    
    try:
        # Get room types
        rooms_response = requests.get(f'{API_GATEWAY}/api/rooms/types', timeout=10)
        rooms_data = rooms_response.json()
        room_types = rooms_data.get('room_types', [])
        
        # Get tariffs
        tariffs_response = requests.get(f'{API_GATEWAY}/api/pricing/tariffs', timeout=10)
        tariffs_data = tariffs_response.json()
        tariffs = tariffs_data.get('tariffs', [])
        
        # Get extra services
        extras_response = requests.get(f'{API_GATEWAY}/api/services/extra', timeout=10)
        extras_data = extras_response.json()
        extra_services = extras_data.get('extra_services', [])
        
        # Calculate days
        check_in_date = datetime.strptime(check_in, '%Y-%m-%d')
        check_out_date = datetime.strptime(check_out, '%Y-%m-%d')
        days = (check_out_date - check_in_date).days
        
        return render_template('book.html',
                             hotel_id=hotel_id,
                             hotel_name=hotel_name,
                             hotel_type=hotel_type,
                             check_in=check_in,
                             check_out=check_out,
                             days=days,
                             room_types=room_types,
                             tariffs=tariffs,
                             extra_services=extra_services)
        
    except requests.RequestException as e:
        logger.error(f"Error loading booking form: {str(e)}")
        flash('Ошибка загрузки формы бронирования!')
        return redirect(url_for('index'))

@app.route('/confirmation', methods=['POST'])
def confirmation():
    """Process booking and show confirmation"""
    try:
        # Get form data
        hotel_id = int(request.form.get('hotel_id'))
        hotel_name = request.form.get('hotel_name')
        check_in = request.form.get('check_in')
        check_out = request.form.get('check_out')
        room_type = request.form.get('room_type')
        quantity = int(request.form.get('quantity', 1))
        tariff = request.form.get('tariff')
        guest_name = request.form.get('guest_name')
        guest_email = request.form.get('guest_email')
        guest_phone = request.form.get('guest_phone')
        
        # Get extras
        extras = []
        if request.form.get('minibar'):
            extras.append('minibar')
        if request.form.get('late_checkout'):
            extras.append('late_checkout')
        if request.form.get('breakfast'):
            extras.append('breakfast')
        if request.form.get('transfer'):
            extras.append('transfer')

        # Validate required fields
        if not all([hotel_id, hotel_name, check_in, check_out, room_type, guest_name, guest_email]):
            flash('Пожалуйста, заполните все обязательные поля!')
            return redirect(url_for('book', hotel_id=hotel_id, hotel_name=hotel_name,
                                  check_in=check_in, check_out=check_out))

        # Create booking via API Gateway
        response = requests.post(
            f'{API_GATEWAY}/api/bookings',
            json={
                'hotel_id': hotel_id,
                'hotel_name': hotel_name,
                'check_in': check_in,
                'check_out': check_out,
                'room_type': room_type,
                'quantity': quantity,
                'tariff': tariff,
                'guest_name': guest_name,
                'guest_email': guest_email,
                'guest_phone': guest_phone,
                'extras': extras
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()

            # Store booking info in session
            session['booking_result'] = result

            return render_template('confirmation.html',
                                 hotel_name=hotel_name,
                                 check_in=check_in,
                                 check_out=check_out,
                                 room_type=room_type,
                                 quantity=quantity,
                                 tariff=tariff,
                                 guest_name=guest_name,
                                 guest_email=guest_email,
                                 total_price=result.get('total_price'),
                                 booking_data=result.get('booking_data'),
                                 price_data=result.get('price_data'))
        else:
            flash('Ошибка при создании бронирования!')
            return redirect(url_for('book', hotel_id=hotel_id, hotel_name=hotel_name,
                                  check_in=check_in, check_out=check_out))

    except requests.RequestException as e:
        logger.error(f"Error creating booking: {str(e)}")
        flash('Ошибка соединения с сервером!')
        return redirect(url_for('index'))
    except ValueError as e:
        logger.error(f"Invalid form data: {str(e)}")
        flash('Неверные данные формы!')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

