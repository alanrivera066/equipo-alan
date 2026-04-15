-- Sistema de Gestión de Inventario
-- TechNova Solutions

CREATE DATABASE IF NOT EXISTS inventario_db;
USE inventario_db;

CREATE TABLE IF NOT EXISTS categorias (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(255),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    categoria_id INT NOT NULL,
    cantidad INT NOT NULL DEFAULT 0,
    precio DECIMAL(10,2) NOT NULL,
    stock_minimo INT NOT NULL DEFAULT 5,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id)
);

CREATE TABLE IF NOT EXISTS movimientos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    tipo ENUM('entrada', 'salida') NOT NULL,
    cantidad INT NOT NULL,
    nota VARCHAR(255),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

CREATE TABLE IF NOT EXISTS alertas_reposicion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    producto_id INT NOT NULL,
    stock_actual INT NOT NULL,
    stock_minimo INT NOT NULL,
    estado ENUM('pendiente', 'atendida') DEFAULT 'pendiente',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- Categorías de ejemplo para arrancar
INSERT INTO categorias (nombre, descripcion) VALUES
    ('Electrónica', 'Dispositivos y componentes electrónicos'),
    ('Papelería', 'Artículos de oficina y escritura'),
    ('Herramientas', 'Herramientas manuales y eléctricas');
