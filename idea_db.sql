CREATE TABLE empresas (
    RUC INT NOT NULL UNIQUE,
    PRIMARY KEY (RUC),
    nombre VARCHAR(100) NOT NULL,
    CIIU VARCHAR(100),
    razon_social VARCHAR(100) NOT NULL,
    sector VARCHAR(100) NOT NULL,
    direccion1 VARCHAR(256) NOT NULL,
    direccion2 VARCHAR(256),
    distrito VARCHAR(100),
    facturacion VARCHAR(100),
    tamano VARCHAR(100),
    contacto VARCHAR(100),
    correo VARCHAR(100),
    telefono_fijo VARCHAR(20) NOT NULL,
    pagina_web VARCHAR(200),
    provincia VARCHAR(100),
    clasificacion_de_cliente VARCHAR(100)
);

CREATE Table personas (
    id_persona INT NOT NULL AUTO_INCREMENT UNIQUE,
    PRIMARY KEY (id_persona),
    DNI INT,
    nombre VARCHAR(100) NOT NULL,
    apellido1 VARCHAR(100) NOT NULL,
    apellido2 VARCHAR(100),
    edad INT,
    universidad VARCHAR(100),
    carrera VARCHAR(100),
    cargo VARCHAR(100) NOT NULL,
    email_personal VARCHAR(100),
    email_corporativo VARCHAR(100),
    fecha_de_nacimiento DATE,
    direccion VARCHAR(256),
    area_de_trabajo VARCHAR(100),
    telefono_corporativo VARCHAR(25) NOT NULL,
    telefono_personal VARCHAR(25),
    nacionalidad VARCHAR(100),
    especializacion VARCHAR(100),
    empresa_asociada INT NOT NULL,
    FOREIGN KEY (empresa_asociada) REFERENCES empresas(RUC)
);

CREATE TABLE equipos (
    ID INT NOT NULL AUTO_INCREMENT UNIQUE,
    PRIMARY KEY (ID),
    nombre VARCHAR(100),
    descripcion VARCHAR(256),
    tipo VARCHAR(100),
    modelo VARCHAR(100),
    fecha_de_creacion DATE,
    fecha_de_compra DATE,
    ultima_fecha_de_mantenimiento DATETIME,
    RUC_empresa INT,
    FOREIGN KEY (RUC_empresa) REFERENCES empresas(RUC),
    persona_asociada INT,
    FOREIGN KEY (persona_asociada) REFERENCES personas(id_persona),
    estado_operativo VARCHAR(100),
    ubicacion_del_equipo_planta_o_area VARCHAR(100),
    costo_de_mantenimiento INT,
    precio_de_compra INT,
    depreciacion_anual_estimada INT
);

CREATE TABLE historial_de_mantenimientos (
    ID INT NOT NULL AUTO_INCREMENT UNIQUE,
    PRIMARY KEY (ID),
    ID_equipo INT,
    FOREIGN KEY (ID_equipo) REFERENCES equipos(ID),
    fecha_de_mantenimiento DATE,
    descripcion VARCHAR(256),
    costo INT,
    responsable VARCHAR(100),
    tipo_de_mantenimiento VARCHAR(100)
);

CREATE TABLE historial_de_cambios (
    ID INT NOT NULL AUTO_INCREMENT UNIQUE,
    PRIMARY KEY (ID),
    usuario VARCHAR(100),
    fecha DATETIME,
    tipo VARCHAR(100),
    tabla_afectada VARCHAR(100),
    ID_afectado INT,
    columna_afectada VARCHAR(100)
);


-- SELECT COLUMN_NAME
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'empresas'
-- AND TABLE_SCHEMA = 'idea_db';

-- SELECT TABLE_NAME
-- FROM INFORMATION_SCHEMA.TABLES
-- WHERE TABLE_SCHEMA = 'nombre_de_tu_base_de_datos';

-- DROP TABLE historial_de_mantenimientos;
-- DROP TABLE equipos;
-- DROP TABLE personas;
-- DROP TABLE empresas

-- SELECT * FROM empresas
-- SELECT * FROM personas
-- SELECT * FROM equipos
-- SELECT * FROM historial_de_cambios
-- SELECT * FROM historial_de_mantenimientos

-- ALTER TABLE personas MODIFY fecha_de_nacimiento DATE

-- ALTER TABLE 

-- SELECT * FROM equipos WHERE RUC_empresa = 7742

-- DELETE FROM empresas WHERE RUC = 258;
-- DELETE FROM empresas WHERE RUC = 369;

-- SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'personas' AND COLUMN_NAME = 'DNI';
