from models.db_manager import DatabaseManager
from mysql.connector import Error
from cryptography.fernet import Fernet
import datetime

class Password:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def add_password(self, user_id: int, data: dict) -> dict:
        """
        添加新密码
        data: {
            'title': str,
            'category': str,
            'website_name': str,
            'website_url': str,
            'account_username': str,
            'password': str,        # 原始密码
            'master_key': str       # 用于加密的主密钥
        }
        """
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 首先获取用户的master_key
            cursor.execute("SELECT master_key FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return {'success': False, 'message': '用户不存在'}

            # 使用存储的Fernet密钥
            f = Fernet(user['master_key'].encode())
            encrypted_password = f.encrypt(data['password'].encode()).decode()

            # 计算密码强度（示例实现）
            password_strength = self._calculate_password_strength(data['password'])

            sql = """INSERT INTO passwords 
                    (user_id, title, category, website_name, website_url, 
                     account_username, encrypted_password, password_strength)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            values = (user_id, data['title'], data.get('category'), 
                     data.get('website_name'), data.get('website_url'),
                     data.get('account_username'), encrypted_password, 
                     password_strength)
            
            cursor.execute(sql, values)
            conn.commit()

            return {'success': True, 'message': '密码添加成功', 'id': cursor.lastrowid}
        except Error as e:
            return {'success': False, 'message': f'添加失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def get_password(self, password_id: int, user_id: int, master_key: str = None) -> dict:
        """获取密码详情（包括解密的密码）"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 首先获取用户的master_key
            cursor.execute("""
                SELECT p.*, u.master_key 
                FROM passwords p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = %s AND p.user_id = %s AND p.is_active = true
            """, (password_id, user_id))
            
            pwd = cursor.fetchone()
            if not pwd:
                return {'success': False, 'message': '密码不存在或无权访问', 'data': None}

            # 使用存储的master_key进行解密
            try:
                f = Fernet(pwd['master_key'].encode())
                decrypted_password = f.decrypt(pwd['encrypted_password'].encode()).decode()
                pwd['password'] = decrypted_password
                # 删除不需要返回的字段
                del pwd['encrypted_password']
                del pwd['master_key']
            except Exception as e:
                return {'success': False, 'message': f'密码解密失败: {str(e)}', 'data': None}

            return {'success': True, 'message': '获取成功', 'data': pwd}
        except Error as e:
            return {'success': False, 'message': f'获取失败: {str(e)}', 'data': None}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def list_passwords(self, user_id: int, category: str = None) -> dict:
        """获取密码列表（不包含实际密码）"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            sql = """SELECT id, title, category, website_name, website_url, 
                     account_username, password_strength, created_at, updated_at
                     FROM passwords 
                     WHERE user_id = %s AND is_active = true"""
            params = [user_id]

            if category:
                sql += " AND category = %s"
                params.append(category)

            sql += " ORDER BY updated_at DESC"
            cursor.execute(sql, params)
            
            passwords = cursor.fetchall()
            return {'success': True, 'message': '获取成功', 'data': passwords}
        except Error as e:
            return {'success': False, 'message': f'获取失败: {str(e)}', 'data': None}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def update_password(self, password_id: int, user_id: int, data: dict) -> dict:
        """更新密码信息"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor(dictionary=True)

            # 获取用户的master_key
            cursor.execute("""
                SELECT p.id, u.master_key 
                FROM passwords p
                JOIN users u ON p.user_id = u.id
                WHERE p.id = %s AND p.user_id = %s AND p.is_active = true
            """, (password_id, user_id))
            
            pwd = cursor.fetchone()
            if not pwd:
                return {'success': False, 'message': '密码不存在或无权修改'}

            # 构建更新语句
            update_fields = []
            values = []
            for key, value in data.items():
                if key in ['title', 'category', 'website_name', 'website_url', 
                          'account_username', 'password']:
                    if key == 'password':
                        # 使用存储的master_key加密新密码
                        f = Fernet(pwd['master_key'].encode())
                        encrypted_password = f.encrypt(value.encode()).decode()
                        update_fields.append("encrypted_password = %s")
                        values.append(encrypted_password)
                        # 更新密码强度
                        update_fields.append("password_strength = %s")
                        values.append(self._calculate_password_strength(value))
                    else:
                        update_fields.append(f"{key} = %s")
                        values.append(value)

            if not update_fields:
                return {'success': False, 'message': '没有可更新的内容'}

            values.extend([password_id, user_id])
            sql = f"""UPDATE passwords 
                     SET {', '.join(update_fields)} 
                     WHERE id = %s AND user_id = %s"""
            
            cursor.execute(sql, values)
            conn.commit()

            return {'success': True, 'message': '更新成功'}
        except Error as e:
            return {'success': False, 'message': f'更新失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def delete_password(self, password_id: int, user_id: int) -> dict:
        """删除密码（软删除）"""
        try:
            conn = self.db_manager.connect()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE passwords 
                SET is_active = false 
                WHERE id = %s AND user_id = %s AND is_active = true
            """, (password_id, user_id))
            
            if cursor.rowcount == 0:
                return {'success': False, 'message': '密码不存在或无权删除'}

            conn.commit()
            return {'success': True, 'message': '删除成功'}
        except Error as e:
            return {'success': False, 'message': f'删除失败: {str(e)}'}
        finally:
            if conn.is_connected():
                cursor.close()
                self.db_manager.close()

    def _calculate_password_strength(self, password: str) -> int:
        """计算密码强度（示例实现）"""
        score = 0
        if len(password) >= 8: score += 20
        if any(c.isupper() for c in password): score += 20
        if any(c.islower() for c in password): score += 20
        if any(c.isdigit() for c in password): score += 20
        if any(not c.isalnum() for c in password): score += 20
        return score
