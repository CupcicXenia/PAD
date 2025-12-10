import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from copy import deepcopy
from flask import Flask, render_template, request, redirect, url_for, flash
from typing import List, Dict
import json

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Инициализация базы данных SQLite
def init_db():
    conn = sqlite3.connect('hotel_bookings.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id TEXT PRIMARY KEY, hotel_name TEXT, room_type TEXT, check_in TEXT, check_out TEXT, services TEXT, total_price REAL, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Паттерн Singleton: Менеджер бронирований
class BookingManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BookingManager, cls).__new__(cls)
            cls._instance.available_rooms = {
                'Standard': 10, 'Luxury': 5, 'Apartment': 3
            }
        return cls._instance

    def check_availability(self, room_type: str, quantity: int) -> bool:
        return self.available_rooms.get(room_type, 0) >= quantity

    def reserve_room(self, room_type: str, quantity: int) -> bool:
        if self.check_availability(room_type, quantity):
            self.available_rooms[room_type] -= quantity
            return True
        return False

    def release_room(self, room_type: str, quantity: int):
        self.available_rooms[room_type] = self.available_rooms.get(room_type, 0) + quantity

# Паттерн Factory Method: Создание номеров
class Room(ABC):
    @abstractmethod
    def get_description(self) -> str:
        pass

    @abstractmethod
    def get_base_price(self) -> float:
        pass

class StandardRoom(Room):
    def get_description(self) -> str:
        return "Стандартный номер: Уютный одноместный номер с базовыми удобствами"
    
    def get_base_price(self) -> float:
        return 100.0

class LuxuryRoom(Room):
    def get_description(self) -> str:
        return "Люкс: Просторный номер с премиум-удобствами"
    
    def get_base_price(self) -> float:
        return 250.0

class ApartmentRoom(Room):
    def get_description(self) -> str:
        return "Апартаменты: Полноценный номер с кухней и гостиной"
    
    def get_base_price(self) -> float:
        return 400.0

class RoomFactory:
    @staticmethod
    def create_room(room_type: str) -> Room:
        if room_type == "Standard":
            return StandardRoom()
        elif room_type == "Luxury":
            return LuxuryRoom()
        elif room_type == "Apartment":
            return ApartmentRoom()
        raise ValueError("Неизвестный тип номера")

# Паттерн Abstract Factory: Создание гостиничных комплексов
class HotelComplex(ABC):
    @abstractmethod
    def get_services(self) -> List[str]:
        pass

class CityHotel(HotelComplex):
    def get_services(self) -> List[str]:
        return ["Wi-Fi", "Тренажёрный зал"]

class ResortHotel(HotelComplex):
    def get_services(self) -> List[str]:
        return ["Wi-Fi", "Бассейн", "Спа"]

class HotelComplexFactory:
    @staticmethod
    def create_hotel(hotel_type: str) -> HotelComplex:
        if hotel_type == "City":
            return CityHotel()
        elif hotel_type == "Resort":
            return ResortHotel()
        raise ValueError("Неизвестный тип отеля")

# Паттерн Builder: Сборка пакета бронирования
class BookingPackage:
    def __init__(self):
        self.room = None
        self.services = []
        self.breakfast = False
        self.transfer = False

    def __str__(self) -> str:
        services = ", ".join(self.services)
        extras = []
        if self.breakfast:
            extras.append("Завтрак")
        if self.transfer:
            extras.append("Трансфер")
        extras_str = ", ".join(extras) if extras else "Отсутствуют"
        return f"Номер: {self.room.get_description()}, Услуги: {services}, Дополнительно: {extras_str}"

class BookingBuilder:
    def __init__(self):
        self.package = BookingPackage()

    def set_room(self, room: Room):
        self.package.room = room
        return self

    def set_hotel_services(self, hotel: HotelComplex):
        self.package.services = hotel.get_services()
        return self

    def add_breakfast(self):
        self.package.breakfast = True
        return self

    def add_transfer(self):
        self.package.transfer = True
        return self

    def build(self) -> BookingPackage:
        return self.package

# Паттерн Prototype: Клонирование бронирований
class BookingPrototype:
    def __init__(self, package: BookingPackage, check_in: str, check_out: str, price: float):
        self.package = package
        self.check_in = check_in
        self.check_out = check_out
        self.price = price
        self.id = str(uuid.uuid4())

    def clone(self) -> 'BookingPrototype':
        return deepcopy(self)

# Паттерн Adapter: Обработка платежей
class PaymentProcessor(ABC):
    @abstractmethod
    def process_payment(self, amount: float, currency: str) -> bool:
        pass

class USDProcessor:
    def pay(self, amount: float) -> bool:
        return True  # Имитация платежа

class EURProcessor:
    def execute_payment(self, amount: float) -> bool:
        return True  # Имитация платежа

class PaymentAdapter(PaymentProcessor):
    def __init__(self, processor):
        self.processor = processor

    def process_payment(self, amount: float, currency: str) -> bool:
        if currency == "USD":
            return self.processor.pay(amount)
        elif currency == "EUR":
            return self.processor.execute_payment(amount * 0.85)  # Простая конверсия
        return False

# Паттерн Observer: Уведомления о бронировании
class BookingObserver(ABC):
    @abstractmethod
    def update(self, booking_id: str, status: str):
        pass

class EmailNotifier(BookingObserver):
    def update(self, booking_id: str, status: str):
        flash(f"Email отправлен: Бронирование {booking_id} {status}")

class SMSNotifier(BookingObserver):
    def update(self, booking_id: str, status: str):
        flash(f"SMS отправлен: Бронирование {booking_id} {status}")

class BookingSubject:
    def __init__(self):
        self._observers: List[BookingObserver] = []

    def attach(self, observer: BookingObserver):
        self._observers.append(observer)

    def notify(self, booking_id: str, status: str):
        for observer in self._observers:
            observer.update(booking_id, status)

# Паттерн Strategy: Тарифные планы
class PricingStrategy(ABC):
    @abstractmethod
    def calculate_price(self, base_price: float, days: int) -> float:
        pass

class FlexibleTariff(PricingStrategy):
    def calculate_price(self, base_price: float, days: int) -> float:
        return base_price * days * 1.2  # 20% наценка за гибкость

class NonRefundableTariff(PricingStrategy):
    def calculate_price(self, base_price: float, days: int) -> float:
        return base_price * days * 0.9  # 10% скидка за невозвратность

# Паттерн Decorator: Дополнительные услуги
class BookingDecorator(ABC):
    def __init__(self, booking: BookingPrototype):
        self._booking = booking

    @property
    def package(self) -> BookingPackage:
        return self._booking.package

    @property
    def price(self) -> float:
        return self._booking.price

    # Добавляем setter для свойства price
    @price.setter
    def price(self, value: float):
        self._booking.price = value

    @property
    def id(self) -> str:
        return self._booking.id

class MiniBarDecorator(BookingDecorator):
    def __init__(self, booking: BookingPrototype):
        super().__init__(booking)
        self._booking.price += 50.0

class LateCheckoutDecorator(BookingDecorator):
    def __init__(self, booking: BookingPrototype):
        super().__init__(booking)
        self._booking.price += 30.0
        
# Маршруты Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    city = request.form['city']
    check_in = request.form['check_in']
    check_out = request.form['check_out']
    # Имитация поиска отелей по городу
    hotels = [
        {"name": f"Отель {city} Городской", "type": "City"},
        {"name": f"Отель {city} Курортный", "type": "Resort"}
    ]
    return render_template('hotels.html', hotels=hotels, check_in=check_in, check_out=check_out)

@app.route('/book/<hotel_type>/<hotel_name>', methods=['GET', 'POST'])
def book(hotel_type: str, hotel_name: str):
    check_in = request.args.get('check_in')
    check_out = request.args.get('check_out')
    room_types = ["Standard", "Luxury", "Apartment"]
    tariffs = ["Flexible", "NonRefundable"]

    if request.method == 'POST':
        room_type = request.form['room_type']
        tariff = request.form['tariff']
        currency = request.form['currency']
        add_minibar = 'minibar' in request.form
        add_late_checkout = 'late_checkout' in request.form
        add_breakfast = 'breakfast' in request.form
        add_transfer = 'transfer' in request.form
        group_size = int(request.form.get('group_size', 1))

        # Singleton: Проверка доступности
        booking_manager = BookingManager()
        if not booking_manager.reserve_room(room_type, group_size):
            flash("Выбранные номера недоступны!")
            return redirect(url_for('book', hotel_type=hotel_type, hotel_name=hotel_name, check_in=check_in, check_out=check_out))

        # Factory Method: Создание номера
        room = RoomFactory.create_room(room_type)

        # Abstract Factory: Создание услуг отеля
        hotel = HotelComplexFactory.create_hotel(hotel_type)

        # Builder: Сборка пакета бронирования
        builder = BookingBuilder()
        builder.set_room(room).set_hotel_services(hotel)
        if add_breakfast:
            builder.add_breakfast()
        if add_transfer:
            builder.add_transfer()
        package = builder.build()

        # Strategy: Расчёт стоимости
        days = (datetime.strptime(check_out, '%Y-%m-%d') - datetime.strptime(check_in, '%Y-%m-%d')).days
        strategy = FlexibleTariff() if tariff == "Flexible" else NonRefundableTariff()
        price = strategy.calculate_price(room.get_base_price(), days)

        # Prototype: Создание и клонирование бронирований
        base_booking = BookingPrototype(package, check_in, check_out, price)
        bookings = [base_booking.clone() for _ in range(group_size)]

        # Decorator: Добавление дополнительных услуг
        for i, booking in enumerate(bookings):
            if add_minibar:
                booking = MiniBarDecorator(booking)
            if add_late_checkout:
                booking = LateCheckoutDecorator(booking)
            bookings[i] = booking

        # Adapter: Обработка платежа
        processor = USDProcessor() if currency == "USD" else EURProcessor()
        payment_adapter = PaymentAdapter(processor)
        total_price = sum(b.price for b in bookings)
        if not payment_adapter.process_payment(total_price, currency):
            booking_manager.release_room(room_type, group_size)
            flash("Оплата не прошла!")
            return redirect(url_for('book', hotel_type=hotel_type, hotel_name=hotel_name, check_in=check_in, check_out=check_out))

        # Observer: Уведомление о подтверждении
        subject = BookingSubject()
        subject.attach(EmailNotifier())
        subject.attach(SMSNotifier())

        # Сохранение бронирований в базу данных
        conn = sqlite3.connect('hotel_bookings.db')
        c = conn.cursor()
        for booking in bookings:
            c.execute("INSERT INTO bookings (id, hotel_name, room_type, check_in, check_out, services, total_price, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (booking.id, hotel_name, room_type, check_in, check_out, str(booking.package), booking.price, "Подтверждено"))
            subject.notify(booking.id, "Подтверждено")
        conn.commit()
        conn.close()

        return redirect(url_for('confirmation', booking_ids=[b.id for b in bookings]))

    return render_template('book.html', hotel_name=hotel_name, hotel_type=hotel_type, check_in=check_in, check_out=check_out, room_types=room_types, tariffs=tariffs)

@app.route('/confirmation')
def confirmation():
    booking_ids = request.args.getlist('booking_ids')
    conn = sqlite3.connect('hotel_bookings.db')
    c = conn.cursor()
    bookings = []
    for bid in booking_ids:
        c.execute("SELECT * FROM bookings WHERE id = ?", (bid,))
        bookings.append(c.fetchone())
    conn.close()
    return render_template('confirmation.html', bookings=bookings)

if __name__ == '__main__':
    app.run(debug=True)