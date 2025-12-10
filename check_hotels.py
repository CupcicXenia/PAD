import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'hotel_search_db',
    'user': 'postgres',
    'password': 'postgres',
    'port': '5432'
}

try:
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    # Check if hotels table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'hotels'
        )
    """)
    table_exists = cur.fetchone()['exists']
    
    if table_exists:
        print("✓ Таблица hotels существует")
        
        # Count hotels
        cur.execute('SELECT COUNT(*) as count FROM hotels')
        count = cur.fetchone()['count']
        print(f"✓ Количество отелей в базе: {count}")
        
        # Show all hotels
        cur.execute('SELECT id, name, city, hotel_type, rating FROM hotels ORDER BY city, name')
        hotels = cur.fetchall()
        
        if hotels:
            print("\n=== СПИСОК ОТЕЛЕЙ В БАЗЕ ДАННЫХ ===")
            for hotel in hotels:
                print(f"ID: {hotel['id']}, Название: {hotel['name']}, Город: {hotel['city']}, Тип: {hotel['hotel_type']}, Рейтинг: {hotel['rating']}")
        else:
            print("\n✗ ОТЕЛЕЙ В БАЗЕ НЕТ!")
    else:
        print("✗ Таблица hotels НЕ существует!")
    
    cur.close()
    conn.close()
    
except psycopg2.OperationalError as e:
    print(f"✗ Ошибка подключения к базе данных: {e}")
    print("\nВозможные причины:")
    print("1. PostgreSQL не запущен")
    print("2. База данных hotel_search_db не создана")
    print("3. Неверные учетные данные")
except Exception as e:
    print(f"✗ Ошибка: {e}")

