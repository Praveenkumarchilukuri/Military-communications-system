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
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_name VARCHAR(255),
    receiver_name VARCHAR(255),
    message TEXT,
    encrypt_keys TEXT,
    msg_time DATETIME,
    priority VARCHAR(20) DEFAULT 'ROUTINE',
    is_read BOOLEAN DEFAULT FALSE,
    auto_delete_at DATETIME NULL,
    self_destruct BOOLEAN DEFAULT FALSE,
    aes_key TEXT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    action VARCHAR(100),
    details TEXT,
    ip_address VARCHAR(45),
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS file_attachments (
    attachment_id INT AUTO_INCREMENT PRIMARY KEY,
    message_id INT,
    file_name VARCHAR(255),
    encrypted_file LONGBLOB,
    file_size INT,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255),
    notification_type VARCHAR(50),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert Admin user (optional, but good for testing)
-- INSERT INTO signup (username, password, user_type, status) VALUES ('admin', 'admin', 'Admin', 'Approved');
-- Note: Admin login is handled separately with environment variables.
