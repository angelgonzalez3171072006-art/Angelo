"""Carga datos de demo en una base de datos creada con schema.sql.
Ejecuta una sola vez: python seed_demo.py
"""
import os
import mysql.connector
from werkzeug.security import generate_password_hash

config = dict(host=os.getenv('DB_HOST','127.0.0.1'), port=int(os.getenv('DB_PORT','3306')),
              user=os.getenv('DB_USER','stockmax_user'), password=os.getenv('DB_PASSWORD',''),
              database=os.getenv('DB_NAME','stockmax'), charset='utf8mb4')
conn = mysql.connector.connect(**config)
cur = conn.cursor()
try:
    users = [
        ('dueno','Dueño de demostración',generate_password_hash('Demo1234!'),'dueno'),
        ('cajero','Cajero de demostración',generate_password_hash('Demo1234!'),'cajero'),
        ('cliente','Cliente de demostración',generate_password_hash('Demo1234!'),'cliente'),
    ]
    cur.executemany('INSERT IGNORE INTO users(username,full_name,password_hash,role) VALUES(%s,%s,%s,%s)', users)
    cats = ['Abarrotes','Bebidas','Lácteos','Limpieza','Verdulería','Botanas']
    cur.executemany('INSERT IGNORE INTO categories(name) VALUES(%s)', [(x,) for x in cats])
    conn.commit()
    cur.execute('SELECT id,name FROM categories')
    category_ids = dict(cur.fetchall())
    products = [
      ('Arroz','Arroz blanco, paquete de 1 kg',32.00,30,'Abarrotes','2027-06-30'),
      ('Frijol negro','Paquete de 1 kg',38.00,24,'Abarrotes','2027-05-30'),
      ('Agua natural','Botella de 1 litro',15.00,40,'Bebidas','2027-12-31'),
      ('Leche entera','Envase de 1 litro',28.00,25,'Lácteos','2026-12-15'),
      ('Detergente','Bolsa de 1 kg',45.00,20,'Limpieza','2028-01-31'),
      ('Manzana roja','Precio por kilogramo',35.00,20,'Verdulería','2026-12-01'),
      ('Papas fritas','Bolsa individual',20.00,18,'Botanas','2027-04-30'),
    ]
    for name,desc,price,stock,cat,expiry in products:
        cur.execute('SELECT id FROM products WHERE name=%s LIMIT 1',(name,))
        if not cur.fetchone():
            cur.execute('INSERT INTO products(name,description,price,stock,category_id,expiry_date) VALUES(%s,%s,%s,%s,%s,%s)',
                        (name,desc,price,stock,category_ids[cat],expiry))
    conn.commit()
    print('Datos de demostración preparados.')
    print('Usuarios: dueno / cajero / cliente')
    print('Contraseña para los tres: Demo1234!')
finally:
    cur.close(); conn.close()
