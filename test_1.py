import pytest
from app import app, db

#создание таблицы
@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all() 
        yield client
        with app.app_context():
            db.drop_all()  # Очищаем после тестов

#тест создание новой подписки
def test_create_subscription_success(client):
    data = {
        "name": "Netflix",
        "amount": 10.99,
        "frequency": "monthly",
        "start_date": "11 10 2025"
    }
    response = client.post('/subscriptions', json=data)
    assert response.status_code == 201
    json_data = response.get_json()
    
    assert 'id' in json_data
    assert json_data['name'] == 'Netflix'
    assert json_data['amount'] == 10.99
    assert json_data['frequency'] == 'monthly'
    assert json_data['next_charge'] == '11 11 2025'

#тест ошибки с неполными данными
def test_create_subscription_missing_fields(client):
    data = {"name": "Netflix"}  # Недостаточно полей
    response = client.post('/subscriptions', json=data)
    assert response.status_code == 400
    assert "Отсутствуют" in str(response.get_json())  # Проверяем сообщение об ошибке

#тест ошибки с неверной частотой подписки
def test_create_subscription_invalid_frequency(client):
    data = {
        "name": "Netflix",
        "amount": 10.99,
        "frequency": "daily",  # Неверная частота
        "start_date": "11 10 2025"
    }
    response = client.post('/subscriptions', json=data)
    assert response.status_code == 400
    assert "Частота" in str(response.get_json())  # Проверяем сообщение об ошибке

#тест получение пустого списка подписок
def test_get_subscriptions_empty(client):
    response = client.get('/subscriptions')
    assert response.status_code == 200
    assert response.get_json() == []  # Пустой список

#тест получение списка подписок после создания одной
def test_get_subscriptions(client):
    # Сначала создадим подписку
    data = {
        "name": "Spotify",
        "amount": 5.99,
        "frequency": "monthly",
        "start_date": "14 11 2025"
    }
    client.post('/subscriptions', json=data)
    response = client.get('/subscriptions')
    assert response.status_code == 200
    subs = response.get_json()
    assert len(subs) == 1
    assert subs[0]['name'] == 'Spotify'
    assert subs[0]['next_charge'] == '14 12 2025'

#тест успешного обновления существующей подписки
def test_update_subscription_success(client):
    # Создаём подписку
    data = {
        "name": "Netflix",
        "amount": 10.99,
        "frequency": "monthly",
        "start_date": "14 11 2025"
    }
    create_response = client.post('/subscriptions', json=data)
    sub_id = create_response.get_json()['id']
    
    # Обновляем
    update_data = {"amount": 15.99, "next_charge": "14 12 2025"}
    response = client.put(f'/subscriptions/{sub_id}', json=update_data)
    assert response.status_code == 200
    updated = response.get_json()
    assert updated['amount'] == 15.99
    assert updated['next_charge'] == '14 12 2025'  # Проверяем обновление next_charge

#тест обновления подписки с неверной частотой списания
def test_update_subscription_invalid_frequency(client):
    # Создаём подписку
    data = {
        "name": "Netflix",
        "amount": 10.99,
        "frequency": "monthly",
        "start_date": "13 11 2025"
    }
    create_response = client.post('/subscriptions', json=data)
    sub_id = create_response.get_json()['id']
    
    # Пытаемся обновить на неверную частоту
    update_data = {"frequency": "daily"}
    response = client.put(f'/subscriptions/{sub_id}', json=update_data)
    assert response.status_code == 400
    assert "Периодичность" in str(response.get_json())

#тест успешного удаления подписки
def test_update_subscription_not_found(client):
    update_data = {"amount": 15.99}
    response = client.put('/subscriptions/999', json=update_data)  # Несуществующий ID
    assert response.status_code == 404
    assert "не найдена" in str(response.get_json())

#тест удаление несуществующей подписки
def test_delete_subscription_success(client):
    # Создаём подписку
    data = {
        "name": "Netflix",
        "amount": 10.99,
        "frequency": "monthly",
        "start_date": "14 11 2025"
    }
    create_response = client.post('/subscriptions', json=data)
    sub_id = create_response.get_json()['id']
    
    # Удаляем
    response = client.delete(f'/subscriptions/{sub_id}')
    assert response.status_code == 200
    assert 'message' in response.get_json()
    
    # Проверяем, что удалена
    get_response = client.get('/subscriptions')
    assert len(get_response.get_json()) == 0

def test_delete_subscription_not_found(client):
    response = client.delete('/subscriptions/999')  # Несуществующий ID
    assert response.status_code == 404
    assert "не найдена" in str(response.get_json())
