# Hotel Booking System - Microservices Architecture

Система бронирования отелей на основе микросервисной архитектуры с использованием Docker, Flask, FastAPI и PostgreSQL.

## 🏗️ Архитектура

Система состоит из 6 микросервисов:

1. **Frontend Service** (Flask, порт 5000) - Веб-интерфейс
2. **API Gateway** (FastAPI, порт 8000) - REST API маршрутизация
3. **Hotel Search Service** (Flask, порт 5001) - Поиск отелей (динамическая генерация)
4. **Booking Service** (Flask, порт 5002) - Управление бронированиями
5. **Room Service** (Flask, порт 5003) - Типы номеров, тарифы, доп. услуги
6. **Notification Service** (Flask, порт 5004) - Email/SMS уведомления

### Базы данных:
- **PostgreSQL** - 3 отдельные БД (booking_db, room_db, notification_db)
- **Redis** - Кэширование и сессии

## 🚀 Быстрый старт

### Требования:
- Docker Desktop
- Docker Compose

### Запуск:

```bash
# Клонировать репозиторий
git clone <your-repo-url>
cd booking_hotel

# Запустить все сервисы
docker-compose up -d

# Проверить статус
docker-compose ps
```

### Доступ:
- **Веб-интерфейс**: http://localhost:5000
- **API документация**: http://localhost:8000/docs
- **API Gateway**: http://localhost:8000

## 🧪 Тестирование

### Запуск unit тестов:

**Windows:**
```bash
run_tests.bat
```

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

### Запуск отдельного теста:
```bash
python services/hotel-search-service/test_app.py
```

## 📦 Структура проекта

```
booking_hotel/
├── services/
│   ├── frontend-service/          # Веб-интерфейс
│   ├── api-gateway-fastapi/       # API Gateway
│   ├── hotel-search-service/      # Поиск отелей
│   ├── booking-service/           # Бронирования
│   ├── room-service/              # Номера и тарифы
│   └── notification-service/      # Уведомления
├── docker-compose.yml             # Конфигурация Docker
├── .github/workflows/ci.yml       # GitHub Actions CI/CD
├── run_tests.bat                  # Скрипт тестов (Windows)
└── run_tests.sh                   # Скрипт тестов (Linux/Mac)
```

## 🔧 Управление

### Остановить все сервисы:
```bash
docker-compose down
```

### Пересобрать и перезапустить:
```bash
docker-compose up --build -d
```

### Посмотреть логи:
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f hotel-search-service
```

### Проверить базы данных:
```bash
docker exec hotel_postgres psql -U postgres -c "\l"
```

## 🛠️ Технологии

- **Backend**: Flask, FastAPI, Python 3.11
- **Database**: PostgreSQL, Redis
- **Containerization**: Docker, Docker Compose
- **Web Server**: Gunicorn, Uvicorn
- **Testing**: unittest, pytest
- **CI/CD**: GitHub Actions

## 📝 API Endpoints

### Hotel Search Service (5001)
- `GET /health` - Health check
- `POST /api/search` - Поиск отелей

### Booking Service (5002)
- `GET /health` - Health check
- `POST /api/bookings` - Создать бронирование
- `GET /api/bookings/{id}` - Получить бронирование

### Room Service (5003)
- `GET /health` - Health check
- `GET /api/room-types` - Типы номеров
- `GET /api/pricing-rules` - Тарифы
- `GET /api/extra-services` - Доп. услуги

### Notification Service (5004)
- `GET /health` - Health check
- `POST /api/notifications` - Отправить уведомление
- `GET /api/notifications/booking/{id}` - Уведомления по бронированию

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT License

