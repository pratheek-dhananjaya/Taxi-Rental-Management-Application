# Taxi Rental Management Application

**Overview**

The Taxi Rental Management Application is a web-based system designed to manage taxi rental services. Built with Flask for the backend, PostgreSQL for data storage, and Tailwind CSS for styling, it provides a user-friendly interface for three roles: managers, clients, and drivers. The application supports functionalities such as user registration, car and driver management, rent booking, and statistical reporting, all backed by a relational database.

**Features**

**Managers:**

Register and log in using a unique SSN.
Add or remove cars and car models.
Add or remove drivers with their details.
View top-k clients by number of rents.
Generate reports on car model usage, driver statistics (rents and ratings), and brand performance.
Query clients based on city-based rent patterns.
Identify problematic drivers in specific cities.

**Clients:**

Register with name, email, addresses, and credit card details; log in using email.
Book a rent by selecting an available car model and date, with automatic driver assignment.
Book a rent with the highest-rated available driver for a specific model.
View all booked rents with car and driver details.
Submit reviews for drivers they have rented with, including a rating (0-5) and a message.

**Drivers:**

Log in using their name.
Update their address.
View all available car models.
Declare which car models they can drive.

# Prerequisites

To run the application, ensure you have the following installed:

Python 3.7+: Download from python.org.

PostgreSQL 10+: Download from postgresql.org or install via:

macOS: brew install postgresql

Ubuntu: sudo apt-get install postgresql postgresql-contrib

Windows: Use the PostgreSQL installer.

pip: Python package manager (usually included with Python) (pip3 install psycopg2-binary)

A code editor (e.g., VS Code, PyCharm) for editing configuration files.
