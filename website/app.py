from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a secure value

ACCOUNTS_FILE = 'accounts.json'

# Load accounts from JSON
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save accounts to JSON
def save_accounts(accounts):
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump(accounts, f, indent=4)

@app.route('/')
def home():
    return redirect(url_for('login'))

# =============================
# Register
# =============================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        accounts = load_accounts()
        if username in accounts:
            flash('Username already exists.')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        accounts[username] = {
            'password': hashed_pw,
            'balance': 0,
            'transactions': []
        }

        save_accounts(accounts)
        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# =============================
# Login
# =============================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        accounts = load_accounts()

        if username in accounts and check_password_hash(accounts[username]['password'], password):
            session['user'] = username
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.')
        return redirect(url_for('login'))

    return render_template('login.html')

# =============================
# Dashboard
# =============================
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    accounts = load_accounts()
    balance = accounts[username]['balance']
    return render_template('dashboard.html', username=username, balance=balance)

# =============================
# Deposit
# =============================
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    accounts = load_accounts()

    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0:
            flash('Invalid deposit amount.')
            return redirect(url_for('deposit'))

        accounts[username]['balance'] += amount
        accounts[username]['transactions'].append(f"[{datetime.now()}] Deposited ${amount:.2f}")
        save_accounts(accounts)
        flash('Deposit successful.')
        return redirect(url_for('dashboard'))

    return '''
    <h2>Deposit</h2>
    <form method="POST">
        Amount: <input type="number" step="0.01" name="amount" required>
        <button type="submit">Deposit</button>
    </form>
    <a href="/dashboard">Back to Dashboard</a>
    '''

# =============================
# Withdraw
# =============================
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    accounts = load_accounts()

    if request.method == 'POST':
        amount = float(request.form['amount'])
        if amount <= 0 or amount > accounts[username]['balance']:
            flash('Invalid withdrawal amount.')
            return redirect(url_for('withdraw'))

        accounts[username]['balance'] -= amount
        accounts[username]['transactions'].append(f"[{datetime.now()}] Withdrew ${amount:.2f}")
        save_accounts(accounts)
        flash('Withdrawal successful.')
        return redirect(url_for('dashboard'))

    return '''
    <h2>Withdraw</h2>
    <form method="POST">
        Amount: <input type="number" step="0.01" name="amount" required>
        <button type="submit">Withdraw</button>
    </form>
    <a href="/dashboard">Back to Dashboard</a>
    '''

# =============================
# View Statements
# =============================
@app.route('/statements')
def statements():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    accounts = load_accounts()
    user_statements = accounts[username]['transactions']
    return render_template('statements.html', statements=user_statements)

# =============================
# Admin: View All Balances
# =============================
@app.route('/view-all-balances')
def view_all_balances():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    accounts = load_accounts()
    return '<br>'.join([f'{user}: ${info["balance"]:.2f}' for user, info in accounts.items()])

# =============================
# Admin: View All Statements
# =============================
@app.route('/view-statements')
def view_all_statements():
    if 'user' not in session or session['user'] != 'admin':
        return redirect(url_for('login'))

    accounts = load_accounts()
    output = ''
    for user, info in accounts.items():
        output += f'<h3>{user}</h3>'
        output += '<ul>'
        for txn in info['transactions']:
            output += f'<li>{txn}</li>'
        output += '</ul>'
    return output + '<br><a href="/dashboard">Back to Dashboard</a>'

# =============================
# Logout
# =============================
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))

# =============================
# Run App
# =============================
if __name__ == '__main__':
    app.run(debug=True)
