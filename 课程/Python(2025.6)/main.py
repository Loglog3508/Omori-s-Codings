import tkinter as tk
from tkinter import messagebox
import os
import tkinter.font as tkFont  # 导入字体模块
import customtkinter

customtkinter.set_appearance_mode("dark")  # 设置为暗色主题
customtkinter.set_default_color_theme("blue")  # 设置为蓝色主题

class Package:
    def __init__(self):
        self.tracking_number = ''
        self.sender_name = ''
        self.receiver_name = ''
        self.status = ''
        self.pickup_code = ''  

def add_package():
    package = Package()
    package.tracking_number = entry_tracking_number.get()
    package.sender_name = entry_sender_name.get()
    package.receiver_name = entry_receiver_name.get()
    package.status = status_var.get()  # 获取快递状态

    if package.status == "到达":
        package.pickup_code = pickup_code_entry.get()  # 获取取件码
        if not package.pickup_code:
            messagebox.showerror("错误", "到达状态必须填写取件码！")
            return
    else:
        package.pickup_code = ""  # 非到达状态不保存取件码

    if search_by_tracking_number(package_list, package.tracking_number):
        messagebox.showerror("错误", "快递单号已存在！")
        return

    package_list.append(package)
    save_to_file(package)
    messagebox.showinfo("成功", "快递信息已保存！")
    clear_entries()
    toggle_pickup_code()  # 重置取件码输入框状态

def search_package():
    tracking_number = entry_tracking_number.get()
    for package in package_list:
        if package.tracking_number == tracking_number:
            messagebox.showinfo("快递信息", f"快递单号: {package.tracking_number}\n寄件人: {package.sender_name}\n收件人: {package.receiver_name}\n状态: {package.status}")
            return
    messagebox.showerror("错误", "未找到该快递单号！")

def delete_package():
    tracking_number = entry_tracking_number.get()
    for package in package_list:
        if package.tracking_number == tracking_number:
            package_list.remove(package)
            save_all_to_file()
            messagebox.showinfo("成功", "快递信息已删除！")
            return
    messagebox.showerror("错误", "未找到该快递单号！")

def display_packages():
    display_text = "快递单号\t寄件人\t收件人\t状态\t取件码\n"
    for package in package_list:
        display_text += f"{package.tracking_number}\t{package.sender_name}\t{package.receiver_name}\t{package.status}\t{package.pickup_code}\n"
    messagebox.showinfo("所有快递信息", display_text)

def save_to_file(package):
    with open("packages.txt", "a") as file:
        file.write(f"{package.tracking_number} {package.sender_name} {package.receiver_name} {package.status} {package.pickup_code}\n")

def save_all_to_file():
    with open("packages.txt", "w") as file:
        for package in package_list:
            file.write(f"{package.tracking_number} {package.sender_name} {package.receiver_name} {package.status}\n")

def search_by_tracking_number(package_list, tracking_number):
    for package in package_list:
        if package.tracking_number == tracking_number:
            return True
    return False

def clear_entries():
    entry_tracking_number.delete(0, tk.END)
    entry_sender_name.delete(0, tk.END)
    entry_receiver_name.delete(0, tk.END)
    status_var.set("运输中")
    pickup_code_entry.delete(0, tk.END)

def init_packages():
    if os.path.exists("packages.txt"):
        with open("packages.txt", "r") as file:
            for line in file:
                package = Package()
                data = line.strip().split(" ")
                if len(data) < 4:  # 检查数据长度是否至少包含4个字段
                    continue  # 跳过不完整的数据行
                package.tracking_number = data[0]
                package.sender_name = data[1]
                package.receiver_name = data[2]
                package.status = data[3]
                package.pickup_code = data[4] if len(data) > 4 else ""  # 如果没有取件码，设置为空字符串
                package_list.append(package)

# 初始化快递列表
package_list = []
init_packages()

# 创建图形界面
root = customtkinter.CTk()
root.title("社区快递驿站管理系统")
root.geometry("800x600")
root.configure(bg="#f0f0f0")  # 设置窗口背景颜色
# root.iconbitmap("icon.ico")  # 替换为您的图标文件路径

# 创建字体样式
font_style = tkFont.Font(family="Microsoft YaHei", size=14)  # 设置字体为等线，大小为14

# 配置行和列的权重，让控件随着窗口大小变化
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)
root.grid_rowconfigure(3, weight=1)
root.grid_rowconfigure(4, weight=1)
root.grid_rowconfigure(5, weight=1)
root.grid_rowconfigure(6, weight=1)  # 确保第6行的权重也设置为1

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# 快递信息输入框
customtkinter.CTkLabel(root, text="快递单号:", font=("Microsoft YaHei", 14)).grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
entry_tracking_number = customtkinter.CTkEntry(root, font=("Microsoft YaHei", 14), width=300)
entry_tracking_number.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

customtkinter.CTkLabel(root, text="寄件人姓名:", font=("Microsoft YaHei", 14)).grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
entry_sender_name = customtkinter.CTkEntry(root, font=("Microsoft YaHei", 14), width=300)
entry_sender_name.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)

customtkinter.CTkLabel(root, text="收件人姓名:", font=("Microsoft YaHei", 14)).grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
entry_receiver_name = customtkinter.CTkEntry(root, font=("Microsoft YaHei", 14), width=300)
entry_receiver_name.grid(row=2, column=1, sticky="nsew", padx=20, pady=20)

# 取件码输入框（默认隐藏）
pickup_code_label = customtkinter.CTkLabel(root, text="取件码:", font=("Microsoft YaHei", 14))
pickup_code_entry = customtkinter.CTkEntry(root, font=("Microsoft YaHei", 14))

def toggle_pickup_code():
    if status_var.get() == "到达":
        pickup_code_label.grid(row=4, column=0, sticky="nsew", padx=10, pady=10)
        pickup_code_entry.grid(row=4, column=1, sticky="nsew", padx=10, pady=10)
    else:
        pickup_code_label.grid_forget()
        pickup_code_entry.grid_forget()

# 快递状态变量
status_var = tk.StringVar(value="运输中")  # 默认状态为“运输中”

# 快递状态复选框
customtkinter.CTkLabel(root, text="快递状态:", font=("Microsoft YaHei", 14)).grid(row=3, column=0, sticky="nsew", padx=20, pady=20)
customtkinter.CTkCheckBox(root, text="到达", variable=status_var, onvalue="到达", offvalue="运输中", font=("Microsoft YaHei", 14), command=toggle_pickup_code).grid(row=3, column=1, sticky="nsew", padx=20, pady=20)

# 默认隐藏取件码输入框
pickup_code_label.grid_forget()
pickup_code_entry.grid_forget()

# 修改快递信息的函数
def modify_package():
    tracking_number = entry_tracking_number.get()  # 获取输入的快递单号
    for package in package_list:
        if package.tracking_number == tracking_number:  # 如果找到匹配的快递单号
            # 更新快递信息
            package.sender_name = entry_sender_name.get()  # 更新寄件人姓名
            package.receiver_name = entry_receiver_name.get()  # 更新收件人姓名
            package.status = status_var.get()  # 更新快递状态

            # 如果状态为“到达”，更新取件码
            if package.status == "到达":
                package.pickup_code = pickup_code_entry.get()
                if not package.pickup_code:  # 如果取件码为空，弹出错误提示
                    messagebox.showerror("错误", "到达状态必须填写取件码！")
                    return
            else:
                package.pickup_code = ""  # 非到达状态清空取件码

            save_all_to_file()  # 保存更新后的快递信息到文件
            messagebox.showinfo("成功", "快递信息已修改！")
            clear_entries()  # 清空输入框
            toggle_pickup_code()  # 重置取件码输入框状态
            return

    messagebox.showerror("错误", "未找到该快递单号！")  # 如果未找到，弹出错误提示

# 功能按钮
customtkinter.CTkButton(root, text="增加快递信息", command=add_package, font=("Microsoft YaHei", 14), width=200).grid(row=5, column=0, sticky="nsew", padx=20, pady=20)
customtkinter.CTkButton(root, text="查找快递信息", command=search_package, font=("Microsoft YaHei", 14), width=200).grid(row=5, column=1, sticky="nsew", padx=20, pady=20)
customtkinter.CTkButton(root, text="删除快递信息", command=delete_package, font=("Microsoft YaHei", 14), width=200).grid(row=6, column=0, sticky="nsew", padx=20, pady=20)
customtkinter.CTkButton(root, text="显示所有快递信息", command=display_packages, font=("Microsoft YaHei", 14), width=200).grid(row=6, column=1, sticky="nsew", padx=20, pady=20)
customtkinter.CTkButton(root, text="修改快递信息", command=modify_package, font=("Microsoft YaHei", 14), width=200).grid(row=7, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)

# 调整字体大小的函数
def adjust_font(event):
    new_size = max(14, int(event.width / 30))  # 根据窗口宽度调整字体大小，变化幅度更大
    font_style.configure(size=new_size)

root.bind("<Configure>", adjust_font)  # 绑定窗口大小变化事件

# 登录功能
def login():
    def verify_credentials():
        username = entry_username.get()
        password = entry_password.get()

        # 验证用户名和密码
        if username == "admin" and password == "123456":
            messagebox.showinfo("登录成功", "欢迎使用社区快递驿站管理系统！")
            login_window.destroy()  # 关闭登录窗口
            root.deiconify()  # 显示主窗口
        else:
            messagebox.showerror("登录失败", "用户名或密码错误！")

    # 创建登录窗口
    login_window = customtkinter.CTkToplevel(root)  # 使用 CTkToplevel
    login_window.title("登录")
    login_window.geometry("400x300")
    login_window.resizable(False, False)

    # 用户名输入框
    customtkinter.CTkLabel(login_window, text="用户名:", font=("Microsoft YaHei", 14)).pack(pady=10)
    entry_username = customtkinter.CTkEntry(login_window, font=("Microsoft YaHei", 14), width=250)
    entry_username.pack(pady=10)

    # 密码输入框
    customtkinter.CTkLabel(login_window, text="密码:", font=("Microsoft YaHei", 14)).pack(pady=10)
    entry_password = customtkinter.CTkEntry(login_window, font=("Microsoft YaHei", 14), show="*", width=250)
    entry_password.pack(pady=10)

    # 登录按钮
    customtkinter.CTkButton(login_window, text="登录", font=("Microsoft YaHei", 14), command=verify_credentials, width=150).pack(pady=20)

    # 阻止用户关闭登录窗口
    login_window.protocol("WM_DELETE_WINDOW", lambda: None)

# 隐藏主窗口
root.withdraw()

# 启动登录窗口
login()

# 启动主循环
root.mainloop()