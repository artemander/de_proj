import os, random, datetime, tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import pymysql
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CAPTCHA_FOLDER = os.path.join(BASE_DIR, "captcha_images")
EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")
FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
if os.path.exists(FONT_PATH):
    pdfmetrics.registerFont(TTFont("Arial", FONT_PATH))
    PDF_FONT = "Arial"
else:
    PDF_FONT = "Helvetica"

DB = {"host": "localhost", "user": "root", "password": "root", "database": "de_project",
      "charset": "utf8mb4", "port": 3306}


def get_conn():
    return pymysql.connect(**DB, cursorclass=pymysql.cursors.DictCursor)


def setup_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except:
        pass
    style.configure(".", font=("Segoe UI", 10))
    style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
    style.configure("Treeview", rowheight=24)


class Captcha2x2(tk.Toplevel):
    def __init__(self, parent, cb):
        super().__init__(parent)
        self.cb = cb
        self.title("Капча")
        self.resizable(False, False)
        self.TOTAL = 300
        self.TILE = self.TOTAL // 2
        frame = ttk.Frame(self)
        frame.pack(padx=10, pady=10)
        ttk.Button(self, text="Проверить", command=self.check).pack(pady=6)
        files = sorted([f for f in os.listdir(CAPTCHA_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))])
        if len(files) != 4:
            messagebox.showerror("Ошибка", "В папке captcha_images должно быть ровно 4 файла")
            self.cb(False)
            self.destroy()
            return
        self.correct = [0, 1, 2, 3]
        self.order = self.correct.copy()
        while self.order == self.correct:
            random.shuffle(self.order)
        self.tiles = []
        for f in files:
            im = Image.open(os.path.join(CAPTCHA_FOLDER, f)).resize((self.TILE, self.TILE), Image.LANCZOS)
            self.tiles.append(ImageTk.PhotoImage(im))
        self.buttons = []
        for i in range(4):
            b = tk.Button(frame, image=self.tiles[self.order[i]], width=self.TILE, height=self.TILE,
                          command=lambda i=i: self.select_tile(i))
            b.grid(row=i // 2, column=i % 2, padx=4, pady=4)
            self.buttons.append(b)
        self.selected = None

    def select_tile(self, idx):
        if self.selected is None:
            self.selected = idx
            self.buttons[idx].config(relief="sunken")
        else:
            j = self.selected
            if j != idx:
                self.order[idx], self.order[j] = self.order[j], self.order[idx]
                self.buttons[idx].config(image=self.tiles[self.order[idx]])
                self.buttons[j].config(image=self.tiles[self.order[j]])
            self.buttons[j].config(relief="raised")
            self.selected = None

    def check(self):
        if self.order == self.correct:
            self.cb(True)
            self.destroy()
        else:
            messagebox.showwarning("Ошибка", "Капча неверна")
            self.cb(False)




class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DemoApp — Авторизация")
        self.geometry("420x300")
        setup_style(self)
        if not os.path.isdir(CAPTCHA_FOLDER):
            os.makedirs(CAPTCHA_FOLDER, exist_ok=True)
        if not os.path.isdir(EXPORT_FOLDER):
            os.makedirs(EXPORT_FOLDER, exist_ok=True)
        self.captcha_ok = False
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=16, pady=16)
        ttk.Label(frm, text="Авторизация", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=(0, 12))
        ttk.Label(frm, text="Логин:").grid(row=1, column=0, sticky="w")
        self.e_user = ttk.Entry(frm, width=30)
        self.e_user.grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(frm, text="Пароль:").grid(row=2, column=0, sticky="w")
        self.e_pass = ttk.Entry(frm, show="*", width=30)
        self.e_pass.grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Button(frm, text="Пройти капчу", command=self.open_captcha).grid(row=3, column=0, pady=10, sticky="ew")
        ttk.Button(frm, text="Войти", command=self.do_login).grid(row=3, column=1, pady=10, sticky="ew")
        ttk.Button(frm, text="Регистрация", command=self.open_register).grid(row=4, column=0, columnspan=2, pady=8, sticky="ew")
        self.status = ttk.Label(frm, text="Капча не пройдена", foreground="red")
        self.status.grid(row=5, column=0, columnspan=2)
        frm.columnconfigure(1, weight=1)

    def open_captcha(self):
        Captcha2x2(self, self.captcha_callback)

    def captcha_callback(self, ok):
        self.captcha_ok = ok
        if ok:
            self.status.config(text="Капча пройдена", foreground="green")
        else:
            self.status.config(text="Капча не пройдена", foreground="red")

        

    def do_login(self):
        if not self.captcha_ok:
            messagebox.showwarning("Ошибка", "Сначала пройдите капчу")
            return
        u = self.e_user.get().strip()
        p = self.e_pass.get().strip()
        if not u or not p:
            messagebox.showwarning("Ошибка", "Введите логин и пароль")
            return
        try:
            c = get_conn(); cur = c.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (u, p))
            row = cur.fetchone()
            c.close()
            if not row:
                messagebox.showerror("Ошибка", "Неверный логин или пароль")
                return
            if row["is_blocked"]:
                messagebox.showerror("Ошибка", "Пользователь заблокирован")
                return
            if row["role"] == "Администратор":
                AdminWindow(self)
            else:
                UserWindow(self, row["username"])
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))

    def open_register(self):
        RegisterWindow(self)


class RegisterWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Регистрация")
        self.geometry("340x220")
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frm, text="Новый пользователь", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Label(frm, text="Логин:").pack(anchor="w")
        self.e1 = ttk.Entry(frm); self.e1.pack(fill="x", pady=4)
        ttk.Label(frm, text="Пароль:").pack(anchor="w")
        self.e2 = ttk.Entry(frm, show="*"); self.e2.pack(fill="x", pady=4)
        ttk.Button(frm, text="Создать", command=self.create_user).pack(pady=8, fill="x")

    def create_user(self):
        u = self.e1.get().strip(); p = self.e2.get().strip()
        if not u or not p:
            messagebox.showwarning("Ошибка", "Введите данные")
            return
        try:
            c = get_conn(); cur = c.cursor()
            cur.execute("SELECT id FROM users WHERE username=%s", (u,))
            if cur.fetchone():
                messagebox.showwarning("Ошибка", "Логин занят"); c.close(); return
            cur.execute("INSERT INTO users(username,password,role) VALUES(%s,%s,'Пользователь')", (u, p))
            c.commit(); c.close()
            messagebox.showinfo("OK", "Пользователь создан"); self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))


class AdminWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Админ-панель")
        self.geometry("1100x700")
        frame = ttk.Frame(self); frame.pack(fill="both", expand=True, padx=10, pady=10)
        left = ttk.Frame(frame); left.pack(side="left", fill="y", padx=(0, 12))
        ttk.Label(left, text="Пользователи", style="Header.TLabel").pack(pady=(0, 8))
        self.lb = tk.Listbox(left, width=36); self.lb.pack(fill="y", expand=True)
        btns = [("Добавить", self.add_user), ("Редактировать", self.edit_user),
                ("Удалить", self.delete_user), ("Разблокировать", self.unblock_user)]
        for t, cmd in btns: ttk.Button(left, text=t, command=cmd).pack(fill="x", pady=4)
        center = ttk.Frame(frame); center.pack(side="left", fill="both", expand=True)
        ttk.Label(center, text="Просмотр таблиц", style="Header.TLabel").pack(anchor="w")
        top = ttk.Frame(center); top.pack(anchor="w", pady=(6, 6))
        self.table_cb = ttk.Combobox(top, values=["Customers", "Products", "Materials", "Composition", "OrderToProducts", "users"], state="readonly", width=35)
        self.table_cb.pack(side="left", padx=(0, 10))
        ttk.Button(top, text="Загрузить", command=self.load_table).pack(side="left")
        self.tree = ttk.Treeview(center); self.tree.pack(fill="both", expand=True, pady=8)
        right = ttk.Frame(frame); right.pack(side="left", fill="y", padx=(12, 0))
        ttk.Label(right, text="Экспорт", style="Header.TLabel").pack(pady=(0, 8))
        ttk.Button(right, text="PDF: Прайс-лист", command=self.export_price_list).pack(fill="x", pady=4)
        ttk.Button(right, text="PDF: Квитанция", command=self.export_receipt).pack(fill="x", pady=4)
        ttk.Button(right, text="PDF: Счёт", command=self.export_invoice).pack(fill="x", pady=4)
        ttk.Button(right, text="PDF: Карточка (строка)", command=self.export_card_row).pack(fill="x", pady=4)
        self.load_users()

    def load_users(self):
        self.lb.delete(0, tk.END)
        try:
            c = get_conn(); cur = c.cursor(); cur.execute("SELECT id,username,role,is_blocked FROM users ORDER BY id"); rows = cur.fetchall(); c.close()
            self.users = rows
            for u in rows:
                mark = " (Заблокирован)" if u["is_blocked"] else ""
                self.lb.insert(tk.END, f"{u['id']}: {u['username']}{mark}")
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))

    def add_user(self):
        d = UserEditDialog(self, None, "new"); self.load_users()

    def edit_user(self):
        sel = self.lb.curselection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите пользователя"); return
        idx = sel[0]; d = UserEditDialog(self, self.users[idx], "edit"); self.load_users()

    def delete_user(self):
        sel = self.lb.curselection()
        if not sel: return
        idx = sel[0]; uid = self.users[idx]["id"]
        if not messagebox.askyesno("Внимание", "Удалить пользователя?"): return
        try:
            c = get_conn(); cur = c.cursor(); cur.execute("DELETE FROM users WHERE id=%s", (uid,)); c.commit(); c.close(); self.load_users()
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))

    def unblock_user(self):
        sel = self.lb.curselection()
        if not sel: return
        idx = sel[0]; uid = self.users[idx]["id"]
        try:
            c = get_conn(); cur = c.cursor(); cur.execute("UPDATE users SET is_blocked=0 WHERE id=%s", (uid,)); c.commit(); c.close(); self.load_users(); messagebox.showinfo("OK", "Разблокирован")
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))

        


    def load_table(self):
        table = self.table_cb.get()
        if not table:
            return
        try:
            c = get_conn(); cur = c.cursor(); cur.execute(f"SELECT * FROM {table}"); rows = cur.fetchall(); c.close()
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e)); return
        if not rows:
            self.tree.delete(*self.tree.get_children()); self.tree["columns"] = []; return
        cols = list(rows[0].keys())
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = cols; self.tree["show"] = "headings"
        for col in cols:
            self.tree.heading(col, text=col); self.tree.column(col, width=120)
        for r in rows:
            self.tree.insert("", tk.END, values=[r[c] for c in cols])

        start = time.time()
        cur.execute("SELECT * FROM Products")
        rows = cur.fetchall()
        print(f"[METRIC] Load table Products: {time.time() - start:.2f} sec")
        print(f"[METRIC] Rows loaded: {len(rows)}")

    def export_price_list(self):
        try:
            c = get_conn(); cur = c.cursor(); cur.execute("SELECT code, products, description, base_price FROM Products"); rows = cur.fetchall(); c.close()
            if not rows: messagebox.showwarning("Прайс", "Нет данных"); return
            fn = os.path.join(EXPORT_FOLDER, f"price_list_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
            pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 16); pdf.drawString(40, 800, "ПРАЙС-ЛИСТ")
            y = 770; pdf.setFont(PDF_FONT, 11)
            pdf.drawString(40, y, "Код"); pdf.drawString(120, y, "Наименование"); pdf.drawString(380, y, "Цена")
            y -= 18
            for r in rows:
                pdf.drawString(40, y, str(r["code"])); pdf.drawString(120, y, str(r["products"])[:40]); pdf.drawString(380, y, f"{r['base_price']}")
                y -= 18
                if y < 60: pdf.showPage(); pdf.setFont(PDF_FONT, 11); y = 780
            pdf.save(); messagebox.showinfo("OK", f"Прайс создан: {fn}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def export_receipt(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите строку")
            return
        vals = self.tree.item(sel[0])["values"]; cols = self.tree["columns"]; data = dict(zip(cols, vals))
        fn = os.path.join(EXPORT_FOLDER, f"receipt_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 14); pdf.drawString(40, 800, "КВИТАНЦИЯ")
        pdf.setFont(PDF_FONT, 11)
        y = 760
        for k, v in data.items():
            pdf.drawString(40, y, f"{k}: {v}"); y -= 18
        pdf.drawString(40, y - 6, f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}"); pdf.drawString(40, y - 30, "Подпись: ____________________")
        pdf.save(); messagebox.showinfo("OK", f"Квитанция: {fn}")
        

    def export_invoice(self):
        table = self.table_cb.get()
        if table not in ("Products", "OrderToProducts"):
            messagebox.showwarning("Счёт", "Откройте таблицу Products или OrderToProducts и выберите строки")
            return
        sels = self.tree.selection()
        if not sels:
            messagebox.showwarning("Счёт", "Выберите одну или несколько строк")
            return
        items = []
        for s in sels:
            vals = self.tree.item(s)["values"]; cols = self.tree["columns"]; row = dict(zip(cols, vals))
            if table == "Products":
                qty = simpledialog.askinteger("Количество", f"Введите количество для {row.get('products')}", minvalue=1, initialvalue=1)
                if not qty: continue
                price = float(row.get("base_price") or 0)
                items.append((row.get("products"), qty, price))
            else:
                qty = row.get("count") or 1
                pid = row.get("product_id") or row.get("product_id")
                try:
                    c = get_conn(); cur = c.cursor(); cur.execute("SELECT products, base_price FROM Products WHERE products_id=%s", (row.get("product_id"),))
                    pr = cur.fetchone(); c.close()
                    name = pr["products"] if pr else f"product_{row.get('product_id')}"
                    price = float(pr["base_price"]) if pr and pr["base_price"] else 0
                except:
                    name = f"product_{row.get('product_id')}"; price = 0
                items.append((name, float(qty), price))
        if not items:
            messagebox.showwarning("Счёт", "Нет элементов для счёта"); return
        invoice_no = random.randint(10000, 99999)
        fn = os.path.join(EXPORT_FOLDER, f"invoice_{invoice_no}.pdf")
        pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 16); pdf.drawString(40, 800, f"СЧЁТ № {invoice_no}")
        pdf.setFont(PDF_FONT, 11); pdf.drawString(40, 780, f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}")
        y = 740; pdf.drawString(40, y, "Наименование"); pdf.drawString(360, y, "Кол-во"); pdf.drawString(460, y, "Цена"); pdf.drawString(520, y, "Сумма")
        y -= 18; total = 0
        for name, qty, price in items:
            summa = qty * price
            total += summa
            pdf.drawString(40, y, str(name)[:40]); pdf.drawString(360, y, str(qty)); pdf.drawString(460, y, f"{price:.2f}"); pdf.drawString(520, y, f"{summa:.2f}")
            y -= 18
            if y < 60: pdf.showPage(); pdf.setFont(PDF_FONT, 11); y = 780
        pdf.drawString(40, y - 10, f"Итого: {total:.2f} руб.")
        pdf.drawString(40, y - 40, "Ответственный: ____________________")
        pdf.save(); messagebox.showinfo("OK", f"Счёт создан: {fn}")

    def export_card_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Ошибка", "Выберите строку")
            return
        vals = self.tree.item(sel[0])["values"]; cols = self.tree["columns"]; data = dict(zip(cols, vals))
        fn = os.path.join(EXPORT_FOLDER, f"card_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 14); pdf.drawString(40, 800, "КАРТОЧКА")
        pdf.setFont(PDF_FONT, 11); y = 760
        for k, v in data.items():
            pdf.drawString(40, y, f"{k}: {v}"); y -= 18
        pdf.save(); messagebox.showinfo("OK", f"PDF: {fn}")

    def insert_test_data(self):
        try:
            c = get_conn(); cur = c.cursor()
            cur.execute("INSERT INTO Units (unit_name) VALUES ('шт')")
            cur.execute("INSERT INTO Materials (code,name,unit_id,cost,stock_qty) VALUES ('M100','Материал Тест',1,15.5,100)")
            cur.execute("INSERT INTO Products (code,products,description,base_price) VALUES ('P100','Продукт Тест','Описание',250)")
            cur.execute("INSERT INTO Customers (ext_id,name,inn,address,phone,salesman,buyer) VALUES ('C100','Клиент Тест','','Город','+700000000',1,1)")
            cur.execute("INSERT INTO OrderToProducts (customer_id,product_id,unit_id,count) VALUES (1,1,1,2)")
            c.commit(); c.close(); messagebox.showinfo("OK", "Тестовые данные вставлены")
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))


class UserEditDialog(tk.Toplevel):
    def __init__(self, parent, data, mode):
        super().__init__(parent)
        self.data = data; self.mode = mode
        self.title("Пользователь"); self.geometry("320x220")
        frm = ttk.Frame(self); frm.pack(fill="both", expand=True, padx=12, pady=12)
        ttk.Label(frm, text="Логин:").pack(anchor="w"); self.e1 = ttk.Entry(frm); self.e1.pack(fill="x", pady=4)
        ttk.Label(frm, text="Пароль:").pack(anchor="w"); self.e2 = ttk.Entry(frm); self.e2.pack(fill="x", pady=4)
        ttk.Label(frm, text="Роль:").pack(anchor="w"); self.role_cb = ttk.Combobox(frm, values=["Администратор", "Пользователь"], state="readonly"); self.role_cb.pack(fill="x", pady=4)
        self.block_var = tk.BooleanVar(); ttk.Checkbutton(frm, text="Заблокирован", variable=self.block_var).pack(pady=4)
        if mode == "edit" and data:
            self.e1.insert(0, data["username"]); self.e2.insert(0, data["password"]); self.role_cb.set(data["role"]); self.block_var.set(data["is_blocked"])
        ttk.Button(frm, text="Сохранить", command=self.save).pack(pady=8, fill="x")

    def save(self):
        u = self.e1.get().strip(); p = self.e2.get().strip(); r = self.role_cb.get(); b = self.block_var.get()
        try:
            c = get_conn(); cur = c.cursor()
            if self.mode == "new":
                cur.execute("INSERT INTO users(username,password,role,is_blocked) VALUES(%s,%s,%s,%s)", (u, p, r, b))
            else:
                cur.execute("UPDATE users SET username=%s,password=%s,role=%s,is_blocked=%s WHERE id=%s", (u, p, r, b, self.data["id"]))
            c.commit(); c.close(); self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e))
        start = time.time()
        c.save()
        print(f"[METRIC] PDF generation: {time.time() - start:.2f} sec")


class UserWindow(tk.Toplevel):
    def __init__(self, parent, username):
        super().__init__(parent)
        self.title(f"Рабочий стол - {username}"); self.geometry("900x600")
        ttk.Label(self, text=f"Пользователь: {username}", style="Header.TLabel").pack(pady=8)
        frm = ttk.Frame(self); frm.pack(fill="both", expand=True, padx=10, pady=10)
        self.table_cb = ttk.Combobox(frm, values=["Customers", "Products", "Materials", "Composition", "OrderToProducts"], state="readonly")
        self.table_cb.pack(anchor="w")
        ttk.Button(frm, text="Загрузить", command=self.load_table).pack(pady=6, anchor="w")
        self.tree = ttk.Treeview(frm); self.tree.pack(fill="both", expand=True)
        btns = ttk.Frame(self); btns.pack(pady=6)
        ttk.Button(btns, text="Печать карточки (PDF)", command=self.export_card).pack(side="left", padx=6)
        ttk.Button(btns, text="Квитанция (PDF)", command=self.export_receipt).pack(side="left", padx=6)
        ttk.Button(btns, text="Счёт (PDF)", command=self.export_invoice).pack(side="left", padx=6)

    def load_table(self):
        table = self.table_cb.get()
        if not table: return
        try:
            c = get_conn(); cur = c.cursor(); cur.execute(f"SELECT * FROM {table}"); rows = cur.fetchall(); c.close()
        except Exception as e:
            messagebox.showerror("Ошибка DB", str(e)); return
        if not rows:
            self.tree.delete(*self.tree.get_children()); self.tree["columns"] = []; return
        cols = list(rows[0].keys())
        self.tree.delete(*self.tree.get_children()); self.tree["columns"] = cols; self.tree["show"] = "headings"
        for col in cols:
            self.tree.heading(col, text=col); self.tree.column(col, width=120)
        for r in rows:
            self.tree.insert("", tk.END, values=[r[c] for c in cols])

    def export_card(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Ошибка", "Выберите строку"); return
        vals = self.tree.item(sel[0])["values"]; cols = self.tree["columns"]; data = dict(zip(cols, vals))
        fn = os.path.join(EXPORT_FOLDER, f"card_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 14); pdf.drawString(40, 800, "КАРТОЧКА")
        pdf.setFont(PDF_FONT, 11); y = 760
        for k, v in data.items():
            pdf.drawString(40, y, f"{k}: {v}"); y -= 18
        pdf.save(); messagebox.showinfo("OK", f"PDF: {fn}")

    def export_receipt(self):
        sel = self.tree.selection()
        if not sel: messagebox.showwarning("Ошибка", "Выберите строку"); return
        vals = self.tree.item(sel[0])["values"]; cols = self.tree["columns"]; data = dict(zip(cols, vals))
        fn = os.path.join(EXPORT_FOLDER, f"receipt_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf")
        pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 14); pdf.drawString(40, 800, "КВИТАНЦИЯ")
        pdf.setFont(PDF_FONT, 11); y = 760
        for k, v in data.items():
            pdf.drawString(40, y, f"{k}: {v}"); y -= 18
        pdf.drawString(40, y - 6, f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}"); pdf.drawString(40, y - 30, "Подпись: ____________________")
        pdf.save(); messagebox.showinfo("OK", f"Квитанция: {fn}")

    def export_invoice(self):
        table = self.table_cb.get()
        if table != "Products":
            messagebox.showwarning("Счёт", "Откройте таблицу Products и выберите товары")
            return
        sels = self.tree.selection()
        if not sels:
            messagebox.showwarning("Счёт", "Выберите товары"); return
        items = []
        for s in sels:
            vals = self.tree.item(s)["values"]; cols = self.tree["columns"]; row = dict(zip(cols, vals))
            qty = simpledialog.askinteger("Количество", f"Введите количество для {row.get('products')}", minvalue=1, initialvalue=1)
            if not qty: continue
            price = float(row.get("base_price") or 0)
            items.append((row.get("products"), qty, price))
        if not items:
            messagebox.showwarning("Счёт", "Нет позиций для счёта"); return
        invoice_no = random.randint(10000, 99999)
        fn = os.path.join(EXPORT_FOLDER, f"invoice_{invoice_no}.pdf")
        pdf = canvas.Canvas(fn, pagesize=A4); pdf.setFont(PDF_FONT, 16); pdf.drawString(40, 800, f"СЧЁТ № {invoice_no}")
        pdf.setFont(PDF_FONT, 11); pdf.drawString(40, 780, f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y')}")
        y = 740; pdf.drawString(40, y, "Наименование"); pdf.drawString(360, y, "Кол-во"); pdf.drawString(460, y, "Цена"); pdf.drawString(520, y, "Сумма")
        y -= 18; total = 0
        for name, qty, price in items:
            summa = qty * price; total += summa
            pdf.drawString(40, y, str(name)[:40]); pdf.drawString(360, y, str(qty)); pdf.drawString(460, y, f"{price:.2f}"); pdf.drawString(520, y, f"{summa:.2f}")
            y -= 18
            if y < 60: pdf.showPage(); pdf.setFont(PDF_FONT, 11); y = 780
        pdf.drawString(40, y - 10, f"Итого: {total:.2f} руб."); pdf.drawString(40, y - 40, "Подпись: ____________________")
        pdf.save(); messagebox.showinfo("OK", f"Счёт создан: {fn}")


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
