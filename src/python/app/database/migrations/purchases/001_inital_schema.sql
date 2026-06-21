CREATE TABLE purchases (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    map_id INT NOT NULL,
    invoice_id INT NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id),
    UNIQUE KEY uq_user_map_purchase (user_id, map_id),
    INDEX idx_purchases_user_id (user_id)
);