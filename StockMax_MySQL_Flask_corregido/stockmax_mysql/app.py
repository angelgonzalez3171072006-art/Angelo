import os
from decimal import Decimal
from functools import wraps
from flask import Flask, render_template, request, jsonify, session
from werkzeug.security import check_password_hash
from stockmax_utils import money
import mysql.connector
from mysql.connector import pooling, Error

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(32)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'stockmax_user'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'stockmax'),
    'charset': 'utf8mb4',
    'use_unicode': True,
}
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(pool_name='stockmax_pool', pool_size=5, **DB_CONFIG)
    return _pool

def query(sql, params=(), fetch='all', commit=False):
    conn = get_pool().get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, params)
        if commit:
            conn.commit()
            return cur.lastrowid
        if fetch == 'one':
            return cur.fetchone()
        if fetch == 'none':
            return None
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def api_login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Debes iniciar sesión.'}), 401
        return fn(*args, **kwargs)
    return wrapped

def role_required(*roles):
    def deco(fn):
        @wraps(fn)
        @api_login_required
        def wrapped(*args, **kwargs):
            if session.get('role') not in roles:
                return jsonify({'error': 'No tienes permiso para esta acción.'}), 403
            return fn(*args, **kwargs)
        return wrapped
    return deco

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/api/session')
def current_session():
    if 'user_id' not in session:
        return jsonify({'authenticated': False})
    return jsonify({'authenticated': True, 'user': {'id': session['user_id'], 'username': session['username'], 'role': session['role']}})

@app.post('/api/login')
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip().lower()
    password = str(data.get('password', ''))
    user = query('SELECT id, username, password_hash, role, active FROM users WHERE username=%s LIMIT 1', (username,), fetch='one')
    if not user or not user['active'] or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Usuario o contraseña incorrectos.'}), 401
    session.clear()
    session.update(user_id=user['id'], username=user['username'], role=user['role'])
    return jsonify({'ok': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})

@app.post('/api/logout')
def logout():
    session.clear()
    return jsonify({'ok': True})

@app.get('/api/categories')
@api_login_required
def categories():
    return jsonify(query('SELECT id, name FROM categories ORDER BY name'))

@app.get('/api/products')
@api_login_required
def products():
    rows = query('''SELECT p.id,p.name,p.description,p.price,p.stock,p.expiry_date,c.id AS category_id,c.name AS category
                    FROM products p JOIN categories c ON c.id=p.category_id WHERE p.active=1 ORDER BY p.name''')
    for p in rows:
        p['price'] = float(p['price'])
        p['expiry_date'] = p['expiry_date'].isoformat() if p['expiry_date'] else None
    return jsonify(rows)

@app.post('/api/products')
@role_required('dueno')
def create_product():
    data = request.get_json(silent=True) or {}
    name = str(data.get('name', '')).strip()
    try:
        price = money(data.get('price'))
        stock = int(data.get('stock', 0))
        category_id = int(data.get('category_id'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Revisa precio, existencia y categoría.'}), 400
    if not name or stock < 0:
        return jsonify({'error': 'El nombre es obligatorio y la existencia no puede ser negativa.'}), 400
    try:
        pid = query('INSERT INTO products(name,description,price,stock,category_id,expiry_date,active) VALUES(%s,%s,%s,%s,%s,%s,1)',
                    (name, str(data.get('description','')).strip(), price, stock, category_id, data.get('expiry_date') or None), commit=True)
        if stock:
            query('INSERT INTO inventory_movements(product_id,user_id,movement_type,quantity,reason) VALUES(%s,%s,\'entrada\',%s,\'Existencia inicial\')', (pid,session['user_id'],stock), commit=True)
        return jsonify({'ok': True, 'id': pid}), 201
    except Error as e:
        return jsonify({'error': 'No se pudo guardar el producto. Verifica que la categoría exista.'}), 400

@app.post('/api/movements')
@role_required('dueno')
def create_movement():
    data = request.get_json(silent=True) or {}
    try:
        pid, qty = int(data.get('product_id')), int(data.get('quantity'))
    except (ValueError, TypeError):
        return jsonify({'error': 'Producto y cantidad deben ser válidos.'}), 400
    kind = data.get('type')
    if kind not in ('entrada','salida') or qty <= 0:
        return jsonify({'error': 'Tipo o cantidad inválidos.'}), 400
    conn = get_pool().get_connection(); cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute('SELECT stock FROM products WHERE id=%s AND active=1 FOR UPDATE', (pid,)); product = cur.fetchone()
        if not product:
            conn.rollback(); return jsonify({'error':'Producto no encontrado.'}), 404
        if kind == 'salida' and qty > product['stock']:
            conn.rollback(); return jsonify({'error':f"Existencia insuficiente. Disponible: {product['stock']}"}), 400
        delta = qty if kind == 'entrada' else -qty
        cur.execute('UPDATE products SET stock=stock+%s WHERE id=%s', (delta,pid))
        cur.execute('INSERT INTO inventory_movements(product_id,user_id,movement_type,quantity,reason) VALUES(%s,%s,%s,%s,%s)', (pid,session['user_id'],kind,qty,str(data.get('reason','Movimiento manual')).strip()))
        conn.commit()
        return jsonify({'ok':True})
    except Error:
        conn.rollback(); return jsonify({'error':'No se pudo registrar el movimiento.'}), 500
    finally:
        cur.close(); conn.close()

@app.get('/api/movements')
@role_required('dueno')
def movements():
    rows = query('''SELECT m.id,m.movement_type AS type,m.quantity,m.reason,m.created_at,p.name AS product,u.username
                    FROM inventory_movements m JOIN products p ON p.id=m.product_id JOIN users u ON u.id=m.user_id
                    ORDER BY m.created_at DESC LIMIT 300''')
    for r in rows: r['created_at'] = r['created_at'].isoformat(sep=' ', timespec='seconds')
    return jsonify(rows)

def create_sale(items, user_id, sale_type):
    if not isinstance(items, list) or not items:
        raise ValueError('Agrega al menos un producto a la venta.')
    normalized = {}
    for item in items:
        try: pid, qty = int(item.get('product_id')), int(item.get('quantity'))
        except (ValueError, TypeError, AttributeError): raise ValueError('Hay un producto o cantidad inválidos.')
        if qty < 1: raise ValueError('La cantidad debe ser mayor que cero.')
        normalized[pid] = normalized.get(pid, 0) + qty
    conn = get_pool().get_connection(); cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        product_rows = {}
        total = Decimal('0.00')
        for pid, qty in normalized.items():
            cur.execute('SELECT id,name,price,stock FROM products WHERE id=%s AND active=1 FOR UPDATE', (pid,))
            p = cur.fetchone()
            if not p: raise ValueError(f'El producto {pid} no existe.')
            if p['stock'] < qty: raise ValueError(f"Stock insuficiente para {p['name']}. Disponible: {p['stock']}.")
            product_rows[pid] = (p, qty)
            total += p['price'] * qty
        cur.execute('INSERT INTO sales(user_id,sale_type,total,status) VALUES(%s,%s,%s,\'completada\')', (user_id,sale_type,total))
        sale_id = cur.lastrowid
        for pid, (p, qty) in product_rows.items():
            cur.execute('INSERT INTO sale_items(sale_id,product_id,quantity,unit_price,subtotal) VALUES(%s,%s,%s,%s,%s)', (sale_id,pid,qty,p['price'],p['price']*qty))
            cur.execute('UPDATE products SET stock=stock-%s WHERE id=%s', (qty,pid))
            cur.execute('INSERT INTO inventory_movements(product_id,user_id,movement_type,quantity,reason,sale_id) VALUES(%s,%s,\'salida\',%s,%s,%s)', (pid,user_id,qty,'Venta '+sale_type,sale_id))
        conn.commit()
        return {'ok':True,'sale_id':sale_id,'total':float(total)}
    except Exception:
        conn.rollback(); raise
    finally:
        cur.close(); conn.close()

@app.post('/api/sales')
@api_login_required
def sales():
    role = session['role']
    if role not in ('cliente','cajero','dueno'):
        return jsonify({'error':'No tienes permiso para vender.'}), 403
    data = request.get_json(silent=True) or {}
    try:
        return jsonify(create_sale(data.get('items'), session['user_id'], 'caja' if role == 'cajero' else 'cliente')), 201
    except ValueError as e:
        return jsonify({'error':str(e)}), 400
    except Error:
        return jsonify({'error':'No se pudo registrar la venta en la base de datos.'}), 500

@app.get('/api/sales')
@role_required('dueno','cajero')
def sales_history():
    rows = query('SELECT s.id,s.sale_type,s.total,s.status,s.created_at,u.username FROM sales s JOIN users u ON u.id=s.user_id ORDER BY s.created_at DESC LIMIT 200')
    for r in rows:
        r['total'] = float(r['total']); r['created_at'] = r['created_at'].isoformat(sep=' ', timespec='seconds')
    return jsonify(rows)

@app.get('/api/dashboard')
@role_required('dueno')
def dashboard():
    return jsonify(query('''SELECT COUNT(*) AS products, COALESCE(SUM(stock),0) AS units,
        COALESCE(SUM(CASE WHEN stock<=5 THEN 1 ELSE 0 END),0) AS low_stock,
        (SELECT COUNT(*) FROM sales WHERE status='completada') AS sales_count,
        (SELECT COALESCE(SUM(total),0) FROM sales WHERE status='completada') AS sales_total FROM products WHERE active=1''', fetch='one'))

@app.errorhandler(500)
def server_error(_):
    return jsonify({'error':'Error interno. Revisa la configuración y los registros del servidor.'}), 500

if __name__ == '__main__':
    app.run(debug=os.getenv('FLASK_DEBUG','0') == '1')
