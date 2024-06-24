from flask import Flask, render_template, request, redirect, url_for, flash
from web3 import Web3
from web3.middleware import geth_poa_middleware
from contact_info import abi, contract_address
import re

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Инициализация подключения к Ethereum ноде
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = w3.eth.contract(address=contract_address, abi=abi)

# Функции проверки пароля и регистрации
def is_strong_password(password):
    if len(password) < 12:
        return False
    if re.search(r"password123|qwerty123", password):
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%]", password):
        return False
    return True

def auth(public_key, password):
    try:
        w3.geth.personal.unlock_account(public_key, password)
        return True
    except Exception as e:
        flash(f"Ошибка авторизации: {e}", "danger")
        return False

def registration(password):
    if not is_strong_password(password):
        flash("Пароль не соответствует требованиям. Попробуйте еще раз.", "danger")
        return None
    try:
        address = w3.geth.personal.new_account(password)
        flash(f"Адрес нового аккаунта: {address}", "success")
        return address
    except Exception as e:
        flash(f"Ошибка при создании аккаунта: {e}", "danger")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get('password')
        registration(password)
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        public_key = request.form.get('public_key')
        password = request.form.get('password')
        if auth(public_key, password):
            return redirect(url_for('dashboard', public_key=public_key))
    return render_template('login.html')

@app.route('/dashboard/<public_key>')
def dashboard(public_key):
    return render_template('dashboard.html', public_key=public_key)

# Добавляем функции для работы с контрактом
def create_estate(public_key, size, photo, rooms, estate_type):
    try:
        tx_hash = contract.functions.createEstate(size, photo, rooms, estate_type).transact({'from': public_key})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash(f"Недвижимость создана успешно. Хеш транзакции: {tx_hash.hex()}", "success")
    except Exception as e:
        flash(f"Ошибка при создании недвижимости: {e}", "danger")

def create_ad(public_key, estate_id, price):
    try:
        tx_hash = contract.functions.createAd(estate_id, price).transact({'from': public_key})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash(f"Объявление создано успешно. Хеш транзакции: {tx_hash.hex()}", "success")
    except Exception as e:
        flash(f"Ошибка при создании объявления: {e}", "danger")

def buy_estate(public_key, ad_id, price):
    try:
        tx_hash = contract.functions.buyEstate(ad_id).transact({'from': public_key, 'value': price})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash(f"Недвижимость успешно куплена. Хеш транзакции: {tx_hash.hex()}", "success")
    except Exception as e:
        flash(f"Ошибка при покупке недвижимости: {e}", "danger")

def withdraw_funds(public_key, amount):
    try:
        tx_hash = contract.functions.withdraw(amount).transact({'from': public_key})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash(f"Средства успешно выведены. Хеш транзакции: {tx_hash.hex()}", "success")
    except Exception as e:
        flash(f"Ошибка при выводе средств: {e}", "danger")

def change_estate_status(public_key, estate_id):
    try:
        tx_hash = contract.functions.updateEstate(estate_id, True).transact({'from': public_key})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash(f"Статус недвижимости успешно изменен. Хеш транзакции: {tx_hash.hex()}", "success")
    except Exception as e:
        flash(f"Ошибка при изменении статуса недвижимости: {e}", "danger")

def change_ad_status(public_key, ad_id):
    try:
        tx_hash = contract.functions.updateAd(ad_id, 1).transact({'from': public_key})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash(f"Статус объявления успешно изменен. Хеш транзакции: {tx_hash.hex()}", "success")
    except Exception as e:
        flash(f"Ошибка при изменении статуса объявления: {e}", "danger")


def get_estates():
    try:
        estates = contract.functions.getEstates().call()
        return estates
    except Exception as e:
        flash(f"Ошибка при получении информации о недвижимости: {e}", "danger")
        return []

def get_ads():
    try:
        ads = contract.functions.getAds().call()
        return ads
    except Exception as e:
        flash(f"Ошибка при получении информации о объявлениях: {e}", "danger")
        return []

def get_balance(public_key):
    try:
        balance = contract.functions.getBalance().call({'from': public_key})
        return balance
    except Exception as e:
        flash(f"Ошибка при получении баланса: {e}", "danger")
        return 0

@app.route('/create_estate', methods=['GET', 'POST'])
def create_estate_route():
    public_key = request.args.get('public_key')
    if request.method == 'POST':
        size = int(request.form.get('size'))
        photo = request.form.get('photo')
        rooms = int(request.form.get('rooms'))
        estate_type = request.form.get('estate_type')
        estate_type = {"Дом": 0, "Квартира": 1, "Мансарда": 2}.get(estate_type, 0)
        create_estate(public_key, size, photo, rooms, estate_type)
        return redirect(url_for('dashboard', public_key=public_key))
    return render_template('create_estate.html', public_key=public_key)

@app.route('/create_ad', methods=['GET', 'POST'])
def create_ad_route():
    public_key = request.args.get('public_key')
    if request.method == 'POST':
        estate_id = int(request.form.get('estate_id'))
        price = int(request.form.get('price'))
        create_ad(public_key, estate_id, price)
        return redirect(url_for('dashboard', public_key=public_key))
    return render_template('create_ad.html', public_key=public_key)

@app.route('/buy_estate', methods=['GET', 'POST'])
def buy_estate_route():
    public_key = request.args.get('public_key')
    if request.method == 'POST':
        ad_id = int(request.form.get('ad_id'))
        price = int(request.form.get('price'))
        buy_estate(public_key, ad_id, price)
        return redirect(url_for('dashboard', public_key=public_key))
    return render_template('buy_estate.html', public_key=public_key)

@app.route('/withdraw_funds', methods=['GET', 'POST'])
def withdraw_funds_route():
    public_key = request.args.get('public_key')
    if request.method == 'POST':
        amount = int(request.form.get('amount'))
        withdraw_funds(public_key, amount)
        return redirect(url_for('dashboard', public_key=public_key))
    return render_template('withdraw_funds.html', public_key=public_key)

@app.route('/change_estate_status', methods=['GET', 'POST'])
def change_estate_status_route():
    public_key = request.args.get('public_key')
    if request.method == 'POST':
        estate_id = int(request.form.get('estate_id'))
        change_estate_status(public_key, estate_id)
        return redirect(url_for('dashboard', public_key=public_key))
    return render_template('change_estate_status.html', public_key=public_key)

@app.route('/change_ad_status', methods=['GET', 'POST'])
def change_ad_status_route():
    public_key = request.args.get('public_key')
    if request.method == 'POST':
        ad_id = int(request.form.get('ad_id'))
        change_ad_status(public_key, ad_id)
        return redirect(url_for('dashboard', public_key=public_key))
    return render_template('change_ad_status.html', public_key=public_key)

@app.route('/get_estates')
def get_estates_route():
    estates = get_estates()
    return render_template('estates.html', estates=estates)

@app.route('/get_ads')
def get_ads_route():
    ads = get_ads()
    return render_template('ads.html', ads=ads)

@app.route('/get_balance/<public_key>')
def get_balance_route(public_key):
    balance = get_balance(public_key)
    return render_template('balance.html', balance=balance)

if __name__ == "__main__":
    app.run(debug=True)
