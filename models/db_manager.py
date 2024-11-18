from config.database import get_db_config
import mysql.connector

# models/db_manager.py
class DatabaseManager:
    def __init__(self):
        self.config = get_db_config()
        self.connection = None
    
    def connect(self):
        self.connection = mysql.connector.connect(**self.config)
        return self.connection
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()