-- strong entities

CREATE TABLE Manager (
    ssn VARCHAR(11) PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE
);

CREATE TABLE Client (
    email VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE Address (
    road_name VARCHAR(100) NOT NULL,
    number VARCHAR(10) NOT NULL,
    city VARCHAR(50) NOT NULL,
    PRIMARY KEY (road_name, number, city)
);

CREATE TABLE Car (
    car_id INTEGER PRIMARY KEY,
    brand VARCHAR(100)
);

-- weak entities

CREATE TABLE ClientAddress (
    client_email VARCHAR(100),
    road_name VARCHAR(100),
    number VARCHAR(10),
    city VARCHAR(50),
    PRIMARY KEY (client_email, road_name, number, city),
    FOREIGN KEY (client_email) REFERENCES Client(email),
    FOREIGN KEY (road_name, number, city) REFERENCES Address(road_name, number, city)
);

CREATE TABLE CreditCard (
    card_number VARCHAR(20) PRIMARY KEY,
    client_email VARCHAR(100),
    payment_road_name VARCHAR(100),
    payment_number VARCHAR(10),
    payment_city VARCHAR(50),
    FOREIGN KEY (client_email) REFERENCES Client(email),
    FOREIGN KEY (payment_road_name, payment_number, payment_city)
        REFERENCES Address(road_name, number, city)
);

CREATE TABLE Model (
    model_id SERIAL,
    car_id INT NOT NULL,
    color VARCHAR(30),
    construction_year INT,
    transmission_type VARCHAR(10) CHECK (transmission_type IN ('manual', 'automatic')),
    PRIMARY KEY (model_id, car_id),
    FOREIGN KEY (car_id) REFERENCES Car(car_id)
);

CREATE TABLE Driver (
    name VARCHAR(100) PRIMARY KEY,
    road_name VARCHAR(100),
    number VARCHAR(10),
    city VARCHAR(50),
    FOREIGN KEY (road_name, number, city) REFERENCES Address(road_name, number, city)
);

CREATE TABLE Rent (
    rent_id VARCHAR(8) PRIMARY KEY,  -- Changed to VARCHAR for UUID
    rent_date DATE NOT NULL,
    client_email VARCHAR(100),
    driver_name VARCHAR(100) NOT NULL,
    model_id INT,
    car_id INT,
    FOREIGN KEY (client_email) REFERENCES Client(email),
    FOREIGN KEY (driver_name) REFERENCES Driver(name),
    FOREIGN KEY (model_id, car_id) REFERENCES Model(model_id, car_id)
);

CREATE TABLE Review (
    review_id VARCHAR(8),  -- Changed to VARCHAR for UUID
    message TEXT,
    rating INTEGER NOT NULL CHECK (rating >= 0 AND rating <= 5),
    driver_name VARCHAR(100),
    client_email VARCHAR(100),
    PRIMARY KEY (review_id, driver_name, client_email),
    FOREIGN KEY (driver_name) REFERENCES Driver(name),
    FOREIGN KEY (client_email) REFERENCES Client(email)
);

CREATE TABLE DriverModel (
    driver_name VARCHAR(100),
    model_id INT,
    car_id INT,
    PRIMARY KEY (driver_name, model_id, car_id),
    FOREIGN KEY (driver_name) REFERENCES Driver(name),
    FOREIGN KEY (model_id, car_id) REFERENCES Model(model_id, car_id)
);