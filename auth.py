from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

# Crear el Blueprint de autenticación
auth = Blueprint('auth', __name__)

# Función para crear la conexión a la base de datos
def crear_conexion():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Coloca tu contraseña de MySQL aquí
            database='web_scraping_db'  # Asegúrate de que el nombre de tu base de datos sea correcto
        )
        return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

# Modelo de usuario
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Ruta de login
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Conexión a la base de datos para verificar credenciales
        conexion = crear_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        # Validación del usuario y la contraseña
        if user and check_password_hash(user['password'], password):
            user_obj = User(id=user['id'], username=user['username'])
            login_user(user_obj)
            flash("Inicio de sesión exitoso")
            return redirect(url_for('dashboard'))  # Redirigir al dashboard después del login
        else:
            flash("Nombre de usuario o contraseña incorrectos")
            return redirect(url_for('auth.login'))

    return render_template('login.html')

# Ruta de registro
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Conexión a la base de datos
        conexion = crear_conexion()
        cursor = conexion.cursor()

        # Verificar si el usuario ya existe
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            flash("El usuario ya existe")
            return redirect(url_for('auth.register'))

        # Registrar al nuevo usuario
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

# Ruta de logout
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión")
    return redirect(url_for('auth.login'))

# Ruta de la calculadora de pronóstico
@auth.route('/pronostico', methods=['GET', 'POST'])
@login_required
def pronostico_ingenuo():
    pronostico = None
    datos_ingresados = []

    if request.method == 'POST':
        datos = request.form['datos']
        if datos:
            try:
                datos_ingresados = list(map(float, datos.split(',')))
                if datos_ingresados:
                    pronostico = datos_ingresados[-1]  # Método ingenuo: último valor
            except ValueError:
                flash("Por favor, ingrese números válidos separados por comas.")

    return render_template('pronostico.html', pronostico=pronostico, datos_ingresados=datos_ingresados)

