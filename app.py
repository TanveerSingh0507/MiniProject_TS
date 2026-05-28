from flask import Flask, request, jsonify, render_template, session
import joblib
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__, 
            template_folder='../frontend/templates', 
            static_folder='../frontend/static')
app.secret_key = 'truthguard_super_secret_key'

# Base path for backend files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load the models
try:
    model = joblib.load(os.path.join(BASE_DIR, 'model.pkl'))
    vectorizer = joblib.load(os.path.join(BASE_DIR, 'vectorizer.pkl'))
except FileNotFoundError:
    model = None
    vectorizer = None

def init_db():
    conn = sqlite3.connect(os.path.join(BASE_DIR, 'truthguard.db'))
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, text_preview TEXT, prediction TEXT, confidence TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Initialize DB on script load
init_db()

def get_db_connection():
    conn = sqlite3.connect('truthguard.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if model is None or vectorizer is None:
        return jsonify({'error': 'Model not loaded. Please run train.py first.'}), 500

    data = request.json
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    # Transform the text
    vectorized_text = vectorizer.transform([text])
    
    # Predict
    prediction = model.predict(vectorized_text)[0]
    
    # Calculate confidence based on distance from the decision boundary
    decision_score = model.decision_function(vectorized_text)[0]
    # Map raw distance to a reasonable 70-98% confidence range for visualization
    # Most scores are between -5 and 5, so we scale it.
    confidence_val = int(min(98, 72 + abs(decision_score) * 4))
    confidence = f"{confidence_val}%"

    # Ensure we handle string or int labels. The new model outputs 'REAL' or 'FAKE'
    pred_str = str(prediction).upper()
    if pred_str == '1' or pred_str == 'REAL':
        result = "Real News"
    else:
        result = "Fake News"
    
    # Save to history if logged in
    # ...
    # (keeping the rest of the logic as is)
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            text_preview = text[:100] + ('...' if len(text) > 100 else '')
            conn.execute('INSERT INTO history (user_id, text_preview, prediction, confidence) VALUES (?, ?, ?, ?)', 
                         (session['user_id'], text_preview, result, confidence))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error saving history:", e)

    return jsonify({
        'prediction': result,
        'confidence': confidence
    })

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user is None:
            conn.close()
            return jsonify({'error': 'Incorrect email or password'}), 401
        else:
            # Verify password
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['email'] = user['email']
                conn.close()
                return jsonify({'message': 'Logged in successfully!', 'status': 'success'})
            else:
                conn.close()
                return jsonify({'error': 'Incorrect email or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            conn.close()
            return jsonify({'error': 'Email already registered'}), 400
            
        hashed_password = generate_password_hash(password)
        cursor = conn.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
        conn.commit()
        
        session['user_id'] = cursor.lastrowid
        session['email'] = email
        conn.close()
        return jsonify({'message': 'Account created successfully!', 'status': 'registered'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/me', methods=['GET'])
def me():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'email': session['email']})
    return jsonify({'logged_in': False})

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/history', methods=['GET'])
def history():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
        
    try:
        conn = get_db_connection()
        # Fetch latest 5 history entries for the user
        history_rows = conn.execute(
            'SELECT * FROM history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5', 
            (session['user_id'],)
        ).fetchall()
        conn.close()
        
        result = []
        for row in history_rows:
            result.append({
                'id': row['id'],
                'text_preview': row['text_preview'],
                'prediction': row['prediction'],
                'confidence': row['confidence'],
                'timestamp': row['timestamp']
            })
        return jsonify({'history': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/contact', methods=['POST'])
def contact():
    data = request.json
    email = data.get('email', 'Anonymous')
    message = data.get('message')
    
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400
        
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO contacts (email, message) VALUES (?, ?)', (email, message))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Message saved successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
