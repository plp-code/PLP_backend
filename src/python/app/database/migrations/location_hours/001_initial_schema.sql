-- Per-day opening hours for a location.
-- Conventions:
--   * day_of_week: 0 = Monday ... 6 = Sunday
--   * Open day        -> one row, is_closed = FALSE, open_time/close_time set
--   * Closed day      -> one row, is_closed = TRUE,  open_time/close_time NULL
--   * Split hours     -> multiple rows for the same day (e.g. 09:00-12:00 and 14:00-18:00)
--   * No row for a day means hours are unknown / not published.
CREATE TABLE location_hours (
    id INT AUTO_INCREMENT PRIMARY KEY,
    location_id INT NOT NULL,
    day_of_week TINYINT NOT NULL,
    open_time TIME,
    close_time TIME,
    is_closed BOOL NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE,
    INDEX idx_location_hours_location_id (location_id),
    CONSTRAINT chk_location_hours_day CHECK (day_of_week BETWEEN 0 AND 6)
);
