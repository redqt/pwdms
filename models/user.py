from models.db_manager import DatabaseManager
from mysql.connector import Error
import hashlib
import datetime
from cryptography.fernet import Fernet
import base64

class User:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _hash_password(self, password: str) -> str:
        """对密码进行哈希处理"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_fernet_key(self, master_key: str) -> str:
        """生成合法的Fernet密钥"""
        # 确保master_key至少32位
        master_key = master_key.ljust(32)[:32]
        # 转换为base64格式
        return base64.urlsafe_b64encode(master_key.encode()).decode()

    def register(self, username: str, password: str, email: str, master_key: str) -> dict:
        """
        用户注册
        返回: {'success': bool, 'message': str, 'user_id': int}
        """
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return {'success': False, 'message': '用户名已存在', 'user_id': None}

            # 检查邮箱是否已存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {'success': False, 'message': '邮箱已被注册', 'user_id': None}

            # 生成合法的Fernet密钥
            fernet_key = self._generate_fernet_key(master_key)

            # 插入新用户
            sql = """INSERT INTO users (username, password, email, master_key, is_active) 
                    VALUES (%s, %s, %s, %s, true)"""
            hashed_password = self._hash_password(password)
            cursor.execute(sql, (username, hashed_password, email, fernet_key))
            conn.commit()

            return {
                'success': True, 
                'message': '注册成功', 
                'user_id': cursor.lastrowid
            }

        except Error as e:
            return {'success': False, 'message': f'注册失败: {str(e)}', 'user_id': None}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def login(self, username: str, password: str) -> dict:
        """
        用户登录
        返回: {'success': bool, 'message': str, 'user_data': dict}
        """
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 验证用户名和密码
            hashed_password = self._hash_password(password)
            sql = """SELECT id, username, email, is_active, master_key 
                    FROM users 
                    WHERE username = %s AND password = %s"""
            cursor.execute(sql, (username, hashed_password))
            user = cursor.fetchone()

            if not user:
                return {
                    'success': False, 
                    'message': '用户名或密码错误', 
                    'user_data': None
                }

            if not user['is_active']:
                return {
                    'success': False, 
                    'message': '账号已被禁用', 
                    'user_data': None
                }

            # 更新最后登录时间
            cursor.execute(
                "UPDATE users SET last_login_at = %s WHERE id = %s",
                (datetime.datetime.now(), user['id'])
            )
            conn.commit()

            return {
                'success': True,
                'message': '登录成功',
                'user_data': user
            }

        except Error as e:
            return {'success': False, 'message': f'登录失败: {str(e)}', 'user_data': None}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def change_password(self, user_id: int, old_password: str, new_password: str) -> dict:
        """修改密码"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 验证旧密码
            hashed_old_password = self._hash_password(old_password)
            cursor.execute("SELECT id FROM users WHERE id = %s AND password = %s", 
                          (user_id, hashed_old_password))
            if not cursor.fetchone():
                return {'success': False, 'message': '原密码错误'}

            # 更新新密码
            hashed_new_password = self._hash_password(new_password)
            cursor.execute("UPDATE users SET password = %s WHERE id = %s", 
                          (hashed_new_password, user_id))
            conn.commit()

            return {'success': True, 'message': '密码修改成功'}
        except Error as e:
            return {'success': False, 'message': f'密码修改失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def reset_password_by_email(self, email: str) -> dict:
        """通过邮箱重置密码（发送重置链接）"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 检查邮箱是否存在
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if not cursor.fetchone():
                return {'success': False, 'message': '邮箱不存在'}

            # TODO: 生成重置token并发送邮件
            # 这里需要添加发送邮件的具体实现
            return {'success': True, 'message': '重置密码邮件已发送'}
        except Error as e:
            return {'success': False, 'message': f'重置密码失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def update_profile(self, user_id: int, data: dict) -> dict:
        """更新用户信息"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 构建更新语句
            update_fields = []
            values = []
            for key, value in data.items():
                if key in ['email', 'master_key']:  # 允许更新的字段
                    update_fields.append(f"{key} = %s")
                    values.append(value)

            if not update_fields:
                return {'success': False, 'message': '没有可更新的内容'}

            values.append(user_id)
            sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(sql, values)
            conn.commit()

            return {'success': True, 'message': '信息更新成功'}
        except Error as e:
            return {'success': False, 'message': f'更新失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def deactivate_account(self, user_id: int, password: str) -> dict:
        """停用账号"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 验证密码
            hashed_password = self._hash_password(password)
            cursor.execute("SELECT id FROM users WHERE id = %s AND password = %s", 
                          (user_id, hashed_password))
            if not cursor.fetchone():
                return {'success': False, 'message': '密码验证失败'}

            # 停用账号
            cursor.execute("UPDATE users SET is_active = false WHERE id = %s", (user_id,))
            conn.commit()

            return {'success': True, 'message': '账号已停用'}
        except Error as e:
            return {'success': False, 'message': f'停用账号失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def get_user_info(self, user_id: int) -> dict:
        """获取用户信息"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("""
                SELECT id, username, email, is_active, created_at, last_login_at 
                FROM users WHERE id = %s
            """, (user_id,))
            user_info = cursor.fetchone()

            if not user_info:
                return {'success': False, 'message': '用户不存在', 'data': None}

            return {'success': True, 'message': '获取成功', 'data': user_info}
        except Error as e:
            return {'success': False, 'message': f'获取用户信息失败: {str(e)}', 'data': None}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()
