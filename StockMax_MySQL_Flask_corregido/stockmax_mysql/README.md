# StockMax — Flask + MySQL

Versión de demostración funcional con backend, persistencia MySQL, roles, inventario, movimientos y ventas. Los productos y usuarios se consultan en la base de datos; no están definidos como arreglos o contraseñas dentro del JavaScript.

## Requisitos
- Python 3.10 o posterior
- MySQL 8 (o compatible)
- Navegador moderno

## Instalación en Windows (CMD)
1. Instala Python y MySQL Server. En MySQL crea un usuario para la aplicación o usa uno propio.
2. Abre CMD dentro de esta carpeta y ejecuta:
   ```bat
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Crea la base de datos y tablas. Desde CMD, si `mysql` está en PATH:
   ```bat
   mysql -u root -p < schema.sql
   ```
4. Configura las variables de entorno en la misma ventana de CMD (cambia la contraseña por la tuya):
   ```bat
   set DB_HOST=127.0.0.1
   set DB_PORT=3306
   set DB_USER=stockmax_user
   set DB_PASSWORD=TU_CONTRASENA_MYSQL
   set DB_NAME=stockmax
   set FLASK_SECRET_KEY=cambia-esta-clave-por-una-larga
   ```
   Si aún no creaste `stockmax_user`, inicia sesión como administrador de MySQL y créalo, por ejemplo:
   ```sql
   CREATE USER 'stockmax_user'@'localhost' IDENTIFIED BY 'TU_CONTRASENA_MYSQL';
   GRANT SELECT, INSERT, UPDATE, DELETE ON stockmax.* TO 'stockmax_user'@'localhost';
   FLUSH PRIVILEGES;
   ```
5. Carga los datos de demostración una sola vez:
   ```bat
   python seed_demo.py
   ```
6. Arranca el servidor:
   ```bat
   python app.py
   ```
7. Abre `http://127.0.0.1:5000` en Chrome.

## Usuarios de demo
Los tres usuarios usan la contraseña `Demo1234!`:
- `dueno` — administra inventario y ve ventas
- `cajero` — registra ventas y consulta el historial
- `cliente` — consulta productos y registra una compra de demostración

El script `seed_demo.py` almacena hashes de contraseñas, no contraseñas en texto plano. Las cuentas demo son solo para pruebas locales.

## Prueba manual completa
1. Entra como `dueno`; confirma que aparecen productos cargados desde MySQL.
2. Registra un producto con existencia inicial. Debe aparecer en el catálogo y en inventario.
3. Registra una entrada y comprueba que aumenta el stock.
4. Registra una salida menor que la existencia; debe disminuir. Intenta sacar más de lo disponible; debe mostrar error y no cambiar el stock.
5. Consulta movimientos; deben mostrar usuario, fecha, tipo, cantidad y motivo.
6. Cierra sesión, entra como `cliente`, agrega productos y confirma una venta. Debe crear venta, detalle, movimiento de salida y reducir stock dentro de una transacción.
7. Entra como `cajero`, registra otra venta y revisa el historial.
8. Reinicia el servidor y vuelve a consultar el catálogo; los datos deben seguir en MySQL.

## Modelo entidad-relación
Consulta `diagrama_er.mmd`. Las entidades son `users`, `categories`, `products`, `sales`, `sale_items` e `inventory_movements`.

## Pruebas automatizadas / limitaciones
La base de datos debe estar encendida y las variables de conexión deben estar configuradas. Este paquete no ha sido ejecutado contra tu instalación local de MySQL; primero hay que instalar/configurar MySQL y correr el flujo de prueba manual. No publiques el servidor de desarrollo directamente en internet. Para producción se recomienda CSRF, límites de intentos de inicio de sesión, migraciones, logging, HTTPS y gestión segura de secretos.
