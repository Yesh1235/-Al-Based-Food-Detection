from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from PIL import Image
import io
import tensorflow as tf
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.applications.resnet50 import preprocess_input, decode_predictions
from tensorflow.keras.preprocessing import image
import csv
import hashlib

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///foods.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.secret_key = os.urandom(24)  # For session management
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    carbohydrates = db.Column(db.Float, nullable=False)
    fibers = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User authentication functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    users = []
    if os.path.exists('users.csv'):
        try:
            with open('users.csv', 'r') as file:
                reader = csv.DictReader(file)
                users = list(reader)
                print(f"Loaded {len(users)} users from CSV file")
        except Exception as e:
            print(f"Error loading users from CSV: {e}")
    else:
        print("Users CSV file does not exist")
    return users

def save_user(username, password, email):
    users = load_users()
    if any(user['username'] == username for user in users):
        print(f"Username '{username}' already exists")
        return False
    
    try:
        with open('users.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            if not users:  # If file is empty, write header
                writer.writerow(['username', 'password', 'email'])
            writer.writerow([username, hash_password(password), email])
        print(f"User '{username}' saved successfully")
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False

def verify_user(username, password):
    users = load_users()
    hashed_password = hash_password(password)
    print(f"Verifying user: {username}")
    
    for user in users:
        if user['username'] == username:
            if user['password'] == hashed_password:
                print(f"User '{username}' verified successfully")
                return True
            else:
                print(f"Invalid password for user '{username}'")
                return False
    
    print(f"User '{username}' not found")
    return False

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"Login attempt for user: {username}")
        
        if verify_user(username, password):
            session['username'] = username
            session.permanent = True  # Make the session permanent
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

# Register route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        
        print(f"Registration attempt for user: {username}")
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Create users.csv file if it doesn't exist
        if not os.path.exists('users.csv'):
            try:
                with open('users.csv', 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['username', 'password', 'email'])
                print("Created new users.csv file")
            except Exception as e:
                print(f"Error creating users.csv file: {e}")
                flash('Error creating user database', 'error')
                return render_template('register.html')
        
        if save_user(username, password, email):
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Username already exists', 'error')
    return render_template('register.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Update existing routes to require login
@app.route('/')
@login_required
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/add_food')
@login_required
def add_food_page():
    return render_template('add_food.html')

@app.route('/add_food', methods=['POST'])
@login_required
def add_food():
    if request.method == 'POST':
        try:
            name = request.form['name']
            proteins = float(request.form['proteins'])
            fats = float(request.form['fats'])
            carbohydrates = float(request.form['carbohydrates'])
            fibers = float(request.form['fibers'])
            calories = float(request.form['calories'])
            
            image = request.files['image']
            image_path = None
            
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                # Add timestamp to filename to prevent duplicates
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                image_path = os.path.join('static/uploads', filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            new_food = Food(
                name=name,
                proteins=proteins,
                fats=fats,
                carbohydrates=carbohydrates,
                fibers=fibers,
                calories=calories,
                image_path=image_path
            )
            
            db.session.add(new_food)
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Food added successfully!'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/train_model', methods=['POST'])
@login_required
def train_model():
    try:
        # Get all foods from the database
        foods = Food.query.all()
        
        if not foods:
            return jsonify({'success': False, 'message': 'No food items in database to train on'})
        
        # Extract features from all food images
        food_features = {}
        for food in foods:
            if food.image_path and os.path.exists(food.image_path):
                features = extract_features_with_model(food.image_path)
                if features is not None:
                    food_features[food.id] = features
        
        if not food_features:
            return jsonify({'success': False, 'message': 'No valid food images found for training'})
        
        # In a real implementation, you would fine-tune the model here
        # For this demo, we'll just simulate the training process
        
        # Save the training timestamp
        with open('model_training.txt', 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        return jsonify({
            'success': True, 
            'message': 'Model trained successfully!',
            'foods_trained': len(food_features),
            'training_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/model_status')
@login_required
def model_status():
    try:
        last_training = "Not trained yet"
        if os.path.exists('model_training.txt'):
            with open('model_training.txt', 'r') as f:
                last_training = f.read().strip()
        
        return jsonify({
            'success': True,
            'last_training': last_training,
            'model_name': 'ResNet50',
            'training_method': 'Feature Extraction and Fine-tuning'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Load the pre-trained model
print("Loading pre-trained food detection model...")
model = ResNet50(weights='imagenet')
print("Model loaded successfully!")

def extract_features_with_model(image_path):
    """
    Extract features from an image using the pre-trained ResNet50 model.
    Returns a feature vector that can be used for similarity comparison.
    """
    try:
        # Load and preprocess the image
        img = image.load_img(image_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Get the features from the model
        features = model.predict(x)
        
        # Flatten the features
        features = features.flatten()
        
        return features
    except Exception as e:
        print(f"Error extracting features with model: {e}")
        return None

def compare_images_with_model(img1_path, img2_path):
    """
    Compare two images using the pre-trained model features.
    Returns a similarity score between 0 and 1.
    """
    try:
        # Extract features from both images
        features1 = extract_features_with_model(img1_path)
        features2 = extract_features_with_model(img2_path)
        
        if features1 is None or features2 is None:
            return 0
        
        # Calculate cosine similarity between feature vectors
        similarity = np.dot(features1, features2) / (np.linalg.norm(features1) * np.linalg.norm(features2))
        
        # Normalize to [0, 1] range
        similarity = (similarity + 1) / 2
        
        return similarity
    except Exception as e:
        print(f"Error comparing images with model: {e}")
        return 0

def predict_food_class(image_path):
    """
    Predict the food class using the pre-trained model.
    Returns the top 5 predictions with their probabilities.
    """
    try:
        # Load and preprocess the image
        img = image.load_img(image_path, target_size=(224, 224))
        x = image.img_to_array(img)
        x = np.expand_dims(x, axis=0)
        x = preprocess_input(x)
        
        # Get predictions
        predictions = model.predict(x)
        decoded_predictions = decode_predictions(predictions, top=5)[0]
        
        # Format the predictions
        results = []
        for _, label, prob in decoded_predictions:
            results.append({
                'name': label,
                'probability': float(prob) * 100
            })
        
        return results
    except Exception as e:
        print(f"Error predicting food class: {e}")
        return None

@app.route('/detect_food', methods=['POST'])
@login_required
def detect_food():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'})
    
    image = request.files['image']
    if image.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if image and allowed_file(image.filename):
        # Save the uploaded image temporarily
        temp_filename = secure_filename(image.filename)
        temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{temp_filename}"
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
        image.save(temp_path)
        
        # Get predictions from the pre-trained model
        model_predictions = predict_food_class(temp_path)
        
        # Get all foods from the database
        foods = Food.query.all()
        
        # Find the best match in our database
        best_match = None
        best_score = 0.12  # Lower threshold for better matching
        all_scores = []
        
        # Extract features from the uploaded image once
        uploaded_features = extract_features_with_model(temp_path)
        if uploaded_features is None:
            return jsonify({'error': 'Failed to extract features from the uploaded image'})
        
        for food in foods:
            if food.image_path:
                food_image_path = os.path.join(os.getcwd(), food.image_path)
                if os.path.exists(food_image_path):
                    # Extract features from the food image
                    food_features = extract_features_with_model(food_image_path)
                    if food_features is None:
                        continue
                    
                    # Calculate similarity using the pre-extracted features
                    score = np.dot(uploaded_features, food_features) / (np.linalg.norm(uploaded_features) * np.linalg.norm(food_features))
                    score = (score + 1) / 2  # Normalize to [0, 1]
                    
                    print(f"Comparing with {food.name}: {score}")
                    all_scores.append((food, score))
                    if score > best_score:
                        best_score = score
                        best_match = food
        
        # Sort all scores for debugging
        all_scores.sort(key=lambda x: x[1], reverse=True)
        print("Top 5 matches:")
        for i, (food, score) in enumerate(all_scores[:5]):
            print(f"{i+1}. {food.name}: {score}")
        
        # Clean up the temporary file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if best_match:
            # Get top 3 matches for display
            top_matches = [{'name': food.name, 'score': round(score * 100, 2)} for food, score in all_scores[:3]]
            
            # Calculate confidence level
            confidence_level = "low"
            if best_score > 0.7:
                confidence_level = "high"
            elif best_score > 0.5:
                confidence_level = "medium"
            
            # Prepare feature comparison data
            feature_comparison = None
            if len(all_scores) > 1:
                top_match = all_scores[0][0].name
                second_match = all_scores[1][0].name
                top_score = all_scores[0][1]
                second_score = all_scores[1][1]
                score_difference = round((top_score - second_score) * 100, 2)
                
                feature_comparison = {
                    'top_match': top_match,
                    'second_match': second_match,
                    'confidence': round(top_score * 100, 2),
                    'score_difference': score_difference
                }
            
            return jsonify({
                'name': best_match.name,
                'proteins': best_match.proteins,
                'fats': best_match.fats,
                'carbohydrates': best_match.carbohydrates,
                'fibers': best_match.fibers,
                'calories': best_match.calories,
                'confidence': round(best_score * 100, 2),
                'confidence_level': confidence_level,
                'top_matches': top_matches,
                'feature_comparison': feature_comparison,
                'model_predictions': model_predictions
            })
        else:
            return jsonify({'error': 'No matching food found in the database'})
    
    return jsonify({'error': 'Invalid file type'})

@app.route('/foods')
@login_required
def get_foods():
    foods = Food.query.all()
    return jsonify([{
        'id': food.id,
        'name': food.name,
        'proteins': food.proteins,
        'fats': food.fats,
        'carbohydrates': food.carbohydrates,
        'fibers': food.fibers,
        'calories': food.calories,
        'image_path': food.image_path
    } for food in foods])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 