from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dateutil.relativedelta import relativedelta


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///subscriptions.db' 
db = SQLAlchemy(app)

# Модель подписки
class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(10), nullable=False) 
    start_date = db.Column(db.String(20), nullable=False) 
    next_charge = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'amount': self.amount,
            'frequency': self.frequency,
            'start_date': self.start_date,
            'next_charge': self.next_charge
        }


with app.app_context():
    db.create_all()


def calculate_next_charge(start_date, frequency):
    # Парсим start_date
    date_obj = datetime.strptime(start_date, '%d %m %Y')
        
    # Добавляем период в зависимости от frequency
    if frequency == 'monthly':
        next_date = date_obj + relativedelta(months=1)
    elif frequency == 'yearly':
        next_date = date_obj + relativedelta(years=1)
   
    # Возвращаем в строковом формате
    return next_date.strftime('%d %m %Y')
    
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/subscriptions', methods=['GET','POST'])
def create_subscription():
    if request.method == 'GET':
        subscriptions = Subscription.query.all()
        return jsonify([sub.to_dict() for sub in subscriptions]), 200

    if request.method == 'POST':
        data = request.get_json()
        required = {'name', 'amount', 'frequency', 'start_date'}
        missing = required - set(data.keys())
        if missing:
            return jsonify({"error": f'Отсутствуют поля: {list(missing)}'}), 400
        
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({"error":"Неверная стоимость"}), 400
        
        start_date = data.get('start_date')
        frequency = data['frequency']
        if frequency not in ['monthly', 'yearly']:
            return jsonify({"error":"Частота должна быть ежемесячной или ежегодной"}), 400
        
        next_charge = calculate_next_charge(start_date, frequency)
        if next_charge is None:
            return jsonify({"error":"Неверная начальная дата или частота"}), 400
        
        subscription = Subscription(
            name=data['name'],
            amount=amount,
            frequency=frequency,
            start_date=data['start_date'],
            next_charge=next_charge
        )

        db.session.add(subscription)
        db.session.commit()
        return jsonify(subscription.to_dict()), 201  

@app.route('/subscriptions/<int:sub_id>', methods=['PUT'])
def update_subscription(sub_id):
    data = request.get_json()
    sub = db.session.get(Subscription, sub_id)
    if not sub:
        return jsonify({"error":"Подписка не найдена"}), 404
    
    if 'name' in data:
            sub.name = data['name']
    
    if 'amount' in data:
        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({"error":"Неверная стоимость"}), 400
        sub.amount = float(data['amount'])
    
    if 'frequency' in data:
        if data['frequency'] not in ['monthly', 'yearly']:
            return jsonify({"error":"Периодичность должна быть ежемесячной или ежегодной"}), 400
        sub.frequency = data['frequency']
        sub.next_charge = calculate_next_charge(sub.start_date, sub.frequency)
        
        if 'next_charge' in data:
            datetime.strptime(data['next_charge'], '%d %m %Y')
            sub.next_charge = data['next_charge']

    db.session.commit()
    return jsonify(sub.to_dict()), 200

@app.route('/subscriptions/<int:sub_id>', methods=['DELETE'])
def delete_subscription(sub_id):
    sub = db.session.get(Subscription, sub_id)
    if not sub:
        return jsonify({"error":"Подписка не найдена"}), 404
    db.session.delete(sub)
    db.session.commit()
    return jsonify({'message': 'Подписка удалена'}), 200

if __name__ == '__main__':
    app.run(debug=True)
