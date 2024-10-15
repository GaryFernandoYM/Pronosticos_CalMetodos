# Calculadora de Pronósticos con Flask

Este proyecto es una aplicación web desarrollada con **Flask**, que permite a los usuarios autenticarse y generar pronósticos utilizando diversos métodos de predicción. La aplicación soporta autenticación de usuarios, registro, y varias funcionalidades para calcular pronósticos con diferentes enfoques, además de generar gráficos visuales para los resultados obtenidos.

## Características

- **Autenticación de usuarios**: Registro, inicio de sesión y cierre de sesión utilizando **Flask-Login**.
- **Cálculo de pronósticos**:
  - Pronóstico ingenuo.
  - Pronóstico por media simple.
  - Pronóstico por media móvil.
  - Pronóstico por deriva.
  - Pronóstico ingenuo estacional.
- **Generación de gráficos** para comparar los valores reales y pronósticos.
- **Interfaz de usuario** con plantillas HTML utilizando **Jinja2** para renderizado dinámico.

## Requisitos

Antes de ejecutar la aplicación, asegúrate de tener instalados los siguientes requisitos:

- Python 3.x
- MySQL

### Instalación de dependencias

Puedes instalar manualmente cada una de las dependencias necesarias usando `pip`. Aquí tienes los comandos para instalar las librerías utilizadas en este proyecto:
python3 -m venv .venv
source .venv/bin/activate  # En Windows usa: .venv\Scripts\activate

1. **Crear el .venv para el entorno virtual**:

    ```bash
    python3 -m venv .venv
    ```
1. **Activamos el entorno Virtual**:

    ```bash
    source .venv/bin/activate
    ```
    # En Windows usa: 
    ```bash
    .venv\Scripts\activate
    ```
    
1. **Instalar Flask**:

    ```bash
    pip install Flask
    ```

2. **Instalar Flask-Login**:

    ```bash
    pip install Flask-Login
    ```

3. **Instalar MySQL Connector** para Python:

    ```bash
    pip install mysql-connector-python
    ```

4. **Instalar Werkzeug** (para manejo de seguridad en contraseñas):

    ```bash
    pip install Werkzeug
    ```

5. **Instalar Matplotlib** (para generación de gráficos):

    ```bash
    pip install matplotlib
    ```

6. **Instalar Jinja2** (generalmente viene preinstalado con Flask, pero si no, puedes instalarlo manualmente):

    ```bash
    pip install Jinja2
    ```




### Crear la Base de Datos

Debes crear una base de datos en MySQL para almacenar la información de los usuarios. Ejecuta los siguientes comandos en tu cliente de MySQL:

1. **Crea la base de datos:**

    ```sql
    CREATE DATABASE calculadora;
    ```

2. **Selecciona la base de datos que acabas de crear:**

    ```sql
    USE calculadora;
    ```

3. **Crea la tabla `users` para gestionar el registro y autenticación de usuarios:**

    ```sql
    CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
    );
    ```

### 2. Levantar el Servidor Local


```python
python app.py
