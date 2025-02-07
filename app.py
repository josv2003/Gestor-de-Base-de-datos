from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_session import Session
from datetime import datetime
from functools import wraps
from io import BytesIO
import pandas as pd
import pyodbc
import json
import webbrowser

app = Flask(__name__)
app.secret_key = 'segura'

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

usuarios = {
    'admin_user': {'password': 'admin123', "role": "admin"},
    'editor_user': {'password': 'editor123', "role": "editor"},
    'viewer_user': {'password': 'viewer123', "role": "visualizador"}
}

# Configuración de la base de datos (SQL Server)
DB_CONFIG = {
    'DRIVER': '{SQL Server}',
    'SERVER': 'SRVSAP01',    #nombre o IP del servidor
    'DATABASE': 'idea_db',      #nombre base de datos
    'UID': 'sa',        #Usuario de SQL Server
    'PWD': 'Seidor2015'      #Contraseña
}

def get_connection():
    """Arma la cadena de conexión y retorna una conexion pyodbc"""

    conn_str = (
        f"DRIVER={DB_CONFIG['DRIVER']};"
        f"SERVER={DB_CONFIG['SERVER']};"
        f"DATABASE={DB_CONFIG['DATABASE']};"
        f"UID={DB_CONFIG['UID']};"
        f"PWD={DB_CONFIG['PWD']};"
    )

    return pyodbc.connect(conn_str)

def row_to_disc_list(cursor):
    """COnvierte las filas del cursor en una lista de diccionarios"""

    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]
#================================================================================================
# MODELO DE USUARIO
#================================================================================================
class Usuario(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    if user_id in usuarios:
        user_info = usuarios[user_id]
        return Usuario(user_id, user_info["role"])
    return None

#================================================================================================
# CONTROL ACCESO A RUTAS
#================================================================================================
def roles_required(roles):
    """
    Permite el acceso a las rutas solo si el usuario tiene uno de los roles especificados.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Debes iniciar sesión para acceder a esta sección.', 'warning')
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('No tienes permisos para acceder a esta sección.', 'danger')
                redirect(url_for('dashboard'))    
            return f(*args, **kwargs)
        return decorated_function
    return decorator

#================================================================================================
# FUNCIONES EXTRAS
#================================================================================================
def obtener_nombre_columnas(tabla):
    QUERY_OBTENER_COLUMNAS = f"""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ? AND TABLE_SCHEMA = 'dbo' 
        ORDER BY ORDINAL_POSITION;
    """
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute(QUERY_OBTENER_COLUMNAS, (tabla,))
    columnas_cursor = cursor.fetchall()
    columnas = [str(columna[0]) for columna in columnas_cursor]
    
    cursor.close()
    connection.close()
    return columnas

def actualizar_historial_de_cambios(valores, cursor):
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    usuario = session["username"]
    QUERY_INSERTAR_CAMBIO = f"""
        INSERT INTO historial_de_cambios 
        (usuario, fecha, tipo, tabla_afectada, ID_afectado, columna_afectada) 
        VALUES (?, ?, ?, ?, ?, ?);
    """
    nuevos_valores = [usuario, fecha] + valores
    cursor.execute(QUERY_INSERTAR_CAMBIO, nuevos_valores)

def arreglar_campo(campo):
    campo_sin_espacios = campo.strip().replace(" ", "_").replace("-", "_").replace(")", "").replace("(", "").lower()
    return campo_sin_espacios.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
#================================================================================================
# RUTAS
#================================================================================================
@app.route('/')
def index():
    if current_user.is_authenticated:
        tablas = ['empresas', 'personas','equipos'] 
        return render_template('index.html', tablas=tablas)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in usuarios and usuarios[username]['password'] == password:
            user_role = usuarios[username]["role"]
            user = Usuario(username, user_role)
            login_user(user)
            session["role"] = user_role # Guardar el rol en la sesión
            session["username"] = username
            flash('Inicio de sesión exitoso.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop("role", None) # Eliminar el rol de la sesión
    flash('Sesión cerrada correctamente.', 'info')
    return redirect(url_for('login'))

# Rutas usadas en el frontend
@app.route('/get_columns', methods=['POST'])
@login_required
def get_columns():
    tabla = request.json.get('tabla')
    columnas = obtener_nombre_columnas(tabla)
    return jsonify(columnas)

@app.route('/get_type', methods=['POST'])
@login_required
def get_type():
    tabla = request.json.get('tabla')
    columna = request.json.get('columna')

    connection = get_connection()
    cursor = connection.cursor()
    
    query_tipo = """
        SELECT DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = ? AND COLUMN_NAME = ?;
    """
    cursor.execute(query_tipo, (tabla, columna))
    tipo = cursor.fetchone()[0]

    cursor.close()
    connection.close()
    
    return jsonify(tipo)

# Subir y procesar archivo Excel (solo admin y editor)
@app.route('/upload', methods=['POST'])
@login_required
@roles_required(['admin', 'editor'])
def upload():
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo.')
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash('El archivo no tiene nombre.')
        return redirect(url_for('index'))

    try:
        # Obtener el nombre de la hoja desde el formulario
        tabla_destino = request.form['tabla']  # Cambiar a tu tabla

        # Conectar a la base de datos
        connection = get_connection()
        cursor = connection.cursor()

        if tabla_destino == 'todas':
            dfs = pd.read_excel(file, sheet_name=None, header=1)
            for sheet_name, df in dfs.items():
                # Limpiar nombres de columnas
                df = df.iloc[:, 1:]
                df.columns = [col.strip().replace(" ", "_").replace("-", "_").replace(")", "").replace("(", "") for col in df.columns]
                
                # Preparar consulta de inserción
                columnas = ', '.join([f"[{col}]" for col in df.columns])
                valores = ', '.join(['?' for _ in df.columns])
                insert_query = f"INSERT INTO [{sheet_name}] ({columnas}) VALUES ({valores})"
                
                # Insertar datos
                for _, row in df.iterrows():
                    row_values = [None if pd.isna(value) else value for value in row]
                    cursor.execute(insert_query, tuple(row_values))
        else:
        
            # Leer archivo Excel
            df = pd.read_excel(file, sheet_name=tabla_destino, header=1).iloc[:, 1:]
            df.columns = [col.strip().replace(" ", "_").replace("-", "_").replace(")", "").replace("(", "") for col in df.columns]

            # Preparar consulta de inserción
            columnas = ', '.join([f"[{col}]" for col in df.columns])
            valores = ', '.join(['?' for _ in df.columns])
            insert_query = f"INSERT INTO [{tabla_destino}] ({columnas}) VALUES ({valores})"

            # Insertar datos
            for _, row in df.iterrows():
                row_values = [None if pd.isna(value) else value for value in row]
                cursor.execute(insert_query, tuple(row_values))

        # Actualizar historial de cambios
        valores_historial = ['Cargar datos excel', f'{tabla_destino}', None, None]
        actualizar_historial_de_cambios(valores_historial, cursor)

        connection.commit()
        flash('Datos insertados correctamente.')

    except Exception as e:
        flash(f'Error al procesar el archivo: {e}')

    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/download', methods=['POST'])
@login_required
def download():
    table_name = request.form['tabla']
    try:
        connection = get_connection()

        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')

        if table_name ==  'todas':
            tablas_db = ['empresas', 'personas', 'equipos']

            for tabla in tablas_db:
                query = f"SELECT * FROM [{tabla}]"
                df = pd.read_sql(query, connection)
                df.to_excel(writer, sheet_name=tabla, index=False)
        else:    
            query = f"SELECT * FROM [{table_name}];"
            df = pd.read_sql(query, connection)
            df.to_excel(writer, sheet_name=table_name, index=False)

        writer.close()
        output.seek(0)

        filename = f"{'backup_db' if table_name == 'todas' else table_name}.xlsx"

        return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    except Exception as e:
        flash(f'Error al descargar archivo: {e}')
    finally:
        try:
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/download_search', methods=['POST'])
@login_required
def download_search():
    results_json = session.get('search_results')
    if not results_json:
        flash("No se encontraron resultados guardados para descargar")
        return redirect(url_for('index'))
    try:
        results = json.loads(results_json)
    except Exception as e:
        flash(f'Error al procesar los resultados: {e}')
        return redirect(url_for('index'))
    
    df = pd.DataFrame(results)
    if df.empty:
        flash("No hay resultados para descargar.")
        return redirect(url_for('index'))
    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='openpyxl')
    sheet_name = request.form.get('selected_table', 'Resultados')
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    writer.close()
    output.seek(0)

    filename = f"Busqueda_{sheet_name}.xlsx"

    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# Buscar datos
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    results = []
    search_params = {}
    if request.method == 'POST':
        selected_table = request.form['search-table']
        columna = request.form['search-column'].replace(" ", "_").lower()
        search_query = request.form['query']
        type_query = request.form['input-type']

        search_params = {
            'selected_table': selected_table,
            'columna': columna,
            'query': search_query,
            'type': type_query
        }
        
        try:
            connection = get_connection()
            cursor = connection.cursor()
            
            if type_query == 'text':
                query = f"SELECT * FROM [{selected_table}] WHERE [{columna}] LIKE ?"
                cursor.execute(query, (f"%{search_query}%",))
            elif type_query == 'number':
                query = f"SELECT * FROM [{selected_table}] WHERE [{columna}] = ?"
                cursor.execute(query, (search_query,))
            elif columna == 'historial':
                query = f"SELECT * FROM historial_de_mantenimientos WHERE ID_equipo = ?"
                cursor.execute(query, (search_query,))
            else:
                query = f"SELECT * FROM [{selected_table}] WHERE [{columna}] = ?"
                cursor.execute(query, (search_query,))
            
            results = row_to_disc_list(cursor)
            #Guarda los resultados en la sesion (convertidos en JSON)
            session['search_results'] = json.dumps(results, default=str)

        except Exception as e:
            flash(f'Error al buscar: {e}')

        finally:
            try:
                cursor.close()
                connection.close()
            except:
                pass

    columnas = obtener_nombre_columnas(search_params.get('selected_table', '')) if search_params.get('selected_table') else []
    
    return render_template('resultados.html', results=results, columnas=columnas, search_params=search_params)

@app.route('/historial', methods=['POST'])
@login_required
@roles_required(['admin'])
def historial():
    results = []
    columnas = obtener_nombre_columnas('historial_de_cambios')
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        
        query = "SELECT * FROM historial_de_cambios"
        cursor.execute(query)
        results = row_to_disc_list(cursor)
    except Exception as e:
        flash(f'Error al obtener el historial: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return render_template('resultados.html', results=results, columnas=columnas)

@app.route('/historial_maquina', methods=['POST'])
@login_required
def historial_maquina():
    results = []
    columnas = obtener_nombre_columnas('historial_de_maquinas')
    ID_maquina = request.form['query']
    try:
        connection = get_connection()
        cursor = connection.cursor()
        
        query = f"SELECT * FROM historial_de_maquinas WHERE ID_equipo = ?"
        cursor.execute(query, (ID_maquina,))
        results = row_to_disc_list(cursor)

    except Exception as e:
        flash(f'Error al obtener el historial: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return render_template('resultados.html', results=results, columnas=columnas)

@app.route('/insertar_campo', methods=['POST'])
@login_required
@roles_required(['admin'])
def insertar_campo():
    tabla = request.form['insert-table']
    campo = arreglar_campo(request.form['insert-data'])
    tipo = request.form['insert-type']

    try:
        connection = get_connection()
        cursor = connection.cursor()
        if tipo == 'text':
            tipo = 'VARCHAR(255)'
        elif tipo == 'number':
            tipo = 'INT'
        elif tipo == 'date':
            tipo = 'DATE'
        elif tipo == 'datetime':
            tipo = 'DATETIME'
        elif tipo == 'Booleano':
            tipo = 'BOOLEAN'
        elif tipo == 'decimal':
            tipo = 'DECIMAL(10, 2)'

        query = f"ALTER TABLE [{tabla}] ADD [{campo}] {tipo};"
        cursor.execute(query)
        
        #actualizar historial de cambios
        valores_historial = ['Insertar nuevo campo', f'{tabla}', None, campo]
        actualizar_historial_de_cambios(valores_historial, cursor)
        
        connection.commit()
        flash('Campo insertado correctamente.')
    except Exception as e:
        flash(f'Error al insertar campo: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/eliminar_campo', methods=['POST'])
@login_required
@roles_required(['admin'])
def eliminar_campo():
    tabla = request.form['delete-table']
    campo = arreglar_campo(request.form['delete-column'])

    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = f"ALTER TABLE [{tabla}] DROP COLUMN [{campo}];"
        cursor.execute(query)
        
        #actualizar historial de cambios
        valores_historial = ['Eliminar campo', f'{tabla}', None, campo]
        actualizar_historial_de_cambios(valores_historial, cursor)
        
        connection.commit()
        flash('Campo eliminado correctamente.')
    except Exception as e:
        flash(f'Error al eliminar campo: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/insertar_registro', methods=['POST'])
@login_required
@roles_required(['admin', 'editor'])
def insertar_registro():
    tabla = request.form['insert-element-table']
    columnas = obtener_nombre_columnas(tabla)
    columnas_insertadas = []
    valores_insertados = []
    for col in columnas:
        valor = request.form[col]
        if valor != '':
            valores_insertados.append(valor)
            columnas_insertadas.append(col)
    # valores = [request.form[col] for col in columnas]
    try:
        connection = get_connection()
        cursor = connection.cursor()

        columnas = ', '.join([f"[{col}]" for col in columnas_insertadas])
        valores = ', '.join(['?' for _ in valores_insertados])
        query = f"INSERT INTO [{tabla}] ({columnas}) VALUES ({valores});"

        cursor.execute(query, tuple(valores_insertados))
        
        #actualizar historial de cambios
        cursor.execute("SELECT SCOPE_IDENTITY();")
        last_id = cursor.fetchone()[0]
        valores_historial = ['Insertar nuevo registro', f'{tabla}', last_id, None] #!!!!! ver si se puede obtener el id del registro
        actualizar_historial_de_cambios(valores_historial, cursor)

        connection.commit()
        flash('Registro insertado correctamente.')
    except Exception as e:
        flash(f'Error al insertar registro: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/eliminar_registro', methods=['POST'])
@login_required
@roles_required(['admin', 'editor'])
def eliminar_registro():
    tabla = request.form['delete-element-table']
    id_registro = request.form['delete-element-id']
    id_columna = obtener_nombre_columnas(tabla)[0]
    try:
        connection = get_connection()
        cursor = connection.cursor()

        query = f"DELETE FROM [{tabla}] WHERE [{id_columna}] = ?;"
        cursor.execute(query, (id_registro,))

        #actualizar historial de cambios
        valores_historial = ['Eliminar registro', f'{tabla}', id_registro, None]
        actualizar_historial_de_cambios(valores_historial, cursor)

        connection.commit()
        flash('Registro eliminado correctamente.')
    except Exception as e:
        flash(f'Error al eliminar registro: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

@app.route('/actualizar_registro', methods=['POST'])
@login_required
@roles_required(['admin', 'editor'])
def actualizar_registro():
    tabla = request.form['update-element-table']
    columnas = obtener_nombre_columnas(tabla)[1:]
    columnas_actualizadas = []
    valores_actualizados = []
    for col in columnas:
        valor = request.form[col]
        if valor != '':
            valores_actualizados.append(valor)
            columnas_actualizadas.append(col)
    id_registro = request.form['update-element-id']
    id_columna = obtener_nombre_columnas(tabla)[0]
    try:
        connection = get_connection()
        cursor = connection.cursor()

        sets = ', '.join([f"[{col}] = ?" for col in columnas_actualizadas])
        query = f"UPDATE [{tabla}] SET {sets} WHERE [{id_columna}] = ?;"
        parametros = tuple(valores_actualizados) + (id_registro,)
        cursor.execute(query, parametros)
        
        #actualizar historial de cambios
        valores_historial = ['Actualizar registro', f'{tabla}', id_registro, f'{tuple(columnas_actualizadas)}']
        actualizar_historial_de_cambios(valores_historial, cursor)

        connection.commit()
        flash('Registro actualizado correctamente.')
    except Exception as e:
        flash(f'Error al actualizar registro: {e}')
    finally:
        try:
            cursor.close()
            connection.close()
        except:
            pass
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = 5000
    url =f"http://127.0.0.1:{port}"
    webbrowser.open(url)
    app.run(debug=False, port=port)
