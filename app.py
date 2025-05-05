# taxi_rental_app/app.py
# ---
from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2 import sql
import uuid
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = '8e967fe10f07a8dcc94003436508352d'

# Database connection configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def check_user():
    if session.get('user'):
        role = session.get('role')
        if role == 'manager':
            return 'manager_dashboard'
        elif role == 'client':
            return 'client_dashboard'
        elif role == 'driver':
            return 'driver_dashboard'
        else:
            return ''
    else:
        return ''

@app.route('/')
def index():
    # return render_template('login.html')
    current_route = check_user()
    if (current_route):
        return redirect(url_for(current_route))
    else:
        return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    current_route = check_user()
    if (current_route):
        return redirect(url_for(current_route))

    if request.method == 'POST':
        role = request.form['role']
        if role == 'manager':
            ssn = request.form['password']
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT ssn FROM Manager WHERE ssn = %s', (ssn,))
            manager = cur.fetchone()
            cur.close()
            conn.close()
            if manager:
                session['user'] = ssn
                session['role'] = 'manager'
                return redirect(url_for('manager_dashboard'))
            else:
                flash('Invalid SSN')
        elif role == 'client':
            email = request.form['password']
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT email FROM Client WHERE email = %s', (email,))
            client = cur.fetchone()
            cur.close()
            conn.close()
            if client:
                session['user'] = email
                session['role'] = 'client'
                return redirect(url_for('client_dashboard'))
            else:
                flash('Invalid email')
        elif role == 'driver':
            name = request.form['password']
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT name FROM Driver WHERE name = %s', (name,))
            driver = cur.fetchone()
            cur.close()
            conn.close()
            if driver:
                session['user'] = name
                session['role'] = 'driver'
                return redirect(url_for('driver_dashboard'))
            else:
                flash('Invalid name')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('role', None)
    return redirect(url_for('index'))

@app.route('/register_manager', methods=['GET', 'POST'])
def register_manager():
    if request.method == 'POST':
        name = request.form['name']
        ssn = request.form['ssn']
        email = request.form['email']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO Manager (ssn, name, email) VALUES (%s, %s, %s)',
                (ssn, name, email)
            )
            conn.commit()
            flash('Manager registered successfully')
            return redirect(url_for('login'))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('register_manager.html')

@app.route('/register_client', methods=['GET', 'POST'])
def register_client():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        addresses = request.form.getlist('address[]')
        card_numbers = request.form.getlist('card_number[]')
        payment_addresses = request.form.getlist('payment_address[]')
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO Client (email, name) VALUES (%s, %s)', (email, name))
            for addr in addresses:
                road_name, number, city = addr.split(',')
                cur.execute(
                    'INSERT INTO Address (road_name, number, city) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                    (road_name.strip(), number.strip(), city.strip())
                )
                cur.execute(
                    'INSERT INTO ClientAddress (client_email, road_name, number, city) VALUES (%s, %s, %s, %s)',
                    (email, road_name.strip(), number.strip(), city.strip())
                )
            for card, pay_addr in zip(card_numbers, payment_addresses):
                pay_road, pay_num, pay_city = pay_addr.split(',')
                cur.execute(
                    'INSERT INTO Address (road_name, number, city) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                    (pay_road.strip(), pay_num.strip(), pay_city.strip())
                )
                cur.execute(
                    'INSERT INTO CreditCard (card_number, client_email, payment_road_name, payment_number, payment_city) VALUES (%s, %s, %s, %s, %s)',
                    (card, email, pay_road.strip(), pay_num.strip(), pay_city.strip())
                )
            conn.commit()
            flash('Client registered successfully')
            return redirect(url_for('login'))
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('register_client.html')

@app.route('/manager_dashboard')
def manager_dashboard():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    # ── load all driver names for the dropdown
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT name FROM Driver')
    driver_records = cur.fetchall()
    cur.close()
    conn.close()
    drivers = [row[0] for row in driver_records]

    return render_template(
        'manager_dashboard.html',
        drivers=drivers
    )

@app.route('/remove_driver', methods=['GET', 'POST'])
def remove_driver():
    # only managers allowed
    if session.get('role') != 'manager':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur  = conn.cursor()

    if request.method == 'POST':
        driver_name = request.form['driver_name']
        try:
            # First delete associated reviews
            cur.execute(
                'DELETE FROM Review WHERE driver_name = %s',
                (driver_name,)
            )
            # Then delete associated rent records
            cur.execute(
                'DELETE FROM Rent WHERE driver_name = %s',
                (driver_name,)
            )
            # Delete driver's model assignments
            cur.execute(
                'DELETE FROM DriverModel WHERE driver_name = %s',
                (driver_name,)
            )
            # Finally delete the driver
            cur.execute(
                'DELETE FROM Driver WHERE name = %s',
                (driver_name,)
            )
            conn.commit()
            flash(f'Driver "{driver_name}" removed successfully.')
        except Exception as e:
            conn.rollback()
            flash(f'Error removing driver: {e}')

    # on GET (or after POST), reload list of names
    cur.execute('SELECT name FROM Driver ORDER BY name')
    drivers = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()
    return render_template('remove_driver.html', drivers=drivers)

@app.route('/remove_car', methods=['GET', 'POST'])
def remove_car():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        car_id = request.form['car_id']
        try:
            # First delete associated rent records
            cur.execute(
                'DELETE FROM Rent WHERE car_id = %s',
                (car_id,)
            )
            # Then delete driver model assignments
            cur.execute(
                'DELETE FROM DriverModel WHERE car_id = %s',
                (car_id,)
            )
            # Delete all models for this car
            cur.execute(
                'DELETE FROM Model WHERE car_id = %s',
                (car_id,)
            )
            # Finally delete the car
            cur.execute(
                'DELETE FROM Car WHERE car_id = %s',
                (car_id,)
            )
            conn.commit()
            flash(f'Car "{car_id}" removed successfully.')
        except Exception as e:
            conn.rollback()
            flash(f'Error removing car: {e}')

    # on GET or after POST, reload the current cars
    cur.execute('SELECT car_id, brand FROM Car ORDER BY car_id')
    cars = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('remove_car.html', cars=cars)

@app.route('/remove_model', methods=['GET', 'POST'])
def remove_model():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        sel = request.form['model']              # "model" field is "<model_id>|<car_id>"
        model_id, car_id = sel.split('|')
        try:
            # First delete associated rent records
            cur.execute(
                'DELETE FROM Rent WHERE model_id = %s AND car_id = %s',
                (model_id, car_id)
            )
            # Then delete driver model assignments
            cur.execute(
                'DELETE FROM DriverModel WHERE model_id = %s AND car_id = %s',
                (model_id, car_id)
            )
            # Finally delete the model
            cur.execute(
                'DELETE FROM Model WHERE model_id = %s AND car_id = %s',
                (model_id, car_id)
            )
            conn.commit()
            flash(f'Model "{model_id}" (Car {car_id}) removed successfully.')
        except Exception as e:
            conn.rollback()
            flash(f'Error removing model: {e}')

    # on GET or after POST, reload all models
    cur.execute('''
        SELECT m.model_id, m.car_id, c.brand
        FROM Model m
        JOIN Car c ON m.car_id = c.car_id
        ORDER BY m.model_id
    ''')
    models = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('remove_model.html', models=models)

@app.route('/client_dashboard')
def client_dashboard():
    if session.get('role') != 'client':
        return redirect(url_for('login'))
    return render_template('client_dashboard.html')

@app.route('/driver_dashboard')
def driver_dashboard():
    if session.get('role') != 'driver':
        return redirect(url_for('login'))
    return render_template('driver_dashboard.html')

@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    if request.method == 'POST':
        brand = request.form['brand']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            # Get the maximum car_id and increment by 1
            cur.execute('SELECT COALESCE(MAX(car_id), 0) + 1 FROM Car')
            car_id = cur.fetchone()[0]
            
            cur.execute(
                'INSERT INTO Car (car_id, brand) VALUES (%s, %s)',
                (car_id, brand)
            )
            conn.commit()
            flash(f'Car added successfully with ID: {car_id}')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('add_car.html')

@app.route('/add_model', methods=['GET', 'POST'])
def add_model():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get available cars for the dropdown
    cur.execute('SELECT car_id, brand FROM Car ORDER BY car_id')
    cars = cur.fetchall()
    
    if request.method == 'POST':
        car_id = request.form['car_id']
        color = request.form['color']
        construction_year = request.form['construction_year']
        transmission_type = request.form['transmission_type']
        try:
            cur.execute(
                'INSERT INTO Model (car_id, color, construction_year, transmission_type) VALUES (%s, %s, %s, %s)',
                (car_id, color, construction_year, transmission_type)
            )
            conn.commit()
            flash('Model added successfully')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
    
    cur.close()
    conn.close()
    return render_template('add_model.html', cars=cars)

@app.route('/add_driver', methods=['GET', 'POST'])
def add_driver():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        road_name = request.form['road_name']
        number = request.form['number']
        city = request.form['city']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO Address (road_name, number, city) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                (road_name, number, city)
            )
            cur.execute(
                'INSERT INTO Driver (name, road_name, number, city) VALUES (%s, %s, %s, %s)',
                (name, road_name, number, city)
            )
            conn.commit()
            flash('Driver added successfully')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('add_driver.html')

@app.route('/top_k_clients', methods=['GET', 'POST'])
def top_k_clients():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    clients = []
    if request.method == 'POST':
        k = request.form['k']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
                SELECT c.name, c.email, COUNT(r.rent_id) as rent_count
                FROM Client c
                LEFT JOIN Rent r ON c.email = r.client_email
                GROUP BY c.email, c.name
                ORDER BY rent_count DESC
                LIMIT %s
                ''',
                (k,)
            )
            clients = cur.fetchall()
        except psycopg2.Error as e:
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('top_k_clients.html', clients=clients)

@app.route('/car_model_rents')
def car_model_rents():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            SELECT m.model_id, m.car_id, c.brand, m.color, m.construction_year, m.transmission_type, COUNT(r.rent_id) as rent_count
            FROM Model m
            JOIN Car c ON m.car_id = c.car_id
            LEFT JOIN Rent r ON m.model_id = r.model_id AND m.car_id = r.car_id
            GROUP BY m.model_id, m.car_id, c.brand, m.color, m.construction_year, m.transmission_type
            '''
        )
        models = cur.fetchall()
    except psycopg2.Error as e:
        flash(f'Error: {e}')
        models = []
    finally:
        cur.close()
        conn.close()
    return render_template('car_model_rents.html', models=models)

@app.route('/driver_stats')
def driver_stats():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            WITH rent_counts AS (
            SELECT driver_name, COUNT(*) AS rent_count
            FROM Rent
            GROUP BY driver_name
            ),
            review_avgs AS (
                SELECT driver_name, AVG(rating) AS avg_rating
                FROM Review
                GROUP BY driver_name
            )
            SELECT  d.name,
                    COALESCE(rc.rent_count, 0) AS rent_count,
                    COALESCE(ra.avg_rating, 0) AS avg_rating
            FROM    Driver d
            LEFT JOIN rent_counts  rc ON rc.driver_name  = d.name
            LEFT JOIN review_avgs ra ON ra.driver_name = d.name;
            '''
        )
        drivers = cur.fetchall()
    except psycopg2.Error as e:
        flash(f'Error: {e}')
        drivers = []
    finally:
        cur.close()
        conn.close()
    return render_template('driver_stats.html', drivers=drivers)

@app.route('/city_query', methods=['GET', 'POST'])
def city_query():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    clients = []
    if request.method == 'POST':
        city1 = request.form['city1']
        city2 = request.form['city2']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
                SELECT DISTINCT c.name, c.email
                FROM Client c
                JOIN ClientAddress ca ON c.email = ca.client_email
                JOIN Rent r ON c.email = r.client_email
                JOIN Driver d ON r.driver_name = d.name
                WHERE ca.city = %s AND d.city = %s
                ''',
                (city1, city2)
            )
            clients = cur.fetchall()
        except psycopg2.Error as e:
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('city_query.html', clients=clients)

@app.route('/problematic_drivers')
def problematic_drivers():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            SELECT d.name
            FROM Driver d
            JOIN Rent r ON d.name = r.driver_name
            JOIN Review rev ON d.name = rev.driver_name
            JOIN Client c ON r.client_email = c.email
            JOIN ClientAddress ca ON c.email = ca.client_email
            WHERE d.city = 'Chicago' AND ca.city = 'Chicago'
            GROUP BY d.name
            HAVING AVG(rev.rating) < 2.5 AND COUNT(DISTINCT r.rent_id) >= 2
            '''
        )
        drivers = cur.fetchall()
    except psycopg2.Error as e:
        flash(f'Error: {e}')
        drivers = []
    finally:
        cur.close()
        conn.close()
    return render_template('problematic_drivers.html', drivers=drivers)

@app.route('/brand_stats')
def brand_stats():
    if session.get('role') != 'manager':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            WITH rents_by_brand AS (
            SELECT c.brand, COUNT(*) AS rent_count
            FROM   Car   c
            JOIN   Model m  ON m.car_id = c.car_id
            JOIN   Rent  r  ON r.car_id  = m.car_id
                        AND r.model_id = m.model_id
            GROUP  BY c.brand
            ),
            reviews_by_brand AS (
                SELECT c.brand, AVG(rev.rating) AS avg_rating
                FROM   Car         c
                JOIN   Model       m  ON m.car_id = c.car_id
                JOIN   DriverModel dm ON dm.car_id   = m.car_id
                                    AND dm.model_id = m.model_id
                JOIN   Review      rev ON rev.driver_name = dm.driver_name
                GROUP  BY c.brand
            )
            SELECT  b.brand,
                    COALESCE(rv.avg_rating, 0) AS avg_rating,
                    COALESCE(rt.rent_count, 0) AS rent_count
            FROM   (SELECT DISTINCT brand FROM Car) b
            LEFT JOIN rents_by_brand   rt ON rt.brand = b.brand
            LEFT JOIN reviews_by_brand rv ON rv.brand = b.brand;
            '''
        )
        brands = cur.fetchall()
    except psycopg2.Error as e:
        flash(f'Error: {e}')
        brands = []
    finally:
        cur.close()
        conn.close()
    return render_template('brand_stats.html', brands=brands)

@app.route('/update_driver_address', methods=['GET', 'POST'])
def update_driver_address():
    if session.get('role') != 'driver':
        return redirect(url_for('login'))
    if request.method == 'POST':
        road_name = request.form['road_name']
        number = request.form['number']
        city = request.form['city']
        driver_name = session['user']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                'INSERT INTO Address (road_name, number, city) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING',
                (road_name, number, city)
            )
            cur.execute(
                'UPDATE Driver SET road_name = %s, number = %s, city = %s WHERE name = %s',
                (road_name, number, city, driver_name)
            )
            conn.commit()
            flash('Address updated successfully')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('update_driver_address.html')

@app.route('/view_models')
def view_models():
    if session.get('role') != 'driver':
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            SELECT m.model_id, m.car_id, c.brand, m.color, m.construction_year, m.transmission_type
            FROM Model m
            JOIN Car c ON m.car_id = c.car_id
            '''
        )
        models = cur.fetchall()
    except psycopg2.Error as e:
        flash(f'Error: {e}')
        models = []
    finally:
        cur.close()
        conn.close()
    return render_template('view_models.html', models=models)

@app.route('/assign_model', methods=['GET', 'POST'])
def assign_model():
    if session.get('role') != 'driver':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get available models for the dropdown
    cur.execute('''
        SELECT m.model_id, m.car_id, c.brand, m.color, m.construction_year, m.transmission_type
        FROM Model m
        JOIN Car c ON m.car_id = c.car_id
        WHERE NOT EXISTS (
            SELECT 1 FROM DriverModel dm 
            WHERE dm.model_id = m.model_id 
            AND dm.car_id = m.car_id 
            AND dm.driver_name = %s
        )
        ORDER BY m.model_id
    ''', (session['user'],))
    models = cur.fetchall()
    
    if request.method == 'POST':
        model_sel = request.form['model']  # Format: "model_id|car_id"
        model_id, car_id = model_sel.split('|')
        driver_name = session['user']
        try:
            cur.execute(
                'INSERT INTO DriverModel (driver_name, model_id, car_id) VALUES (%s, %s, %s)',
                (driver_name, model_id, car_id)
            )
            conn.commit()
            flash('Model assigned successfully')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
    
    cur.close()
    conn.close()
    return render_template('assign_model.html', models=models)

@app.route('/book_rent', methods=['GET', 'POST'])
def book_rent():
    if session.get('role') != 'client':
        return redirect(url_for('login'))
    models = []
    if request.method == 'POST':
        rent_date = request.form['rent_date']
        client_email = session['user']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
                SELECT m.model_id, m.car_id, c.brand, m.color, m.construction_year, m.transmission_type
                FROM Model m
                JOIN Car c ON m.car_id = c.car_id
                JOIN DriverModel dm ON m.model_id = dm.model_id AND m.car_id = dm.car_id
                JOIN Driver d ON dm.driver_name = d.name
                WHERE NOT EXISTS (
                    SELECT 1 FROM Rent r
                    WHERE r.model_id = m.model_id AND r.car_id = m.car_id AND r.rent_date = %s
                )
                AND NOT EXISTS (
                    SELECT 1 FROM Rent r
                    WHERE r.driver_name = d.name AND r.rent_date = %s
                )
                ''',
                (rent_date, rent_date)
            )
            models = cur.fetchall()
            if 'book' in request.form:
                model_id = request.form['model_id']
                car_id = request.form['car_id']
                cur.execute(
                    '''
                    SELECT d.name
                    FROM Driver d
                    JOIN DriverModel dm ON d.name = dm.driver_name
                    WHERE dm.model_id = %s AND dm.car_id = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM Rent r
                        WHERE r.driver_name = d.name AND r.rent_date = %s
                    )
                    LIMIT 1
                    ''',
                    (model_id, car_id, rent_date)
                )
                driver = cur.fetchone()
                if driver:
                    rent_id = str(uuid.uuid4())[:8]
                    cur.execute(
                        '''
                        INSERT INTO Rent (rent_id, rent_date, client_email, driver_name, model_id, car_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ''',
                        (rent_id, rent_date, client_email, driver[0], model_id, car_id)
                    )
                    conn.commit()
                    flash('Rent booked successfully')
                else:
                    flash('No available driver for this model')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('book_rent.html', models=models)

@app.route('/book_best_driver', methods=['GET', 'POST'])
def book_best_driver():
    if session.get('role') != 'client':
        return redirect(url_for('login'))
    models = []
    if request.method == 'POST':
        rent_date = request.form['rent_date']
        client_email = session['user']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
                SELECT m.model_id, m.car_id, c.brand, m.color, m.construction_year, m.transmission_type
                FROM Model m
                JOIN Car c ON m.car_id = c.car_id
                JOIN DriverModel dm ON m.model_id = dm.model_id AND m.car_id = dm.car_id
                JOIN Driver d ON dm.driver_name = d.name
                WHERE NOT EXISTS (
                    SELECT 1 FROM Rent r
                    WHERE r.model_id = m.model_id AND r.car_id = m.car_id AND r.rent_date = %s
                )
                AND NOT EXISTS (
                    SELECT 1 FROM Rent r
                    WHERE r.driver_name = d.name AND r.rent_date = %s
                )
                ''',
                (rent_date, rent_date)
            )
            models = cur.fetchall()
            if 'book' in request.form:
                model_id = request.form['model_id']
                car_id = request.form['car_id']
                cur.execute(
                    '''
                    SELECT d.name
                    FROM Driver d
                    JOIN DriverModel dm ON d.name = dm.driver_name
                    LEFT JOIN Review rev ON d.name = rev.driver_name
                    WHERE dm.model_id = %s AND dm.car_id = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM Rent r
                        WHERE r.driver_name = d.name AND r.rent_date = %s
                    )
                    GROUP BY d.name
                    ORDER BY COALESCE(AVG(rev.rating), 0) DESC
                    LIMIT 1
                    ''',
                    (model_id, car_id, rent_date)
                )
                driver = cur.fetchone()
                if driver:
                    rent_id = str(uuid.uuid4())[:8]
                    cur.execute(
                        '''
                        INSERT INTO Rent (rent_id, rent_date, client_email, driver_name, model_id, car_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ''',
                        (rent_id, rent_date, client_email, driver[0], model_id, car_id)
                    )
                    conn.commit()
                    flash('Rent booked with best driver')
                else:
                    flash('No available driver for this model')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('book_best_driver.html', models=models)

@app.route('/view_rents')
def view_rents():
    if session.get('role') != 'client':
        return redirect(url_for('login'))
    client_email = session['user']
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            '''
            SELECT r.rent_id, r.rent_date, r.driver_name, m.model_id, m.car_id, c.brand, m.color
            FROM Rent r
            JOIN Model m ON r.model_id = m.model_id AND r.car_id = m.car_id
            JOIN Car c ON m.car_id = c.car_id
            WHERE r.client_email = %s
            ''',
            (client_email,)
        )
        rents = cur.fetchall()
    except psycopg2.Error as e:
        flash(f'Error: {e}')
        rents = []
    finally:
        cur.close()
        conn.close()
    return render_template('view_rents.html', rents=rents)

@app.route('/add_review', methods=['GET', 'POST'])
def add_review():
    if session.get('role') != 'client':
        return redirect(url_for('login'))
    if request.method == 'POST':
        driver_name = request.form['driver_name']
        rating = request.form['rating']
        message = request.form['message']
        client_email = session['user']
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                '''
                SELECT 1 FROM Rent
                WHERE client_email = %s AND driver_name = %s
                ''',
                (client_email, driver_name)
            )
            if cur.fetchone():
                review_id = str(uuid.uuid4())[:8]
                cur.execute(
                    '''
                    INSERT INTO Review (review_id, message, rating, driver_name, client_email)
                    VALUES (%s, %s, %s, %s, %s)
                    ''',
                    (review_id, message, rating, driver_name, client_email)
                )
                conn.commit()
                flash('Review added successfully')
            else:
                flash('Cannot review a driver you have not rented with')
        except psycopg2.Error as e:
            conn.rollback()
            flash(f'Error: {e}')
        finally:
            cur.close()
            conn.close()
    return render_template('add_review.html')

if __name__ == '__main__':
    app.run(debug=True)