CREATE TABLE invoices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    map_id INT NOT NULL,
    stripe_checkout_session_id VARCHAR(255) NOT NULL UNIQUE,
    stripe_payment_intent_id VARCHAR(255) UNIQUE,
    stripe_customer_id VARCHAR(255),
    amount INT NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'usd',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    failure_reason VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (map_id) REFERENCES maps(id) ON DELETE CASCADE,
    INDEX idx_invoices_user_id (user_id),
    INDEX idx_invoices_session_id (stripe_checkout_session_id),
    INDEX idx_invoices_payment_intent_id (stripe_payment_intent_id)
);

