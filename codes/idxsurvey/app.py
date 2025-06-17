from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Load Configuration from config.py ---
try:
    app.config.from_object('config')
    if not app.config.get('SECRET_KEY'):
        print("CRITICAL: SECRET_KEY not found in config.py or is empty. Using a temporary insecure key.")
        app.config['SECRET_KEY'] = 'temporary_insecure_fallback_key_123!@#_final_v2'  # Fallback
except ImportError:
    print("CRITICAL: config.py not found. Please ensure it exists in the project root. Using fallback configurations.")
    app.config['SECRET_KEY'] = 'temporary_insecure_fallback_key_123!@#_final_v2'
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = ''
    app.config['MYSQL_DB'] = 'idxsurvey'
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# --- MySQL Initialization ---
mysql = MySQL(app)


# --- Helper Functions ---
def get_user_by_username(username):
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        return user
    except Exception as e:
        return None


def create_user(username, password):
    try:
        password_hash = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, password_hash))
        mysql.connection.commit()
        user_id = cur.lastrowid
        cur.close()
        return user_id
    except mysql.connection.IntegrityError:
        flash("Username already exists. Please choose a different one.", "warning")
        return None
    except Exception as e:
        flash("An error occurred during registration. Please try again later.", "danger")
        return None


# --- Routes ---
@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect(url_for('survey_page'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logged_in' in session:
        return redirect(url_for('survey_page'))
    if request.method == 'POST':
        username = request.form.get('username')
        password_candidate = request.form.get('password')
        if not username or not password_candidate:
            flash("Username and password are required.", "warning")
            return render_template('login.html')
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password_candidate):
            session['logged_in'] = True
            session['username'] = user['username']
            session['user_id'] = user['id']
            flash('You were successfully logged in!', 'success')
            return redirect(url_for('survey_page'))
        else:
            flash('Invalid username or password. Please try again.', 'danger')
        return render_template('login.html')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'logged_in' in session:
        return redirect(url_for('survey_page'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not username or not password or not confirm_password:
            flash("All fields are required.", "warning")
        elif len(password) < 6:
            flash("Password must be at least 6 characters long.", "warning")
        elif password != confirm_password:
            flash("Passwords do not match.", "warning")
        else:
            user_id = create_user(username, password)
            if user_id:
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
        return render_template('register.html', username=username)
    return render_template('register.html')


@app.route('/survey')
def survey_page():
    if 'logged_in' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('login'))

    selected_fid = request.args.get('selected_fid', None)
    files_data = []
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT DISTINCT fid, fname FROM allfiles ORDER BY fname")
        files_data = cur.fetchall()
        files_with_serials = [(i + 1, f['fid'], f['fname']) for i, f in enumerate(files_data)]
        #print(files_with_serials)
        cur.close()
    except Exception as e:
        flash("Error fetching files from database.", "danger")
    return render_template('survey.html',
                           username=session.get('username'),
                           files=files_with_serials,
                           selected_fid=selected_fid)


@app.route('/get_prompts_for_file/<string:file_id>')
def get_prompts_for_file(file_id):
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    prompts_for_frontend = []
    user_id = session['user_id']
    try:
        cur = mysql.connection.cursor()
        sql_final = """
            SELECT 
                p_unique.pid, 
                p_unique.prompt, 
                p_unique.searching_area,
                p_unique.description,
                EXISTS (
                    SELECT 1 
                    FROM humanevaluation he 
                    WHERE he.pid = p_unique.pid AND he.fid = %s AND he.actor = %s
                ) AS is_evaluated
            FROM (
                SELECT 
                    pid, 
                    MIN(prompt) AS prompt,  -- Or any aggregate if prompt text can vary for same pid
                    MIN(searching_area) AS searching_area, -- Or any aggregate
                    MIN(description) AS description -- Or any aggregate
                FROM prompts
                GROUP BY pid
            ) AS p_unique
            ORDER BY p_unique.pid;
        """
        cur.execute(sql_final, (file_id, user_id))  # Pass file_id and user_id for the EXISTS subquery
        db_prompts = cur.fetchall()
        cur.close()

        for index, prompt_data in enumerate(db_prompts):
            prompts_for_frontend.append({
                'pid': prompt_data['pid'],
                'displayText': f"Question: {index + 1}",
                'fullPromptText': prompt_data['prompt'],
                'searching_area': prompt_data['searching_area'],  # Add searching_area
                'description': prompt_data['description'],
                'is_evaluated': bool(prompt_data['is_evaluated'])
            })
    except Exception as e:
        return jsonify({'error': 'Error fetching prompts', 'details': str(e)}), 500
    return jsonify(prompts_for_frontend)


@app.route('/check_evaluation_status/<string:file_id>/<string:prompt_id>')
def check_evaluation_status(file_id, prompt_id):
    if 'logged_in' not in session or 'user_id' not in session:
        return jsonify({'error': 'User not logged in'}), 401
    user_id = session['user_id']
    is_evaluated = False
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT EXISTS(
                SELECT 1 FROM humanevaluation
                WHERE actor = %s AND fid = %s AND pid = %s
            ) AS evaluated_exists;
        """, (user_id, file_id, prompt_id))
        result = cur.fetchone()
        if result and result['evaluated_exists']:
            is_evaluated = True
        cur.close()
    except Exception as e:
        return jsonify({'error': 'Error checking status', 'details': str(e)}), 500
    return jsonify({'is_evaluated': is_evaluated})


@app.route('/get_model_responses/<string:file_id>/<string:prompt_id>')
def get_model_responses(file_id, prompt_id):
    if 'logged_in' not in session:
        return jsonify({'error': 'User not logged in'}), 401

    responses = {}
    frontend_model_keys = ['Model1', 'Model2', 'Model3', 'Model4']
    for key in frontend_model_keys:
        responses[key] = ""
    try:
        cur = mysql.connection.cursor()
        sql = """
            SELECT modelname, response
            FROM infer
            WHERE fid = %s AND pid = %s
            ORDER BY id; 
        """
        cur.execute(sql, (file_id, prompt_id))
        db_results = cur.fetchall()
        cur.close()

        for i, row_data in enumerate(db_results):
            if i < len(frontend_model_keys):
                frontend_key_to_populate = frontend_model_keys[i]
                responses[frontend_key_to_populate] = row_data['response'] if row_data['response'] is not None else ""
            else:
                break
    except Exception as e:
        return jsonify({'error': 'Error fetching responses', 'details': str(e)}), 500
    return jsonify(responses)


@app.route('/submit_evaluation', methods=['POST'])
def submit_evaluation():
    if 'logged_in' not in session or 'user_id' not in session:
        flash('Your session has expired or is invalid. Please log in again.', 'warning')
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_id = session['user_id']
        file_identifier = request.form.get('file_id')
        prompt_identifier = request.form.get('question_id')

        if not all([file_identifier, prompt_identifier]):
            flash("File and Question selection are required.", "danger")
            return redirect(url_for('survey_page', selected_fid=file_identifier or ''))

        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                SELECT COUNT(hid) as count FROM humanevaluation
                WHERE actor = %s AND fid = %s AND pid = %s
            """, (user_id, file_identifier, prompt_identifier))
            existing_eval_count = cur.fetchone()['count']

            if existing_eval_count > 0:
                flash("You have already submitted an evaluation for this file and question combination.", "warning")
                cur.close()
                return redirect(url_for('survey_page', selected_fid=file_identifier))

            for i in range(1, 5):
                frontend_model_key = f'Model{i}'
                model_answer = request.form.get(f'{frontend_model_key.lower()}_answer')
                model_rating = request.form.get(f'{frontend_model_key.lower()}_rating')

                if model_rating:
                    sql_insert_eval = """
                        INSERT INTO humanevaluation
                        (actor, modelname, fid, pid, human_eval)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    val_insert_eval = (user_id, frontend_model_key, file_identifier, prompt_identifier, model_rating)
                    cur.execute(sql_insert_eval, val_insert_eval)

            mysql.connection.commit()
            cur.close()
            flash('Evaluation submitted successfully!', 'success')
        except Exception as e:
            mysql.connection.rollback()
            flash(f'An error occurred while submitting your evaluation: {str(e)}', 'danger')

        return redirect(url_for('survey_page', selected_fid=file_identifier))


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    port = int(app.config.get('PORT', 5001))
    app.run(debug=app.config.get('DEBUG', True), port=port)
