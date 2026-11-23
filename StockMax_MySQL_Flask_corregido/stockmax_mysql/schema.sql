-- =========================================================
-- BASE DE DATOS PARA STOCKMAX
-- Compatible con MySQL 8.0+
-- Importar este archivo desde MySQL Workbench o phpMyAdmin.
-- =========================================================

CREATE DATABASE IF NOT EXISTS stockmax
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE stockmax;

-- El orden de creación respeta las relaciones entre tablas.

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL UNIQUE,
    password_hash CHAR(64) NOT NULL,
    rol ENUM('dueno', 'cajero', 'cliente') NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS productos (
    id_producto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    id_categoria INT NOT NULL,
    icono VARCHAR(12) DEFAULT NULL,
    fecha_caducidad DATE DEFAULT NULL,
    stock INT NOT NULL DEFAULT 0,
    total_entradas INT NOT NULL DEFAULT 0,
    total_salidas INT NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_producto_categoria
      FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria),
    CONSTRAINT chk_producto_precio CHECK (precio >= 0),
    CONSTRAINT chk_producto_stock CHECK (stock >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ventas (
    id_venta BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_usuario INT NULL,
    tipo_venta ENUM('cliente', 'caja') NOT NULL,
    fecha_venta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total DECIMAL(12,2) NOT NULL DEFAULT 0,
    estado ENUM('completada', 'cancelada') NOT NULL DEFAULT 'completada',
    observaciones VARCHAR(255) DEFAULT NULL,
    CONSTRAINT fk_venta_usuario
      FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT chk_venta_total CHECK (total >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS detalle_venta (
    id_detalle BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_venta BIGINT NOT NULL,
    id_producto INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_detalle_venta
      FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
    CONSTRAINT fk_detalle_producto
      FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
    CONSTRAINT chk_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_detalle_precio CHECK (precio_unitario >= 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id_movimiento BIGINT AUTO_INCREMENT PRIMARY KEY,
    id_producto INT NOT NULL,
    id_usuario INT NULL,
    tipo ENUM('entrada', 'salida') NOT NULL,
    cantidad INT NOT NULL,
    motivo VARCHAR(150) NOT NULL,
    fecha_movimiento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    id_venta BIGINT NULL,
    CONSTRAINT fk_mov_producto
      FOREIGN KEY (id_producto) REFERENCES productos(id_producto),
    CONSTRAINT fk_mov_usuario
      FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_mov_venta
      FOREIGN KEY (id_venta) REFERENCES ventas(id_venta),
    CONSTRAINT chk_mov_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB;

-- Categorías de la tienda.
INSERT IGNORE INTO categorias (nombre) VALUES
('Verdulería'),
('Abarrotes'),
('Limpieza'),
('Niños'),
('Bebidas'),
('Lácteos'),
('Higiene'),
('Botanas');

-- Usuarios de demostración.
-- Contraseña inicial para los tres: 1234.
-- SHA2 solo sirve como ejemplo académico; en producción se debe
-- usar Argon2id o bcrypt desde el backend, nunca autenticar en JS.
INSERT IGNORE INTO usuarios (usuario, password_hash, rol) VALUES
('dueno', SHA2('1234', 256), 'dueno'),
('cajero', SHA2('1234', 256), 'cajero'),
('cliente', SHA2('1234', 256), 'cliente');

-- Catálogo inicial basado en los productos que aparecen en StockMax.
INSERT INTO productos
(nombre, precio, id_categoria, icono, fecha_caducidad, stock, total_entradas, total_salidas)
SELECT v.nombre, v.precio, c.id_categoria, v.icono, v.caducidad, v.stock, v.stock, 0
FROM (
    SELECT 'Manzana roja' nombre, 35.00 precio, 'Verdulería' categoria, '🍎' icono, '2026-10-15' caducidad, 20 stock
    UNION ALL SELECT 'Plátano', 28.00, 'Verdulería', '🍌', '2026-10-05', 25
    UNION ALL SELECT 'Jitomate', 32.00, 'Verdulería', '🍅', '2026-10-10', 18
    UNION ALL SELECT 'Arroz', 32.00, 'Abarrotes', '🍚', '2027-02-20', 30
    UNION ALL SELECT 'Frijol negro', 38.00, 'Abarrotes', '🫘', '2027-03-15', 25
    UNION ALL SELECT 'Café molido', 65.00, 'Abarrotes', '☕', '2027-01-10', 15
    UNION ALL SELECT 'Detergente', 45.00, 'Limpieza', '🧺', '2028-01-20', 20
    UNION ALL SELECT 'Cloro', 22.00, 'Limpieza', '🧴', '2028-05-10', 20
    UNION ALL SELECT 'Cereal infantil', 48.00, 'Niños', '🥣', '2026-11-15', 15
    UNION ALL SELECT 'Galletas infantiles', 25.00, 'Niños', '🍪', '2027-01-15', 20
    UNION ALL SELECT 'Agua natural', 15.00, 'Bebidas', '💧', '2027-06-20', 40
    UNION ALL SELECT 'Jugo de naranja', 31.00, 'Bebidas', '🍊', '2026-12-10', 20
    UNION ALL SELECT 'Leche entera', 28.00, 'Lácteos', '🥛', '2026-10-08', 25
    UNION ALL SELECT 'Queso manchego', 48.00, 'Lácteos', '🧀', '2026-10-12', 15
    UNION ALL SELECT 'Shampoo', 58.00, 'Higiene', '🧴', '2028-02-10', 20
    UNION ALL SELECT 'Pasta dental', 35.00, 'Higiene', '🪥', '2028-03-20', 20
    UNION ALL SELECT 'Papas fritas', 20.00, 'Botanas', '🍟', '2027-02-10', 25
    UNION ALL SELECT 'Galletas de chocolate', 22.00, 'Botanas', '🍪', '2027-01-30', 20
) AS v
JOIN categorias c ON c.nombre = v.categoria
WHERE NOT EXISTS (
    SELECT 1 FROM productos p WHERE p.nombre = v.nombre
);

-- Consultas rápidas para comprobar la instalación.
SELECT * FROM usuarios;
SELECT p.id_producto, p.nombre, p.precio, c.nombre AS categoria,
       p.stock, p.fecha_caducidad
FROM productos p
JOIN categorias c ON c.id_categoria = p.id_categoria
ORDER BY p.id_producto;
