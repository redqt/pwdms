import mysql.connector
from mysql.connector import Error

def init_database():
    try:
        connection = mysql.connector.connect(
            host="你的服务器IP",
            port=3306,
            user="你的用户名",
            password="你的密码"
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS password_manager")
            print("数据库创建成功或已存在")
            
            # 使用该数据库
            cursor.execute("USE password_manager")
            
            # 创建表的SQL语句（之前我们讨论过的表结构）
            create_tables_sql = ["""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    password VARCHAR(255) NOT NULL,
                    master_key VARCHAR(255) NOT NULL,
                    email VARCHAR(100) NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP NULL
                )""",
                """
                CREATE TABLE IF NOT EXISTS passwords (
                    id INTEGER PRIMARY KEY AUTO_INCREMENT,
                    user_id INTEGER NOT NULL,
                    title VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    website_name VARCHAR(100),
                    website_url VARCHAR(255),
                    account_username VARCHAR(100),
                    encrypted_password TEXT NOT NULL,
                    password_strength INTEGER,
                    is_active BOOLEAN DEFAULT true,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )"""
            ]
            
            # 执行创建表的SQL
            for sql in create_tables_sql:
                cursor.execute(sql)
                
            print("所有表创建成功")
            
    except Error as e:
        print(f"错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL连接已关闭")

if __name__ == "__main__":
    init_database()