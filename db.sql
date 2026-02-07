CREATE DATABASE IF NOT EXISTS military;
USE military;

CREATE TABLE IF NOT EXISTS signup (
    username VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255),
    contact_no VARCHAR(20),
    gender VARCHAR(10),
    email VARCHAR(255),
    address TEXT,
    user_type VARCHAR(50),
    status VARCHAR(20) DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS messages (
    message_id INT PRIMARY KEY,
    sender_name VARCHAR(255),
    receiver_name VARCHAR(255),
    message TEXT,
    encrypt_keys TEXT,
    msg_time DATETIME
);

-- Insert Admin user (optional, but good for testing)
-- INSERT INTO signup (username, password, user_type, status) VALUES ('admin', 'admin', 'Admin', 'Approved');
-- Note: Admin login is hardcoded in the view as 'admin'/'admin' and doesn't check DB.
