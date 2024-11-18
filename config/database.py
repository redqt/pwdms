# config/database.py
def get_db_config():
    return {
        'host':"192.168.6.115",      # 例如："192.168.6.115"
        'port':3306,              # MySQL端口
        'user':"password_manager",        # 1Panel中设置的用户名
        'password':"TZd5RfHm7RR38R8a" ,      # 1Panel中设置的密码
        'database': 'password_manager'
    }