from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
import io
import math
from flask import send_file
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Response

app = Flask(__name__)
app.secret_key = 'mysecretkey'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

auth = Blueprint('auth', __name__)

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

def crear_conexion():
    try:
        conexion = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # Coloca tu contraseña aquí si tienes una
            database='calculadora'  # Asegúrate de que el nombre de tu base de datos sea correcto
        )
        return conexion
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

@login_manager.user_loader
def load_user(user_id):
    conexion = crear_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if user:
        return User(id=user['id'], username=user['username'])
    return None

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        conexion = crear_conexion()
        cursor = conexion.cursor()

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            flash("El usuario ya existe")
            return redirect(url_for('auth.register'))

        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        conexion.commit()
        cursor.close()
        conexion.close()

        flash("Registro exitoso. Ahora puedes iniciar sesión.")
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conexion = crear_conexion()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        cursor.close()
        conexion.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(id=user['id'], username=user['username'])
            login_user(user_obj)
            flash("Inicio de sesión exitoso")
            return redirect(url_for('dashboard'))
        else:
            flash("Nombre de usuario o contraseña incorrectos")
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión")
    return redirect(url_for('auth.login'))

@app.route('/')
@login_required
def dashboard():
    return render_template('index_metodos.html')

@app.route('/pronostico', methods=['GET', 'POST'])
@login_required
def pronostico_ingenuo():
    resultados = []
    total_error_cuadrado = 0
    matriz_generada = False
    num_periodos = 0
    pronostico_proximo_valor = None
    nombre_siguiente_periodo = None
    ecm = None
    recm = None

    if request.method == 'POST':
        try:
            if 'generar_matriz' in request.form:
                num_periodos = int(request.form['num_periodos'])
                matriz_generada = True

            elif 'calcular_pronostico' in request.form:
                num_periodos = int(request.form['num_periodos'])
                periodos = [request.form[f'periodo_{i}'].strip() for i in range(num_periodos)]
                valores = [float(request.form[f'valor_real_{i}']) for i in range(num_periodos)]

                session['valores'] = valores
                session['periodos'] = periodos

                for i in range(num_periodos):
                    valor_real = valores[i]
                    pronostico = valores[i-1] if i > 0 else 'No aplicable (primer período)'
                    error = (valor_real - pronostico) if isinstance(pronostico, float) else 'N/A'
                    error_cuadrado = (error ** 2) if isinstance(error, float) else 'N/A'

                    if isinstance(error_cuadrado, float):
                        total_error_cuadrado += error_cuadrado

                    resultados.append({
                        'periodo': periodos[i],
                        'valor_real': valor_real,
                        'pronostico': pronostico,
                        'error': error,
                        'error_cuadrado': error_cuadrado
                    })

                pronostico_proximo_valor = valores[-1]

                nombre_siguiente_periodo = request.form.get('nombre_siguiente_periodo', 'Siguiente período')

                session['pronostico_proximo_valor'] = pronostico_proximo_valor
                session['nombre_siguiente_periodo'] = nombre_siguiente_periodo

                if num_periodos > 1:
                    ecm = total_error_cuadrado / (num_periodos - 1) if total_error_cuadrado > 0 else 'No disponible'
                    recm = ecm ** 0.5 if isinstance(ecm, float) else 'No disponible'

        except ValueError as ve:
            error_message = f"Error en los datos ingresados: {str(ve)}"
        except Exception as e:
            error_message = f"Ocurrió un error inesperado: {str(e)}"

    return render_template('pronostico.html', 
                           matriz_generada=matriz_generada, 
                           num_periodos=num_periodos, 
                           resultados=resultados, 
                           total_error_cuadrado=total_error_cuadrado, 
                           ecm=ecm, 
                           recm=recm, 
                           pronostico_proximo_valor=pronostico_proximo_valor,
                           nombre_siguiente_periodo=nombre_siguiente_periodo)


@app.route('/graficar')
@login_required
def graficar():
   
    valores = session.get('valores')
    periodos = session.get('periodos')
    pronostico_proximo_valor = session.get('pronostico_proximo_valor')
    nombre_siguiente_periodo = session.get('nombre_siguiente_periodo')

    print(f"Valores: {valores}")
    print(f"Periodos: {periodos}")
    print(f"Pronostico próximo valor: {pronostico_proximo_valor}")
    print(f"Nombre siguiente periodo: {nombre_siguiente_periodo}")

    if not valores or not periodos or pronostico_proximo_valor is None or nombre_siguiente_periodo is None:
        print("Faltan datos para generar el gráfico")
        return "No hay datos suficientes para graficar. Por favor, asegúrate de haber completado todos los pasos.", 400

    try:
        periodos.append(nombre_siguiente_periodo)
        pronosticos = [None] + valores[:-1] + [pronostico_proximo_valor]
        fig, ax = plt.subplots()
        ax.plot(periodos[:-1], valores, label='Valor Real', marker='o')
        ax.plot(periodos, pronosticos, label='Pronóstico', linestyle='--', marker='x')

        ax.set_xlabel('Período')
        ax.set_ylabel('Valores')
        ax.set_title('Valores Reales vs Pronósticos')
        ax.legend()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return Response(img.getvalue(), mimetype='image/png')

    except Exception as e:
        print(f"Error al generar el gráfico: {e}")
        return "Hubo un error al generar el gráfico", 500


@app.route('/pronostico_media', methods=['GET', 'POST'])
@login_required
def pronostico_media():
    resultados = []
    total_error_cuadrado = 0
    matriz_generada = False
    num_periodos = 0
    pronostico_proximo_periodo = None
    nombre_siguiente_periodo = None
    ecm = None
    recm = None
    if request.method == 'POST':
       
        if 'generar_matriz' in request.form:
            num_periodos = int(request.form['num_periodos'])
            matriz_generada = True

        elif 'calcular_pronostico' in request.form:
            num_periodos = int(request.form['num_periodos'])
            periodos = [request.form[f'periodo_{i}'] for i in range(num_periodos)]
            valores = [float(request.form[f'valor_real_{i}']) for i in range(num_periodos)]

            session['valores'] = valores
            session['periodos'] = periodos

            for i in range(num_periodos):
                valor_real = valores[i]
                pronostico = sum(valores[:i]) / i if i > 0 else None
                error = (valor_real - pronostico) if pronostico is not None else None
                error_cuadrado = (error ** 2) if error is not None else None

                if error_cuadrado is not None:
                    total_error_cuadrado += error_cuadrado

                resultados.append({
                    'periodo': periodos[i],
                    'valor_real': valor_real,
                    'pronostico': pronostico if pronostico is not None else '---',
                    'error': error if error is not None else '---',
                    'error_cuadrado': error_cuadrado if error_cuadrado is not None else '---'
                })

            nombre_siguiente_periodo = request.form.get('nombre_siguiente_periodo', f'Periodo {num_periodos + 1}')

            pronostico_proximo_periodo = sum(valores) / len(valores)

            session['pronostico_proximo_periodo'] = pronostico_proximo_periodo
            session['nombre_siguiente_periodo'] = nombre_siguiente_periodo

            if num_periodos > 1:
                ecm = total_error_cuadrado / (num_periodos - 1)
                recm = math.sqrt(ecm)

    if nombre_siguiente_periodo is None:
        nombre_siguiente_periodo = 'Siguiente Período'

    return render_template('pronostico_media.html', 
                           matriz_generada=matriz_generada, 
                           num_periodos=num_periodos, 
                           resultados=resultados, 
                           total_error_cuadrado=total_error_cuadrado, 
                           ecm=ecm, 
                           recm=recm, 
                           pronostico_proximo_periodo=pronostico_proximo_periodo,
                           nombre_siguiente_periodo=nombre_siguiente_periodo)

@app.route('/graficar_media')
@login_required
def graficar_media():
    
    valores = session.get('valores')
    periodos = session.get('periodos')
    pronostico_proximo_periodo = session.get('pronostico_proximo_periodo')
    nombre_siguiente_periodo = session.get('nombre_siguiente_periodo')

    if not valores or not periodos or pronostico_proximo_periodo is None or nombre_siguiente_periodo is None:
        return "No hay datos suficientes para generar el gráfico", 400

    try:
        periodos.append(nombre_siguiente_periodo)
        pronosticos = [None] + [sum(valores[:i]) / i for i in range(1, len(valores))]
        pronosticos.append(pronostico_proximo_periodo)

        fig, ax = plt.subplots()
        ax.plot(periodos[:-1], valores, label='Valor Real', marker='o')
        ax.plot(periodos, pronosticos, label='Pronóstico (Media)', linestyle='--', marker='x')

        ax.set_xlabel('Período')
        ax.set_ylabel('Valores')
        ax.set_title('Valores Reales vs Pronósticos (Media)')
        ax.legend()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return Response(img.getvalue(), mimetype='image/png')

    except Exception as e:
        print(f"Error al generar el gráfico: {e}")
        return "Hubo un error al generar el gráfico", 500

@app.route('/pronostico_media_movil', methods=['GET', 'POST'])
@login_required
def pronostico_media_movil():
    resultados = []
    total_error_cuadrado = 0
    matriz_generada = False
    num_periodos = 0
    ventana = None
    pronostico_proximo_periodo = None
    nombre_siguiente_periodo = None
    ecm = None
    recm = None

    if request.method == 'POST':
        if 'generar_matriz' in request.form:
            num_periodos = int(request.form['num_periodos'])
            ventana = int(request.form['ventana'])
            matriz_generada = True

        elif 'calcular_pronostico' in request.form:
            num_periodos = int(request.form['num_periodos'])
            ventana = int(request.form['ventana'])  
            periodos = [request.form[f'periodo_{i}'] for i in range(num_periodos)]
            valores = [float(request.form[f'valor_real_{i}']) for i in range(num_periodos)]

            nombre_siguiente_periodo = request.form.get('nombre_siguiente_periodo', f'Período {num_periodos + 1}')

            session['valores'] = valores
            session['periodos'] = periodos
            session['ventana'] = ventana

            for i in range(num_periodos):
                valor_real = valores[i]
                if i >= ventana:
                    pronostico = sum(valores[i-ventana:i]) / ventana
                else:
                    pronostico = None

                error = (valor_real - pronostico) if pronostico is not None else None
                error_cuadrado = (error ** 2) if error is not None else None

                if error_cuadrado is not None:
                    total_error_cuadrado += error_cuadrado

                resultados.append({
                    'periodo': periodos[i],
                    'valor_real': valor_real,
                    'pronostico': pronostico if pronostico is not None else '---',
                    'error': error if error is not None else '---',
                    'error_cuadrado': error_cuadrado if error_cuadrado is not None else '---'
                })

            if num_periodos >= ventana:
                pronostico_proximo_periodo = sum(valores[-ventana:]) / ventana
                session['pronostico_proximo_periodo'] = pronostico_proximo_periodo

            if num_periodos > ventana:
                ecm = total_error_cuadrado / (num_periodos - ventana)
                recm = math.sqrt(ecm)

    return render_template('pronostico_media_movil.html', 
                           matriz_generada=matriz_generada, 
                           num_periodos=num_periodos, 
                           ventana=ventana, 
                           resultados=resultados, 
                           total_error_cuadrado=total_error_cuadrado, 
                           ecm=ecm, 
                           recm=recm, 
                           pronostico_proximo_periodo=pronostico_proximo_periodo,
                           nombre_siguiente_periodo=nombre_siguiente_periodo)


@app.route('/graficar_media_movil')
@login_required
def graficar_media_movil():
    valores = session.get('valores')
    periodos = session.get('periodos')
    pronostico_proximo_periodo = session.get('pronostico_proximo_periodo')
    ventana = session.get('ventana')

    if not valores or not periodos or not pronostico_proximo_periodo or not ventana:
        return "No hay datos suficientes o la ventana no está definida", 400

    if not isinstance(ventana, int):
        return "La ventana debe ser un número entero", 400

    
    pronosticos = [None] * ventana
    for i in range(ventana, len(valores)):
        pronosticos.append(sum(valores[i-ventana:i]) / ventana)
    
    periodos.append(f'Pronóstico (Período {len(valores) + 1})')
    valores.append(None)
    pronosticos.append(pronostico_proximo_periodo)

    fig, ax = plt.subplots()
    
    ax.plot(periodos[:len(valores) - 1], valores[:-1], label='Valor Real', marker='o', color='blue')
    
    ax.plot(periodos[ventana:], pronosticos[ventana:], label='Pronóstico (Media Móvil)', linestyle='--', marker='x', color='red')

    ax.set_xlabel('Período')
    ax.set_ylabel('Valores')
    ax.set_title('Valores Reales vs Pronósticos (Media Móvil)')
    ax.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype='image/png')



@app.route('/pronostico_deriva', methods=['GET', 'POST'])
@login_required
def pronostico_deriva():
    resultados = []
    total_error_cuadrado = 0
    matriz_generada = False
    num_periodos = 0
    pronostico_proximo_periodo = None
    ecm = None
    recm = None

    h = 1
    nombre_siguiente_periodo = None

    if request.method == 'POST':
        
        if 'horizonte' in request.form:
            h = int(request.form.get('horizonte', 1))

        if 'generar_matriz' in request.form:
            num_periodos = int(request.form['num_periodos'])
            matriz_generada = True

        elif 'calcular_pronostico' in request.form:
            num_periodos = int(request.form['num_periodos'])
            periodos = [request.form[f'periodo_{i}'] for i in range(num_periodos)]
            valores = [float(request.form[f'valor_real_{i}']) for i in range(num_periodos)]

            nombre_siguiente_periodo = request.form.get('nombre_siguiente_periodo', f'Período {num_periodos + 1}')

            session['valores'] = valores
            session['periodos'] = periodos
            session['horizonte'] = h
            session['nombre_siguiente_periodo'] = nombre_siguiente_periodo

            for i in range(num_periodos):
                valor_real = valores[i]
                if i > 0:
                    T = i + 1
                    pronostico = valores[i - 1] + h * (valores[i - 1] - valores[0]) / (T - 1)
                else:
                    pronostico = None

                error = (valor_real - pronostico) if pronostico is not None else None
                error_cuadrado = (error ** 2) if error is not None else None

                if error_cuadrado is not None:
                    total_error_cuadrado += error_cuadrado

                resultados.append({
                    'periodo': periodos[i],
                    'valor_real': valor_real,
                    'pronostico': round(pronostico, 2) if pronostico is not None else '---',
                    'error': round(error, 2) if error is not None else '---',
                    'error_cuadrado': round(error_cuadrado, 2) if error_cuadrado is not None else '---'
                })

            T = len(valores)
            pronostico_proximo_periodo = valores[-1] + h * (valores[-1] - valores[0]) / (T - 1)

            if num_periodos > 1:
                ecm = total_error_cuadrado / (num_periodos - 1)
                recm = math.sqrt(ecm)

            session['pronostico_proximo_periodo'] = pronostico_proximo_periodo

    return render_template('pronostico_deriva.html', 
                           matriz_generada=matriz_generada, 
                           num_periodos=num_periodos, 
                           resultados=resultados, 
                           total_error_cuadrado=total_error_cuadrado, 
                           ecm=ecm, 
                           recm=recm, 
                           pronostico_proximo_periodo=round(pronostico_proximo_periodo, 2) if pronostico_proximo_periodo else None,
                           nombre_siguiente_periodo=nombre_siguiente_periodo,
                           horizonte=h)


@app.route('/graficar_deriva')
@login_required
def graficar_deriva():
    valores = session.get('valores')
    periodos = session.get('periodos')
    pronostico_proximo_periodo = session.get('pronostico_proximo_periodo')
    h = session.get('horizonte', 1)

    nombre_siguiente_periodo = session.get('nombre_siguiente_periodo', f'Período {len(valores) + h}')

    if not valores or not periodos or pronostico_proximo_periodo is None:
        return "No hay datos suficientes para generar el gráfico", 400

    periodos.append(nombre_siguiente_periodo)
    valores.append(None)

    fig, ax = plt.subplots()

    ax.plot(periodos[:len(valores) - 1], valores[:-1], label='Valor Real', marker='o', color='blue')

    ax.plot(periodos[-2:], [valores[-2], pronostico_proximo_periodo], label=f'Pronóstico para {nombre_siguiente_periodo}', linestyle='--', marker='x', color='red')

    ax.set_xlabel('Periodo')
    ax.set_ylabel('Valores')
    ax.set_title(f'Valores Reales vs Pronóstico ({nombre_siguiente_periodo})')
    ax.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return Response(img.getvalue(), mimetype='image/png')



@app.route('/pronostico_ingenuo_estacional', methods=['GET', 'POST'])
@login_required
def pronostico_ingenuo_estacional():
    resultados = []
    total_error_cuadrado = 0
    matriz_generada = False
    num_periodos = 0
    frecuencia_estacional = 7
    pronostico_proximo_periodo = None
    ecm = None
    recm = None
    nombre_siguiente_periodo = None

    if request.method == 'POST':
        if 'generar_matriz' in request.form:
            num_periodos = int(request.form['num_periodos'])
            frecuencia_estacional = int(request.form.get('frecuencia_estacional', 7))
            matriz_generada = True

        elif 'calcular_pronostico' in request.form:
            num_periodos = int(request.form['num_periodos'])
            frecuencia_estacional = int(request.form.get('frecuencia_estacional', 7))
            periodos = [request.form[f'periodo_{i}'] for i in range(num_periodos)]
            valores = [float(request.form[f'valor_real_{i}']) for i in range(num_periodos)]

            nombre_siguiente_periodo = request.form.get('nombre_siguiente_periodo', f'Período {num_periodos + 1}')

            session['valores'] = valores
            session['periodos'] = periodos
            session['frecuencia_estacional'] = frecuencia_estacional
            session['nombre_siguiente_periodo'] = nombre_siguiente_periodo

            for i in range(num_periodos):
                valor_real = valores[i]
                if i >= frecuencia_estacional:
                    pronostico = valores[i - frecuencia_estacional]
                else:
                    pronostico = None

                error = (valor_real - pronostico) if pronostico is not None else None
                error_cuadrado = (error ** 2) if error is not None else None

                if error_cuadrado is not None:
                    total_error_cuadrado += error_cuadrado

                resultados.append({
                    'periodo': periodos[i],
                    'valor_real': valor_real,
                    'pronostico': pronostico if pronostico is not None else '---',
                    'error': error if error is not None else '---',
                    'error_cuadrado': error_cuadrado if error_cuadrado is not None else '---'
                })

            if len(valores) >= frecuencia_estacional:
                pronostico_proximo_periodo = valores[-frecuencia_estacional]
            else:
                pronostico_proximo_periodo = None

            if num_periodos > frecuencia_estacional:
                ecm = total_error_cuadrado / (num_periodos - frecuencia_estacional)
                recm = math.sqrt(ecm)

    return render_template('pronostico_ingenuo_estacional.html', 
                           matriz_generada=matriz_generada, 
                           num_periodos=num_periodos, 
                           resultados=resultados, 
                           total_error_cuadrado=total_error_cuadrado, 
                           ecm=ecm, 
                           recm=recm, 
                           pronostico_proximo_periodo=pronostico_proximo_periodo,
                           frecuencia_estacional=frecuencia_estacional,
                           nombre_siguiente_periodo=nombre_siguiente_periodo)

@app.route('/graficar_ingenuo_estacional')
@login_required
def graficar_ingenuo_estacional():
    valores = session.get('valores')
    periodos = session.get('periodos')
    pronostico_proximo_periodo = session.get('pronostico_proximo_periodo')
    nombre_siguiente_periodo = session.get('nombre_siguiente_periodo')

    if not valores or not periodos or pronostico_proximo_periodo is None or nombre_siguiente_periodo is None:
        return "No hay datos suficientes para generar el gráfico", 400

    periodos.append(nombre_siguiente_periodo)
    valores.append(None)
    
    fig, ax = plt.subplots()
    
    ax.plot(periodos[:-1], valores[:-1], label='Valor Real', marker='o', color='blue')
    
    ax.plot([periodos[-2], periodos[-1]], [valores[-2], pronostico_proximo_periodo], label=f'Pronóstico ({nombre_siguiente_periodo})', linestyle='--', marker='x', color='red')

    ax.set_xlabel('Período')
    ax.set_ylabel('Valor')
    ax.set_title(f'Pronóstico Ingenuo Estacional - {nombre_siguiente_periodo}')
    ax.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')


@app.route('/index_metodos')
@login_required
def index_metodos():
    return render_template('index_metodos.html') 

app.register_blueprint(auth, url_prefix='/auth')


if __name__ == '__main__':
    app.run(debug=True)
