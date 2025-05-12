from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from models import User, ReadBook, UserPreference
from database import db
import pandas as pd
import os

# Create instance directory if it doesn't exist
instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "data.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()

# Load books from CSV
def load_books(query=None):
    try:
        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.csv')
        print(f"Loading books from: {csv_path}")
        books_df = pd.read_csv(csv_path)
        print(f"Total books loaded: {len(books_df)}")
        
        if query:
            query = query.lower()
            print(f"Searching for query: {query}")
            # Convert columns to string and handle NaN values
            books_df['title'] = books_df['title'].fillna('').astype(str)
            books_df['authors'] = books_df['authors'].fillna('').astype(str)
            books_df['category'] = books_df['category'].fillna('').astype(str)
            
            mask = (
                books_df['title'].str.lower().str.contains(query, na=False) |
                books_df['authors'].str.lower().str.contains(query, na=False) |
                books_df['category'].str.lower().str.contains(query, na=False)
            )
            filtered_df = books_df[mask]
            print(f"Found {len(filtered_df)} matches")
            return filtered_df
        return books_df
    except Exception as e:
        print(f"Error loading books: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def get_recommendations(user_id, num_recommendations=6):
    try:
        # Get user's preferences
        user_preferences = UserPreference.query.filter_by(user_id=user_id).all()
        preferred_categories = [pref.category for pref in user_preferences]
        
        # Get user's completed books to exclude them
        completed_books = {book.book_title for book in ReadBook.query.filter_by(user_id=user_id, status='read').all()}
        
        # Load all books
        books_df = load_books()
        if books_df.empty:
            return []
            
        # Convert categories to string and handle NaN
        books_df['category'] = books_df['category'].fillna('').astype(str)
        
        # Initialize scores for all books
        books_df['score'] = 0.0
        
        # Score based on categories
        for category in preferred_categories:
            category_mask = books_df['category'].str.lower().str.contains(category.lower(), na=False)
            books_df.loc[category_mask, 'score'] += 1.0
            
        # Get high-rated books in preferred categories
        books_df.loc[books_df['average_rating'].notna(), 'score'] += books_df['average_rating'].fillna(0) * 0.2
        
        # Exclude completed books
        books_df = books_df[~books_df['title'].isin(completed_books)]
        
        # Sort by score and get top recommendations
        recommended_books = books_df.nlargest(num_recommendations, 'score')
        
        # Convert to list of dictionaries
        recommendations = []
        for _, book in recommended_books.iterrows():
            if book['score'] > 0:  # Only include books with positive scores
                recommendations.append({
                    'title': str(book['title']),
                    'author': str(book['authors']),
                    'category': str(book['category']),
                    'published_year': str(book['published_year']) if pd.notna(book['published_year']) else '',
                    'average_rating': str(book['average_rating']) if pd.notna(book['average_rating']) else '',
                    'description': str(book['description']) if pd.notna(book['description']) else '',
                    'thumbnail': str(book['thumbnail']) if pd.notna(book['thumbnail']) else '',
                    'score': float(book['score'])
                })
        
        return recommendations
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/index')
@login_required
def index():
    try:
        # Get personalized recommendations
        recommendations = get_recommendations(current_user.id)
        
        # Map the recommendations to match the template's expected fields
        mapped_recommendations = []
        for book in recommendations:
            mapped_recommendations.append({
                'title': book['title'],
                'author': book['author'],
                'genre': book['category'],  # Map category to genre
                'published_date': book['published_year'],  # Map published_year to published_date
                'description': book['description'],
                'thumbnail': book['thumbnail'],
                'average_rating': book['average_rating'] if 'average_rating' in book else '',  # Add average_rating
                'completed': False,  # New books in recommendations are not completed
                'id': book['title']  # Use title as ID since that's what we need for marking as read
            })
        
        return render_template('index.html', 
                             user=current_user,
                             recommendations=mapped_recommendations)
    except Exception as e:
        print(f"Error in index: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while loading recommendations.', 'error')
        return render_template('index.html', user=current_user)

@app.route('/search_books')
@login_required
def search_books():
    try:
        query = request.args.get('query', '').strip()
        print(f"Received search query: {query}")
        if not query:
            return jsonify([])
        
        books_df = load_books(query)
        print(f"Search returned {len(books_df)} books")
        if books_df.empty:
            return jsonify([])
        
        # Get user's completed books
        completed_books = {book.book_title for book in ReadBook.query.filter_by(user_id=current_user.id, status='read').all()}
        print(f"User has {len(completed_books)} completed books")
        
        # Convert DataFrame to list of dictionaries and add completed status
        books_list = []
        for _, book in books_df.iterrows():
            book_dict = {
                'title': str(book['title']),
                'author': str(book['authors']),
                'category': str(book['category']),
                'published_year': str(book['published_year']) if pd.notna(book['published_year']) else '',
                'average_rating': str(book['average_rating']) if pd.notna(book['average_rating']) else '',
                'description': str(book['description']) if pd.notna(book['description']) else '',
                'thumbnail': str(book['thumbnail']) if pd.notna(book['thumbnail']) else '',
                'completed': book['title'] in completed_books
            }
            books_list.append(book_dict)
        
        print(f"Returning {len(books_list)} books")
        return jsonify(books_list)
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/mark_book_read', methods=['POST'])
@login_required
def mark_book_read():
    try:
        data = request.get_json()
        print(f"Received mark_book_read request with data: {data}")
        
        book_title = data.get('bookTitle')
        print(f"Book title: {book_title}")
        
        if not book_title:
            print("Error: Book title is missing")
            return jsonify({'error': 'Book title is required'}), 400

        # Check if book is already marked as read
        existing_read = ReadBook.query.filter_by(
            user_id=current_user.id,
            book_title=book_title
        ).first()
        print(f"Existing read entry: {existing_read}")

        if existing_read:
            print("Book already marked as completed")
            return jsonify({'message': 'Book already marked as completed', 'completed': True}), 200

        # Create new ReadBook entry
        read_book = ReadBook(
            user_id=current_user.id,
            book_title=book_title,
            status='read'
        )
        print(f"Created new ReadBook entry: {read_book}")
        
        db.session.add(read_book)
        db.session.commit()
        print("Successfully saved to database")

        return jsonify({'message': 'Book marked as completed successfully', 'completed': True}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error in mark_book_read: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('Title')
            author = request.form.get('Author')
            year = request.form.get('Year')
            categories = request.form.get('Categories')  # This will be a comma-separated string
            rating = request.form.get('Rate')
            description = request.form.get('Description')
            
            if not all([title, author, year, categories]):
                flash('Please fill in all required fields', 'error')
                return redirect(url_for('add_book'))
            
            # Split categories into a list
            category_list = categories.split(',')
            
            # Add to CSV file
            csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.csv')
            books_df = pd.read_csv(csv_path)
            
            # Check if book already exists
            if not books_df[books_df['title'].str.lower() == title.lower()].empty:
                flash('This book already exists in the dataset.', 'error')
                return redirect(url_for('add_book'))
            
            # Create new book entry
            new_book = {
                'title': title,
                'authors': author,
                'description': description or '',
                'published_year': year,
                'average_rating': float(rating) if rating else 0.0,
                'category': ', '.join(category_list),  # Join categories with comma and space
                'thumbnail': ''
            }
            
            # Update CSV
            books_df = pd.concat([books_df, pd.DataFrame([new_book])], ignore_index=True)
            books_df.to_csv(csv_path, index=False)
            
            # Add to read books with rating
            read_book = ReadBook(
                user_id=current_user.id,
                book_title=title,
                rating=float(rating) if rating else 0.0,
                review=description or '',
                status='read'  # Since we're adding rating, mark as read
            )
            db.session.add(read_book)
            db.session.commit()
            
            flash('Book added successfully!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            if 'read_book' in locals():
                db.session.rollback()
            print(f"Error adding book: {e}")
            import traceback
            traceback.print_exc()
            flash('Error adding book. Please try again.', 'error')
            return redirect(url_for('add_book'))
    
    return render_template('add_book.html')

@app.route('/profile')
@login_required
def profile():
    try:
        # Get user's completed books with full details
        completed_books_db = ReadBook.query.filter_by(user_id=current_user.id, status='read').all()
        
        # Get all books data
        books_df = load_books()
        
        # Create a list of completed books with full details
        completed_books = []
        for book_record in completed_books_db:
            # Find the book in the DataFrame
            book_data = books_df[books_df['title'] == book_record.book_title]
            if not book_data.empty:
                book = book_data.iloc[0]
                # Fix thumbnail URL
                thumbnail_url = book['thumbnail'] if pd.notna(book['thumbnail']) else None
                if thumbnail_url:
                    # Add zoom parameter for higher quality image
                    if 'zoom=' not in thumbnail_url and 'books.google.com' in thumbnail_url:
                        thumbnail_url += '&zoom=1'
                    # Add HTTPS if not present
                    if thumbnail_url.startswith('http://'):
                        thumbnail_url = 'https://' + thumbnail_url[7:]
                
                completed_books.append({
                    'title': book['title'],
                    'authors': book['authors'],
                    'categories': book['category'],
                    'thumbnail_url': thumbnail_url,
                    'description': book['description'] if pd.notna(book['description']) else None,
                    'published_year': book['published_year'] if pd.notna(book['published_year']) else None,
                    'average_rating': book['average_rating'] if pd.notna(book['average_rating']) else None
                })
        
        # Get user's reading preferences from UserPreference model
        user_preferences = UserPreference.query.filter_by(user_id=current_user.id).all()
        reading_preferences = [pref.category for pref in user_preferences]
        
        return render_template('profile.html', 
                             user=current_user, 
                             completed_books=completed_books,
                             reading_preferences=reading_preferences)
    except Exception as e:
        print(f"Error in profile route: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred while loading your profile.', 'error')
        return redirect(url_for('index'))

@app.route('/preferences', methods=['GET'])
@login_required
def preferences():
    return render_template('preferences.html')

@app.route('/save_preferences', methods=['POST'])
@login_required
def save_preferences():
    try:
        data = request.get_json()
        categories = data.get('categories', [])
        
        # Delete existing preferences for this user
        UserPreference.query.filter_by(user_id=current_user.id).delete()
        
        # Save new preferences
        for category in categories:
            preference = UserPreference(
                user_id=current_user.id,
                category=category
            )
            db.session.add(preference)
        
        db.session.commit()
        return jsonify({'message': 'Preferences saved successfully'}), 200
    except Exception as e:
        print(f"Error saving preferences: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to save preferences'}), 500

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        gender = request.form.get('gender', 'male')  # Default to male if not specified
        preferences = request.form.getlist('preferences')
        
        try:
            current_user.username = username
            current_user.email = email
            current_user.gender = gender
            
            # Update preferences
            UserPreference.query.filter_by(user_id=current_user.id).delete()
            for category in preferences:
                preference = UserPreference(user_id=current_user.id, category=category)
                db.session.add(preference)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'error')
            return redirect(url_for('edit_profile'))
            
    preferences = [pref.category for pref in current_user.preferences]
    return render_template('edit_profile.html', user=current_user, preferences=preferences)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validate input
        if not username or not email or not password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('signup.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('signup.html')

        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash('Account created successfully!', 'success')
            return redirect(url_for('preferences'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating account. Please try again.', 'error')
            return render_template('signup.html')

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/remove_completed_book', methods=['POST'])
@login_required
def remove_completed_book():
    try:
        data = request.get_json()
        book_title = data.get('bookId')  # We're receiving the book title here
        
        if not book_title:
            return jsonify({'error': 'Book title is required'}), 400

        # Find and delete the completed book
        completed_book = ReadBook.query.filter_by(
            user_id=current_user.id,
            book_title=book_title
        ).first()

        if not completed_book:
            return jsonify({'error': 'Book not found in completed list'}), 404

        db.session.delete(completed_book)
        db.session.commit()

        return jsonify({'message': 'Book removed from completed list successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error removing book: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['GET', 'POST'])
def reset():
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Email is required.', 'error')
            return render_template('reset.html')
            
        user = User.query.filter_by(email=email).first()
        if user:
           
            flash('If an account exists with that email, you will receive a password reset link.', 'success')
            return redirect(url_for('login'))
        else:
            # Don't reveal if the email exists or not for security
            flash('If an account exists with that email, you will receive a password reset link.', 'success')
            return redirect(url_for('login'))
            
    return render_template('reset.html')

@app.route('/mark_as_read', methods=['POST'])
@login_required
def mark_as_read():
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        
        if not book_id:
            return jsonify({'success': False, 'message': 'Book ID is required'}), 400

        # Check if book is already marked as read
        existing_read = ReadBook.query.filter_by(
            user_id=current_user.id,
            book_title=book_id  # Using book_id as title since that's what we're passing
        ).first()

        if existing_read:
            # If book is already marked as read, remove it
            db.session.delete(existing_read)
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Book removed from completed list',
                'is_completed': False
            })

        # Create new ReadBook entry
        read_book = ReadBook(
            user_id=current_user.id,
            book_title=book_id,  # Using book_id as title
            status='read'
        )
        
        db.session.add(read_book)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Book marked as completed successfully',
            'is_completed': True
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error in mark_as_read: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
