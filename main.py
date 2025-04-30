import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import sqlite3
import os
from tkcalendar import Calendar, DateEntry
from PIL import Image, ImageTk
from datetime import datetime

def setup_database():
    conn = sqlite3.connect("studio.db")
    cursor = conn.cursor()

    # пользователи
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            fullname TEXT
        )
    """)

    # релизы
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            release_type TEXT NOT NULL,
            cover TEXT,
            tracks TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)

    # расписание
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL
        )
    """)

    # пользователи добавление
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users = [
            ("user1", "pass1", "user", "Мудродубов Григорий Иванович"),
            ("admin", "pass1", "admin", "Администратор Системы")
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role, fullname) VALUES (?, ?, ?, ?)",
            users
        )

    # статусы релизов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS release_status (
            release_id INTEGER PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'В производстве',
            FOREIGN KEY (release_id) REFERENCES releases(id)
        )
    """)

    # точки продаж
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL
        )
    """)

    # добавленные точки
    cursor.execute("SELECT COUNT(*) FROM sales_points")
    if cursor.fetchone()[0] == 0:
        points = [
            ("Алматы", "ул. Абая, 1"),
            ("Москва", "ул. Тверская, 10"),
            ("Париж", "ул. Монмартр, 5")
        ]
        cursor.executemany("INSERT INTO sales_points (name, address) VALUES (?, ?)", points)

    # продажи
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            release_id INTEGER NOT NULL,
            point_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (release_id) REFERENCES releases(id),
            FOREIGN KEY (point_id) REFERENCES sales_points(id)
        )
    """)

    conn.commit()
    conn.close()

class SalesManager:
    def __init__(self, parent):
        self.parent = parent

    def get_release_status(self, release_id):
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM release_status WHERE release_id=?", (release_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else "В производстве"

    def set_release_status(self, release_id, status):
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO release_status (release_id, status) 
            VALUES (?, ?)
        """, (release_id, status))
        conn.commit()
        conn.close()

    def get_sales_points(self):
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, address FROM sales_points")
        points = cursor.fetchall()
        conn.close()
        return points

    def add_sale(self, release_id, point_id, quantity):
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sales (release_id, point_id, quantity, date)
            VALUES (?, ?, ?, ?)
        """, (release_id, point_id, quantity, date))
        conn.commit()
        conn.close()

    def get_sales(self):
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, r.title, sp.name, sp.address, s.quantity, s.date 
            FROM sales s
            JOIN releases r ON s.release_id = r.id
            JOIN sales_points sp ON s.point_id = sp.id
            ORDER BY s.date DESC
        """)
        sales = cursor.fetchall()
        conn.close()
        return sales

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.sales_manager = SalesManager(self)
        self.root.title("Студия звукозаписи — Вход")

        tk.Label(root, text="Добро пожаловать!", font=("Arial", 14)).pack(pady=10)

        tk.Label(root, text="Логин:").pack()
        self.username_entry = tk.Entry(root)
        self.username_entry.pack()

        tk.Label(root, text="Пароль:").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        tk.Button(root, text="Войти", command=self.login).pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, fullname FROM users WHERE username=? AND password=?",
            (username, password)
        )
        result = cursor.fetchone()
        conn.close()

        if result:
            role, fullname = result
            self.root.withdraw()

            if role == "admin":
                self.open_admin_window(fullname)
            else:
                self.open_user_window(username, fullname)
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")

    def open_user_window(self, username, fullname):
        user_window = tk.Toplevel()
        user_window.title("Панель пользователя")
        user_window.geometry("1000x800")

        self.current_username = username

        notebook = ttk.Notebook(user_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Вкладка релизов
        releases_frame = ttk.Frame(notebook)
        notebook.add(releases_frame, text="Мои релизы")

        # Вкладка расписания
        schedule_frame = ttk.Frame(notebook)
        notebook.add(schedule_frame, text="Расписание студии")

        # Новая вкладка с продажами для пользователя
        user_sales_frame = ttk.Frame(notebook)
        notebook.add(user_sales_frame, text="Продажи")

        # === Содержимое вкладки релизов ===
        tk.Label(releases_frame, text=f"Релизы пользователя {fullname}", font=("Arial", 12)).pack(pady=10)

        self.user_releases_listbox = tk.Listbox(releases_frame, width=80)
        self.user_releases_listbox.pack(pady=10, fill=tk.BOTH, expand=True)

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, release_type FROM releases WHERE username=?
        """, (username,))
        for title, rtype in cursor.fetchall():
            self.user_releases_listbox.insert(tk.END, f"{title} — {rtype}")
        conn.close()

        self.user_releases_listbox.bind("<Double-Button-1>", self.show_user_release_details)

        # === Содержимое вкладки расписания ===
        tk.Label(schedule_frame, text="Расписание студии", font=("Arial", 12)).pack(pady=10)

        main_frame = ttk.Frame(schedule_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Календарь
        calendar_frame = ttk.Frame(main_frame)
        calendar_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(calendar_frame, text="Выберите дату:").pack()
        self.user_calendar = Calendar(calendar_frame, selectmode="day", date_pattern="dd.MM.yyyy")
        self.user_calendar.pack(pady=5)

        # Список событий
        events_frame = ttk.Frame(main_frame)
        events_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(events_frame, text="События:").pack()
        self.events_listbox = tk.Listbox(events_frame, width=50, height=15)
        self.events_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        self.events_listbox.bind("<Double-Button-1>", self.show_selected_event_details)

        self.event_ids = []

        self.user_calendar.bind("<<CalendarSelected>>", lambda e: self.show_events_for_selected_date())

        self.show_events_for_selected_date()

        # === Содержимое вкладки продаж ===
        tk.Label(user_sales_frame, text="Продажи ваших релизов", font=("Arial", 12)).pack(pady=10)

        self.user_sales_tree = ttk.Treeview(user_sales_frame, columns=("release", "point", "quantity", "date"),
                                            show="headings")
        self.user_sales_tree.heading("release", text="Релиз")
        self.user_sales_tree.heading("point", text="Точка продаж")
        self.user_sales_tree.heading("quantity", text="Количество")
        self.user_sales_tree.heading("date", text="Дата")
        self.user_sales_tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.update_user_sales_list()

        tk.Button(user_window, text="Выйти", command=self.logout_user).pack(pady=10)

    def show_events_for_selected_date(self):
        selected_date = self.user_calendar.get_date()

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()

        date_pattern = f"{selected_date}%"
        cursor.execute("SELECT id, date, description FROM schedule WHERE date LIKE ?", (date_pattern,))
        events = cursor.fetchall()
        conn.close()

        self.events_listbox.delete(0, tk.END)
        self.event_ids.clear()

        if events:
            for event_id, date, description in events:
                short_desc = description[:40] + "..." if len(description) > 40 else description
                self.events_listbox.insert(tk.END, f"{date}: {short_desc}")
                self.event_ids.append(event_id)
        else:
            self.events_listbox.insert(tk.END, "События на выбранную дату отсутствуют")

    def show_selected_event_details(self, event):
        selection = self.events_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_text = self.events_listbox.get(index)

        if "отсутствуют" in selected_text:
            return

        if index < len(self.event_ids):
            event_id = self.event_ids[index]
        else:
            return

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT date, description FROM schedule WHERE id=?", (event_id,))
        event = cursor.fetchone()
        conn.close()

        if not event:
            return

        date, description = event

        detail_window = tk.Toplevel()
        detail_window.title(f"Детали расписания на {date}")
        detail_window.geometry("500x400")

        tk.Label(detail_window, text=f"Дата: {date}", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(detail_window, text="Описание:").pack()
        desc_text = tk.Text(detail_window, height=12, width=50)
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)
        desc_text.pack(pady=10)

        tk.Button(detail_window, text="Закрыть", command=detail_window.destroy).pack(pady=10)

    def open_admin_window(self, fullname):
        admin_window = tk.Toplevel()
        admin_window.title("Панель администратора")
        admin_window.geometry("1000x800")

        self.admin_window = admin_window

        notebook = ttk.Notebook(admin_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        releases_frame = ttk.Frame(notebook)
        notebook.add(releases_frame, text="Управление релизами")

        schedule_frame = ttk.Frame(notebook)
        notebook.add(schedule_frame, text="Управление расписанием")

        status_frame = ttk.Frame(notebook)
        notebook.add(status_frame, text="Статусы релизов")

        sales_frame = ttk.Frame(notebook)
        notebook.add(sales_frame, text="Продажи")

        # === Вкладка релизов ===
        tk.Label(releases_frame, text="Выберите пользователя для добавления релиза:").pack()
        self.user_choice = tk.StringVar()
        self.user_menu = tk.OptionMenu(releases_frame, self.user_choice, *self.get_users())
        self.user_menu.pack()

        tk.Label(releases_frame, text="Название релиза:").pack()
        self.title_entry = tk.Entry(releases_frame, width=50)
        self.title_entry.pack()

        tk.Label(releases_frame, text="Тип релиза:").pack()
        self.type_var = tk.StringVar(value="Сингл")
        tk.OptionMenu(releases_frame, self.type_var, "Сингл", "EP", "Альбом").pack()

        self.cover_path = ""
        tk.Button(releases_frame, text="Выбрать обложку", command=self.choose_cover).pack()

        tk.Label(releases_frame, text="Песни:").pack()
        self.tracks_text = tk.Text(releases_frame, height=5, width=60)
        self.tracks_text.pack()
        tk.Label(releases_frame, text="Название — Длительность").pack()

        tk.Button(releases_frame, text="Добавить релиз", command=self.add_release).pack(pady=10)

        tk.Label(releases_frame, text="Список релизов пользователя:").pack()
        self.releases_listbox = tk.Listbox(releases_frame, width=80, height=5)
        self.releases_listbox.pack(pady=10)
        self.releases_listbox.bind("<Double-Button-1>", self.show_release_details)

        self.user_choice.trace_add("write", self.update_release_list)

        # === Вкладка расписания ===
        tk.Label(schedule_frame, text="Расписание студии", font=("Arial", 12)).pack(pady=10)

        tk.Button(schedule_frame, text="Добавить новое событие",
                  command=self.open_add_schedule_window).pack(pady=10)

        tk.Label(schedule_frame, text="Текущее расписание:").pack()
        self.schedule_listbox = tk.Listbox(schedule_frame, width=80, height=15)
        self.schedule_listbox.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.schedule_listbox.bind("<Double-Button-1>", self.show_schedule_details)

        self.update_schedule_list()

        # === Вкладка статусов релизов ===
        tk.Label(status_frame, text="Выберите релиз для изменения статуса:").pack(pady=10)

        self.status_release_listbox = tk.Listbox(status_frame, width=80, height=10)
        self.status_release_listbox.pack(pady=10)
        self.update_status_release_list()

        tk.Label(status_frame, text="Текущий статус:").pack()
        self.current_status_label = tk.Label(status_frame, text="", font=("Arial", 12))
        self.current_status_label.pack()

        self.status_var = tk.StringVar(value="В производстве")
        status_options = ["В производстве", "Готов", "Архив"]
        status_menu = tk.OptionMenu(status_frame, self.status_var, *status_options)
        status_menu.pack(pady=10)

        tk.Button(status_frame, text="Обновить статус", command=self.update_release_status).pack(pady=10)

        self.status_release_listbox.bind("<<ListboxSelect>>", self.show_release_status)

        # === Вкладка продаж ===
        tk.Label(sales_frame, text="Добавить продажу:").pack(pady=10)

        tk.Label(sales_frame, text="Выберите релиз:").pack()
        self.sale_release_listbox = tk.Listbox(sales_frame, width=80, height=5)
        self.sale_release_listbox.pack(pady=5)
        self.update_sale_release_list()

        tk.Label(sales_frame, text="Выберите точку продаж:").pack()
        self.sale_point_var = tk.StringVar()
        self.sale_point_menu = tk.OptionMenu(sales_frame, self.sale_point_var, "")
        self.sale_point_menu.pack()
        self.update_sale_points_menu()

        tk.Label(sales_frame, text="Количество:").pack()
        self.sale_quantity_entry = tk.Entry(sales_frame)
        self.sale_quantity_entry.pack()

        tk.Button(sales_frame, text="Добавить продажу", command=self.add_sale).pack(pady=10)

        tk.Label(sales_frame, text="История продаж:").pack(pady=10)
        self.sales_tree = ttk.Treeview(sales_frame, columns=("release", "point", "quantity", "date"), show="headings")
        self.sales_tree.heading("release", text="Релиз")
        self.sales_tree.heading("point", text="Точка продаж")
        self.sales_tree.heading("quantity", text="Количество")
        self.sales_tree.heading("date", text="Дата")
        self.sales_tree.pack(fill="both", expand=True, pady=10)
        self.update_sales_list()

        tk.Button(admin_window, text="Выйти", command=self.logout_admin).pack(pady=10)

    def open_add_schedule_window(self):
        schedule_window = tk.Toplevel(self.admin_window)
        schedule_window.title("Добавление события в расписание")
        schedule_window.geometry("500x400")

        tk.Label(schedule_window, text="Выберите дату:", font=("Arial", 10)).pack(pady=(20, 5))
        self.schedule_date_entry = DateEntry(schedule_window, width=12, background='darkblue',
                                             foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
        self.schedule_date_entry.pack(pady=5)

        tk.Label(schedule_window, text="Время:", font=("Arial", 10)).pack(pady=(10, 5))
        self.schedule_time_entry = tk.Entry(schedule_window, width=30)
        self.schedule_time_entry.pack(pady=5)

        tk.Label(schedule_window, text="Описание события:", font=("Arial", 10)).pack(pady=(10, 5))
        self.schedule_description_text = tk.Text(schedule_window, height=10, width=50)
        self.schedule_description_text.pack(pady=10)

        buttons_frame = tk.Frame(schedule_window)
        buttons_frame.pack(pady=20)

        tk.Button(buttons_frame, text="Сохранить", command=lambda: self.add_schedule_item(schedule_window)).pack(
            side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="Отмена", command=schedule_window.destroy).pack(side=tk.LEFT, padx=10)

    def add_schedule_item(self, window):
        date = self.schedule_date_entry.get()
        time = self.schedule_time_entry.get()
        description = self.schedule_description_text.get("1.0", tk.END).strip()

        if not date or not description:
            messagebox.showerror("Ошибка", "Укажите дату и описание")
            return

        datetime_str = f"{date} {time}" if time else date

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO schedule (date, description) VALUES (?, ?)
        """, (datetime_str, description))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успех", "Запись в расписание добавлена")
        window.destroy()
        self.update_schedule_list()

    def edit_schedule_item(self, item_id, date, description, parent_window):
        parent_window.destroy()

        date_parts = date.split(' ', 1)
        date_only = date_parts[0]
        time_only = date_parts[1] if len(date_parts) > 1 else ""

        edit_window = tk.Toplevel(self.admin_window)
        edit_window.title(f"Редактирование расписания")
        edit_window.geometry("500x400")

        tk.Label(edit_window, text="Выберите дату:", font=("Arial", 10)).pack(pady=(20, 5))
        date_cal = DateEntry(edit_window, width=12, background='darkblue',
                             foreground='white', borderwidth=2, date_pattern='dd.MM.yyyy')
        try:
            day, month, year = map(int, date_only.split('.'))
            date_cal.set_date(f"{year}-{month:02d}-{day:02d}")
        except:
            pass
        date_cal.pack(pady=5)

        tk.Label(edit_window, text="Время (ЧЧ:ММ):", font=("Arial", 10)).pack(pady=(10, 5))
        time_entry = tk.Entry(edit_window, width=30)
        time_entry.insert(0, time_only)
        time_entry.pack(pady=5)

        tk.Label(edit_window, text="Описание события:", font=("Arial", 10)).pack(pady=(10, 5))
        description_text = tk.Text(edit_window, height=10, width=50)
        description_text.insert("1.0", description)
        description_text.pack(pady=10)

        def save_changes():
            new_date = date_cal.get()
            new_time = time_entry.get()
            new_description = description_text.get("1.0", tk.END).strip()

            if not new_date or not new_description:
                messagebox.showerror("Ошибка", "Укажите дату и описание")
                return

            new_datetime_str = f"{new_date} {new_time}" if new_time else new_date

            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE schedule SET date=?, description=? WHERE id=?
            """, (new_datetime_str, new_description, item_id))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Информация о расписании обновлена")
            edit_window.destroy()
            self.update_schedule_list()

        buttons_frame = tk.Frame(edit_window)
        buttons_frame.pack(pady=20)

        tk.Button(buttons_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="Отмена", command=edit_window.destroy).pack(side=tk.LEFT, padx=10)

    def delete_schedule_item(self, item_id, parent_window):
        if messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить эту запись?"):
            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedule WHERE id=?", (item_id,))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Запись успешно удалена")
            parent_window.destroy()
            self.update_schedule_list()

    def update_schedule_list(self):
        if hasattr(self, 'schedule_listbox'):
            self.schedule_listbox.delete(0, tk.END)
            self.schedule_ids = []

            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, date, description FROM schedule ORDER BY date")
            for id, date, description in cursor.fetchall():
                short_desc = description[:50] + "..." if len(description) > 50 else description
                self.schedule_listbox.insert(tk.END, f"{date}: {short_desc}")
                self.schedule_ids.append(id)
            conn.close()

    def show_schedule_details(self, event):
        selection = self.schedule_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        if hasattr(self, 'schedule_ids') and index < len(self.schedule_ids):
            item_id = self.schedule_ids[index]
        else:
            messagebox.showerror("Ошибка", "Не удалось определить ID события")
            return

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT date, description FROM schedule WHERE id=?", (item_id,))
        schedule_item = cursor.fetchone()
        conn.close()

        if not schedule_item:
            messagebox.showerror("Ошибка", "Событие не найдено")
            return

        date, description = schedule_item

        detail_window = tk.Toplevel(self.admin_window)
        detail_window.title(f"Детали расписания на {date}")
        detail_window.geometry("500x400")

        tk.Label(detail_window, text=f"Дата: {date}", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(detail_window, text="Описание:").pack()
        desc_text = tk.Text(detail_window, height=12, width=50)
        desc_text.insert(tk.END, description)
        desc_text.config(state=tk.DISABLED)
        desc_text.pack(pady=10)

        buttons_frame = tk.Frame(detail_window)
        buttons_frame.pack(pady=10)

        tk.Button(
            buttons_frame,
            text="Редактировать",
            command=lambda: self.edit_schedule_item(item_id, date, description, detail_window)
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="Удалить",
            command=lambda: self.delete_schedule_item(item_id, detail_window)
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="Закрыть",
            command=detail_window.destroy
        ).pack(side=tk.LEFT, padx=10)

    def get_users(self):
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE role != 'admin'")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users

    def choose_cover(self):
        path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp")]
        )
        if path:
            self.cover_path = path
            try:
                if hasattr(self, 'cover_preview_label'):
                    self.cover_preview_label.destroy()

                frame = self.user_menu.master

                img = Image.open(path)
                img = img.resize((100, 100))
                photo = ImageTk.PhotoImage(img)
                self.cover_preview_label = tk.Label(frame, image=photo)
                self.cover_preview_label.image = photo
                self.cover_preview_label.pack(pady=5)

                if hasattr(self, 'cover_filename_label'):
                    self.cover_filename_label.destroy()

                self.cover_filename_label = tk.Label(frame, text=os.path.basename(path))
                self.cover_filename_label.pack()

                messagebox.showinfo("Обложка выбрана", os.path.basename(path))
            except Exception as e:
                self.cover_path = path
                messagebox.showinfo("Обложка выбрана", os.path.basename(path))

    def add_release(self):
        username = self.user_choice.get()
        title = self.title_entry.get()
        release_type = self.type_var.get()
        cover = self.cover_path
        tracks = self.tracks_text.get("1.0", tk.END).strip()

        if not username or not title:
            messagebox.showerror("Ошибка", "Выберите пользователя и введите название релиза.")
            return

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO releases (username, title, release_type, cover, tracks)
            VALUES (?, ?, ?, ?, ?)
        """, (username, title, release_type, cover, tracks))
        conn.commit()
        conn.close()

        messagebox.showinfo("Успех", "Релиз успешно добавлен.")
        self.title_entry.delete(0, tk.END)
        self.tracks_text.delete("1.0", tk.END)
        self.update_release_list()

    def update_release_list(self, *args):
        self.releases_listbox.delete(0, tk.END)
        username = self.user_choice.get()
        if not username:
            return

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, release_type FROM releases WHERE username=?
        """, (username,))
        for title, rtype in cursor.fetchall():
            self.releases_listbox.insert(tk.END, f"{title} — {rtype}")
        conn.close()

    def show_release_details(self, event):
        selection = self.releases_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_text = self.releases_listbox.get(index)
        title = selected_text.split(" — ")[0]
        username = self.user_choice.get()

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.title, r.release_type, r.cover, r.tracks, rs.status
            FROM releases r
            LEFT JOIN release_status rs ON r.id = rs.release_id
            WHERE r.username=? AND r.title=?
        """, (username, title))
        release = cursor.fetchone()
        conn.close()

        if not release:
            return

        release_id, title, release_type, cover, tracks, status = release
        status = status if status else "В производстве"

        detail_window = tk.Toplevel()
        detail_window.title(f"Детали релиза: {title}")
        detail_window.geometry("600x600")

        tk.Label(detail_window, text=title, font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(detail_window, text=f"Тип: {release_type}").pack()
        tk.Label(detail_window, text=f"Статус: {status}",
                 fg='green' if status == "Готов" else 'blue' if status == "В производстве" else 'gray').pack()

        if cover and os.path.exists(cover):
            try:
                img = Image.open(cover)
                img = img.resize((300, 300))
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(detail_window, image=photo)
                img_label.image = photo
                img_label.pack(pady=10)
            except Exception as e:
                tk.Label(detail_window, text=f"Ошибка загрузки изображения: {str(e)}").pack()
        else:
            tk.Label(detail_window, text="Обложка отсутствует").pack(pady=10)

        tk.Label(detail_window, text="Треки:").pack()
        track_list = tk.Text(detail_window, height=10, width=70)
        track_list.insert(tk.END, tracks if tracks else "Треки не добавлены")
        track_list.config(state=tk.DISABLED)
        track_list.pack(pady=10)

        buttons_frame = tk.Frame(detail_window)
        buttons_frame.pack(pady=10)

        tk.Button(
            buttons_frame,
            text="Редактировать",
            command=lambda: self.edit_release(username, title, release_type, cover, tracks, detail_window)
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="Удалить",
            command=lambda: self.delete_release(username, title, detail_window)
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            buttons_frame,
            text="Закрыть",
            command=detail_window.destroy
        ).pack(side=tk.LEFT, padx=10)

    def show_user_release_details(self, event):
        selection = self.user_releases_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_text = self.user_releases_listbox.get(index)
        title = selected_text.split(" — ")[0]

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.title, r.release_type, r.cover, r.tracks, rs.status 
            FROM releases r
            LEFT JOIN release_status rs ON r.id = rs.release_id
            WHERE r.username=? AND r.title=?
        """, (self.current_username, title))
        release = cursor.fetchone()
        conn.close()

        if not release:
            return

        release_id, title, release_type, cover, tracks, status = release
        status = status if status else "В производстве"

        detail_window = tk.Toplevel()
        detail_window.title(f"Детали релиза: {title}")
        detail_window.geometry("600x600")

        tk.Label(detail_window, text=title, font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(detail_window, text=f"Тип: {release_type}").pack()
        tk.Label(detail_window, text=f"Статус: {status}",
                 fg='green' if status == "Готов" else 'blue' if status == "В производстве" else 'gray').pack()

        if cover and os.path.exists(cover):
            try:
                img = Image.open(cover)
                img = img.resize((300, 300))
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(detail_window, image=photo)
                img_label.image = photo
                img_label.pack(pady=10)
            except Exception:
                tk.Label(detail_window, text="Ошибка загрузки обложки").pack()

        tk.Label(detail_window, text="Треки:").pack()
        track_list = tk.Text(detail_window, height=10, width=70)
        track_list.insert(tk.END, tracks)
        track_list.config(state=tk.DISABLED)
        track_list.pack(pady=10)

    def delete_release(self, username, title, window=None):
        if messagebox.askyesno("Подтверждение", f"Действительно удалить релиз '{title}'?"):
            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM releases WHERE username=? AND title=?", (username, title))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Релиз успешно удален")
            if window:
                window.destroy()
            self.update_release_list()

    def edit_release(self, username, original_title, release_type, cover, tracks, window=None):
        if window:
            window.destroy()

        edit_window = tk.Toplevel(self.admin_window)
        edit_window.title(f"Редактирование релиза: {original_title}")
        edit_window.geometry("600x600")

        tk.Label(edit_window, text="Название релиза:").pack(pady=(10, 5))
        title_entry = tk.Entry(edit_window, width=50)
        title_entry.insert(0, original_title)
        title_entry.pack()

        tk.Label(edit_window, text="Тип релиза:").pack(pady=(10, 5))
        type_var = tk.StringVar(value=release_type)
        tk.OptionMenu(edit_window, type_var, "Сингл", "EP", "Альбом").pack()

        tk.Label(edit_window, text="Текущая обложка:").pack(pady=(10, 5))
        img_label = None
        cover_path_label = tk.Label(edit_window, text=cover if cover else "Обложка не выбрана")
        cover_path_label.pack()

        if cover and os.path.exists(cover):
            try:
                img = Image.open(cover)
                img = img.resize((200, 200))
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(edit_window, image=photo)
                img_label.image = photo
                img_label.pack(pady=5)
            except Exception:
                tk.Label(edit_window, text="Ошибка загрузки изображения").pack()
        else:
            tk.Label(edit_window, text="Обложка не выбрана").pack()

        cover_path_var = tk.StringVar(value=cover if cover else "")

        def choose_new_cover():
            path = filedialog.askopenfilename(
                filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp")]
            )
            if path:
                cover_path_var.set(path)
                try:
                    img = Image.open(path)
                    img = img.resize((200, 200))
                    photo = ImageTk.PhotoImage(img)

                    nonlocal img_label
                    if img_label:
                        img_label.config(image=photo)
                        img_label.image = photo
                    else:
                        img_label = tk.Label(edit_window, image=photo)
                        img_label.image = photo
                        img_label.pack(pady=5)

                    cover_path_label.config(text=path)
                    messagebox.showinfo("Обложка выбрана", os.path.basename(path))
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {e}")

        tk.Button(edit_window, text="Изменить обложку", command=choose_new_cover).pack(pady=10)

        tk.Label(edit_window, text="Песни:").pack(pady=(10, 5))
        tk.Label(edit_window, text="Формат:").pack()
        tracks_text = tk.Text(edit_window, height=10, width=60)
        if tracks:
            tracks_text.insert("1.0", tracks)
        tracks_text.pack(pady=10)

        buttons_frame = tk.Frame(edit_window)
        buttons_frame.pack(pady=10)

        def save_changes():
            new_title = title_entry.get()
            new_type = type_var.get()
            new_cover = cover_path_var.get()
            new_tracks = tracks_text.get("1.0", tk.END).strip()

            if not new_title:
                messagebox.showerror("Ошибка", "Название релиза не может быть пустым")
                return

            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()

            if new_title != original_title:
                cursor.execute(
                    "SELECT COUNT(*) FROM releases WHERE username=? AND title=?",
                    (username, new_title)
                )
                if cursor.fetchone()[0] > 0:
                    messagebox.showerror(
                        "Ошибка",
                        f"Релиз с названием '{new_title}' уже существует у этого пользователя"
                    )
                    conn.close()
                    return

            cursor.execute("""
                UPDATE releases 
                SET title=?, release_type=?, cover=?, tracks=? 
                WHERE username=? AND title=?
            """, (new_title, new_type, new_cover, new_tracks, username, original_title))
            conn.commit()
            conn.close()

            messagebox.showinfo("Успех", "Релиз успешно обновлен")
            edit_window.destroy()
            self.update_release_list()

        tk.Button(buttons_frame, text="Сохранить", command=save_changes).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="Отмена", command=edit_window.destroy).pack(side=tk.LEFT, padx=10)

    def update_status_release_list(self):
        self.status_release_listbox.delete(0, tk.END)
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.title, r.release_type, rs.status 
            FROM releases r
            LEFT JOIN release_status rs ON r.id = rs.release_id
            ORDER BY r.title
        """)
        for id, title, rtype, status in cursor.fetchall():
            status = status if status else "В производстве"
            self.status_release_listbox.insert(tk.END, f"{title} — {rtype} ({status})")
            self.status_release_listbox.itemconfig(tk.END, {'fg': 'green' if status == "Готов" else 'blue' if status == "В производстве" else 'gray'})
        conn.close()

    def show_release_status(self, event):
        selection = self.status_release_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        selected_text = self.status_release_listbox.get(index)
        title = selected_text.split(" — ")[0]

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, rs.status 
            FROM releases r
            LEFT JOIN release_status rs ON r.id = rs.release_id
            WHERE r.title=?
        """, (title,))
        result = cursor.fetchone()
        conn.close()

        if result:
            release_id, status = result
            self.current_release_id = release_id
            status = status if status else "В производстве"
            self.current_status_label.config(text=status)
            self.status_var.set(status)

    def update_release_status(self):
        if not hasattr(self, 'current_release_id'):
            messagebox.showerror("Ошибка", "Выберите релиз")
            return

        new_status = self.status_var.get()
        self.sales_manager.set_release_status(self.current_release_id, new_status)
        messagebox.showinfo("Успех", "Статус релиза обновлен")
        self.update_status_release_list()
        self.current_status_label.config(text=new_status)

    def update_sale_release_list(self):
        self.sale_release_listbox.delete(0, tk.END)
        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, r.title, r.release_type, rs.status 
            FROM releases r
            LEFT JOIN release_status rs ON r.id = rs.release_id
            WHERE rs.status = 'Готов' OR rs.status IS NULL
            ORDER BY r.title
        """)
        for id, title, rtype, status in cursor.fetchall():
            status = status if status else "В производстве"
            self.sale_release_listbox.insert(tk.END, f"{title} — {rtype} ({status})")
            if status == "Готов":
                self.sale_release_listbox.itemconfig(tk.END, {'fg': 'green'})
        conn.close()

    def update_sale_points_menu(self):
        points = self.sales_manager.get_sales_points()
        menu = self.sale_point_menu["menu"]
        menu.delete(0, "end")

        self.sale_points = []
        for point_id, name, address in points:
            self.sale_points.append((point_id, name, address))
            menu.add_command(label=f"{name} ({address})",
                            command=lambda v=(point_id, name, address): self.sale_point_var.set(f"{v[1]} ({v[2]})"))

        if points:
            self.sale_point_var.set(f"{points[0][1]} ({points[0][2]})")

    def add_sale(self):
        selection = self.sale_release_listbox.curselection()
        if not selection:
            messagebox.showerror("Ошибка", "Выберите релиз")
            return

        index = selection[0]
        selected_text = self.sale_release_listbox.get(index)
        title = selected_text.split(" — ")[0]

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM releases WHERE title=?", (title,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            messagebox.showerror("Ошибка", "Релиз не найден")
            return

        release_id = result[0]

        point_text = self.sale_point_var.get()
        if not point_text:
            messagebox.showerror("Ошибка", "Выберите точку продаж")
            return

        point_name = point_text.split(" (")[0]
        point_id = None
        for pid, name, address in self.sale_points:
            if name == point_name:
                point_id = pid
                break

        if not point_id:
            messagebox.showerror("Ошибка", "Точка продаж не найдена")
            return

        try:
            quantity = int(self.sale_quantity_entry.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество")
            return

        self.sales_manager.add_sale(release_id, point_id, quantity)
        messagebox.showinfo("Успех", "Продажа добавлена")
        self.sale_quantity_entry.delete(0, tk.END)
        self.update_sales_list()

    def update_sales_list(self):
        for item in self.sales_tree.get_children():
            self.sales_tree.delete(item)

        sales = self.sales_manager.get_sales()
        for sale in sales:
            self.sales_tree.insert("", "end", values=(sale[1], sale[2], sale[4], sale[5]))

    def update_user_sales_list(self):
        for item in self.user_sales_tree.get_children():
            self.user_sales_tree.delete(item)

        conn = sqlite3.connect("studio.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.title, sp.name, sp.address, s.quantity, s.date 
            FROM sales s
            JOIN releases r ON s.release_id = r.id
            JOIN sales_points sp ON s.point_id = sp.id
            WHERE r.username = ?
            ORDER BY s.date DESC
        """, (self.current_username,))

        for title, name, address, quantity, date in cursor.fetchall():
            self.user_sales_tree.insert("", "end", values=(title, f"{name} ({address})", quantity, date))

        conn.close()

    class SalesManager:
        def __init__(self, parent):
            self.parent = parent

        def get_release_status(self, release_id):
            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM release_status WHERE release_id=?", (release_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else "В производстве"

        def set_release_status(self, release_id, status):
            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO release_status (release_id, status) 
                VALUES (?, ?)
            """, (release_id, status))
            conn.commit()
            conn.close()

        def get_sales_points(self):
            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, address FROM sales_points")
            points = cursor.fetchall()
            conn.close()
            return points

        def add_sale(self, release_id, point_id, quantity):
            date = datetime.now().strftime("%d.%m.%Y %H:%M")

            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sales (release_id, point_id, quantity, date)
                VALUES (?, ?, ?, ?)
            """, (release_id, point_id, quantity, date))
            conn.commit()
            conn.close()

        def get_sales(self):
            conn = sqlite3.connect("studio.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, r.title, sp.name, sp.address, s.quantity, s.date 
                FROM sales s
                JOIN releases r ON s.release_id = r.id
                JOIN sales_points sp ON s.point_id = sp.id
                ORDER BY s.date DESC
            """)
            sales = cursor.fetchall()
            conn.close()
            return sales

    def logout_user(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        self.root.deiconify()
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

    def logout_admin(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        self.root.deiconify()
        self.username_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)

if __name__ == "__main__":
    setup_database()
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()