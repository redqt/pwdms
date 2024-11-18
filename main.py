import tkinter as tk
from tkinter import ttk, messagebox
from models.password import Password

class PasswordManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("密码管理器")
        self.root.geometry("700x350")
        
        self.password_manager = Password()
        self.user_id = 1  # 固定用户ID为1
        
        # 创建主界面
        self.create_main_frame()
        
    def create_main_frame(self):
        """创建主界面"""
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建搜索框架
        search_frame = ttk.Frame(self.main_frame)
        search_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 搜索输入框
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)  # 当输入变化时触发搜索
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.grid(row=0, column=0, padx=(0, 10))
        
        # 搜索类型选择
        self.search_type = tk.StringVar(value="all")
        ttk.Radiobutton(search_frame, text="全部", variable=self.search_type, 
                        value="all", command=self.on_search_change).grid(row=0, column=1)
        ttk.Radiobutton(search_frame, text="标题", variable=self.search_type, 
                        value="title", command=self.on_search_change).grid(row=0, column=2)
        ttk.Radiobutton(search_frame, text="用户名", variable=self.search_type, 
                        value="username", command=self.on_search_change).grid(row=0, column=3)
        ttk.Radiobutton(search_frame, text="网站", variable=self.search_type, 
                        value="website", command=self.on_search_change).grid(row=0, column=4)
        
        # 创建密码列表（注意这里改为row=1）
        self.create_password_list()
        
        # 添加按钮（注意这里改为row=2）
        ttk.Button(self.main_frame, text="添加密码", command=self.show_add_password).grid(row=2, column=0, pady=10)
        
    def create_password_list(self):
        """创建密码列表"""
        # 创建表格框架
        list_frame = ttk.Frame(self.main_frame)
        list_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建表格
        columns = ('title', 'username', 'website', 'category')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # 定义表头
        self.tree.heading('title', text='标题')
        self.tree.heading('username', text='用户名')
        self.tree.heading('website', text='网站/应用')
        self.tree.heading('category', text='分类')
        
        # 设置列宽
        self.tree.column('title', width=150)
        self.tree.column('username', width=150)
        self.tree.column('website', width=200)
        self.tree.column('category', width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')
        
        # 配置grid权重，使表格可以随窗口调整大小
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 绑定双击事件
        self.tree.bind('<Double-1>', self.view_password)
        
        # 加载密码列表
        self.load_passwords()
        
    def load_passwords(self):
        """加载密码列表"""
        # 清除现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 获取密码列表
        result = self.password_manager.list_passwords(self.user_id)
        if result['success']:
            search_text = self.search_var.get().lower()
            search_type = self.search_type.get()
            
            for pwd in result['data']:
                # 根据搜索条件过滤
                if search_text:
                    if search_type == "all":
                        if not (search_text in pwd['title'].lower() or 
                               search_text in pwd['account_username'].lower() or 
                               search_text in (pwd['website_name'] or '').lower()):
                            continue
                    elif search_type == "title":
                        if search_text not in pwd['title'].lower():
                            continue
                    elif search_type == "username":
                        if search_text not in pwd['account_username'].lower():
                            continue
                    elif search_type == "website":
                        if not pwd['website_name'] or search_text not in pwd['website_name'].lower():
                            continue
                
                # 插入符合条件的记录
                item = self.tree.insert('', tk.END, values=(
                    pwd['title'],
                    pwd['account_username'],
                    pwd['website_name'],
                    pwd['category']
                ))
                self.tree.item(item, text=str(pwd['id']))
        
    def show_add_password(self):
        """显示添加密码窗口"""
        add_window = tk.Toplevel(self.root)
        add_window.title("添加密码")
        add_window.geometry("400x300")
        
        # 创建表单
        ttk.Label(add_window, text="标题:").grid(row=0, column=0, pady=5, padx=5)
        title_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=title_var, width=30).grid(row=0, column=1, pady=5)
        
        ttk.Label(add_window, text="用户名:").grid(row=1, column=0, pady=5, padx=5)
        username_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=username_var, width=30).grid(row=1, column=1, pady=5)
        
        ttk.Label(add_window, text="密码:").grid(row=2, column=0, pady=5, padx=5)
        password_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=password_var, show="*", width=30).grid(row=2, column=1, pady=5)
        
        ttk.Label(add_window, text="网站/应用:").grid(row=3, column=0, pady=5, padx=5)
        website_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=website_var, width=30).grid(row=3, column=1, pady=5)
        
        ttk.Label(add_window, text="分类:").grid(row=4, column=0, pady=5, padx=5)
        category_var = tk.StringVar()
        ttk.Entry(add_window, textvariable=category_var, width=30).grid(row=4, column=1, pady=5)
        
        def save_password():
            data = {
                'title': title_var.get(),
                'account_username': username_var.get(),
                'password': password_var.get(),
                'website_name': website_var.get(),
                'category': category_var.get()
            }
            
            result = self.password_manager.add_password(self.user_id, data)
            if result['success']:
                messagebox.showinfo("成功", "密码添加成功！")
                add_window.destroy()
                self.load_passwords()
            else:
                messagebox.showerror("错误", result['message'])
                
        ttk.Button(add_window, text="保存", command=save_password).grid(row=5, column=0, columnspan=2, pady=10)
        
    def view_password(self, event):
        """查看密码详情"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        item = selected_items[0]
        values = self.tree.item(item)['values']
        if not values:
            return
            
        # 获取完整密码信息，包括解密的密码
        result = self.password_manager.get_password(self.tree.item(item)['text'], self.user_id)
        if result['success']:
            pwd = result['data']
            # 创建详情窗口
            detail_window = tk.Toplevel(self.root)
            detail_window.title("密码详情")
            detail_window.geometry("400x300")
            
            # 显示信息
            ttk.Label(detail_window, text="标题:").grid(row=0, column=0, pady=5, padx=5, sticky='e')
            ttk.Label(detail_window, text=pwd['title']).grid(row=0, column=1, pady=5, padx=5, sticky='w')
            
            ttk.Label(detail_window, text="用户名:").grid(row=1, column=0, pady=5, padx=5, sticky='e')
            username_label = ttk.Label(detail_window, text=pwd['account_username'])
            username_label.grid(row=1, column=1, pady=5, padx=5, sticky='w')
            
            ttk.Label(detail_window, text="密码:").grid(row=2, column=0, pady=5, padx=5, sticky='e')
            password_label = ttk.Label(detail_window, text=pwd['password'])
            password_label.grid(row=2, column=1, pady=5, padx=5, sticky='w')
            
            ttk.Label(detail_window, text="网站:").grid(row=3, column=0, pady=5, padx=5, sticky='e')
            ttk.Label(detail_window, text=pwd['website_name']).grid(row=3, column=1, pady=5, padx=5, sticky='w')
            
            ttk.Label(detail_window, text="分类:").grid(row=4, column=0, pady=5, padx=5, sticky='e')
            ttk.Label(detail_window, text=pwd['category']).grid(row=4, column=1, pady=5, padx=5, sticky='w')
            
            # 添加复制按钮
            def copy_username():
                self.root.clipboard_clear()
                self.root.clipboard_append(pwd['account_username'])
                messagebox.showinfo("成功", "用户名已复制到剪贴板")
                
            def copy_password():
                self.root.clipboard_clear()
                self.root.clipboard_append(pwd['password'])
                messagebox.showinfo("成功", "密码已复制到剪贴板")
                
            ttk.Button(detail_window, text="复制用户名", command=copy_username).grid(row=1, column=2, padx=5)
            ttk.Button(detail_window, text="复制密码", command=copy_password).grid(row=2, column=2, padx=5)
            
            # 添加编辑和删除按钮
            def edit_password():
                # TODO: 实现编辑功能
                pass
                
            def delete_password():
                if messagebox.askyesno("确认", "确定要删除这条密码记录吗？"):
                    result = self.password_manager.delete_password(pwd['id'], self.user_id)
                    if result['success']:
                        messagebox.showinfo("成功", "密码记录已删除")
                        detail_window.destroy()
                        self.load_passwords()
                    else:
                        messagebox.showerror("错误", result['message'])
                        
            ttk.Button(detail_window, text="编辑", command=edit_password).grid(row=5, column=0, pady=10)
            ttk.Button(detail_window, text="删除", command=delete_password).grid(row=5, column=1, pady=10)
        else:
            messagebox.showerror("错误", result['message'])
        
    def on_search_change(self, *args):
        """当搜索条件改变时触发"""
        self.load_passwords()
        
if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordManagerApp(root)
    root.mainloop()