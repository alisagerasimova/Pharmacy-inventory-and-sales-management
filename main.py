
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import uuid

# --- ПАЛИТРА ---
COLORS = {
    "bg": "#0F172A", "surface": "#1E293B", "accent": "#38BDF8",
    "text": "#F8FAFC", "text_dim": "#94A3B8", "danger": "#FB7185", "success": "#4ADE80", "border": "#334155"
}

class PharmacyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pharmacy OS Pro v11.1")
        
        self.root.state('zoomed')
        self.root.configure(bg=COLORS["bg"])

        self.cart = [] 
        self.selected_med_id = None 
        self.stock_sort_alpha = False 
        
        self.init_db()
        self.setup_styles()
        self.rx_var = tk.IntVar()

        # ШАПКА
        self.header = tk.Frame(self.root, bg=COLORS["surface"], height=70)
        self.header.pack(side="top", fill="x")
        
        tk.Label(self.header, text="💊 PHARMACY PRO", bg=COLORS["surface"], fg=COLORS["accent"], 
                 font=("Segoe UI", 18, "bold"), padx=30).pack(side="left")
        
        self.nav_frame = tk.Frame(self.header, bg=COLORS["surface"])
        self.nav_frame.pack(side="right", padx=20)
        
        self.create_nav_btn("КАТАЛОГ ЛЕКАРСТВ", self.show_medicines)
        self.create_nav_btn("СКЛАД И КАССА", self.show_stock)
        self.create_nav_btn("ЖУРНАЛ ПРОДАЖ", self.show_sales)

        self.content = tk.Frame(self.root, bg=COLORS["bg"])
        self.content.pack(fill="both", expand=True, padx=30, pady=20)

        self.show_stock()

    def init_db(self):
        self.conn = sqlite3.connect("pharmacy_v13.db")
        self.cur = self.conn.cursor()
        self.cur.execute("PRAGMA foreign_keys = ON;")
        self.cur.execute("CREATE TABLE IF NOT EXISTS medicines (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, rx INTEGER, unit TEXT, price INTEGER)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, med_id INTEGER, qty INTEGER, exp TEXT, FOREIGN KEY(med_id) REFERENCES medicines(id) ON DELETE CASCADE)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS receipts (id TEXT PRIMARY KEY, date TEXT, total_sum INTEGER)")
        self.cur.execute("CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, receipt_id TEXT, med_id INTEGER, qty INTEGER, price_at_sale INTEGER, FOREIGN KEY(receipt_id) REFERENCES receipts(id) ON DELETE CASCADE, FOREIGN KEY(med_id) REFERENCES medicines(id))")
        self.conn.commit()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=COLORS["surface"], foreground=COLORS["text"], fieldbackground=COLORS["surface"], rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=COLORS["bg"], foreground=COLORS["accent"], font=("Segoe UI", 10, "bold"))

    def create_nav_btn(self, text, cmd):
        tk.Button(self.nav_frame, text=text, command=cmd, bg=COLORS["surface"], fg=COLORS["text"], bd=0, padx=15, pady=20, font=("Segoe UI", 9, "bold"), activebackground=COLORS["accent"]).pack(side="left")

    def clear_content(self):
        self.selected_med_id = None
        for widget in self.content.winfo_children(): widget.destroy()

    # --- РАЗДЕЛ: КАТАЛОГ ---
    def show_medicines(self):
        self.clear_content()
        tk.Label(self.content, text="Справочник лекарственных средств", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI", 16, "bold")).pack(anchor="w", pady=(0, 15))

        f = tk.Frame(self.content, bg=COLORS["surface"], padx=20, pady=20)
        f.pack(fill="x", pady=(0, 20))
        
        tk.Label(f, text="Название:", bg=COLORS["surface"], fg="white").grid(row=0, column=0, sticky="w")
        self.ent_name = tk.Entry(f, font=("Segoe UI", 11)); self.ent_name.grid(row=1, column=0, padx=5, pady=5)
        
        tk.Label(f, text="Цена (₽):", bg=COLORS["surface"], fg="white").grid(row=0, column=1, sticky="w")
        self.ent_price = tk.Entry(f, font=("Segoe UI", 11), width=10); self.ent_price.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(f, text="Ед. изм:", bg=COLORS["surface"], fg="white").grid(row=0, column=2, sticky="w")
        self.ent_unit = ttk.Combobox(f, values=["уп", "фл", "шт"], width=8); self.ent_unit.grid(row=1, column=2, padx=5); self.ent_unit.set("уп")
        
        tk.Checkbutton(f, text="Нужен рецепт", variable=self.rx_var, bg=COLORS["surface"], fg=COLORS["accent"], selectcolor=COLORS["bg"]).grid(row=1, column=3, padx=10)
        
        self.btn_save_med = tk.Button(f, text="СОХРАНИТЬ", command=self.save_medicine, bg=COLORS["accent"], fg=COLORS["bg"], font=("Segoe UI", 9, "bold"), padx=20)
        self.btn_save_med.grid(row=1, column=4, padx=5)

        self.btn_del_med = tk.Button(f, text="УДАЛИТЬ", command=self.delete_medicine, bg=COLORS["danger"], fg="white", font=("Segoe UI", 9, "bold"), padx=15)
        self.btn_del_med.grid(row=1, column=5, padx=5); self.btn_del_med.grid_remove()

        self.tree_meds = ttk.Treeview(self.content, columns=("ID", "Название", "Рецепт", "Ед", "Цена"), show="headings", height=15)
        for c in ("ID", "Название", "Рецепт", "Ед", "Цена"): self.tree_meds.heading(c, text=c); self.tree_meds.column(c, anchor="center")
        self.tree_meds.pack(fill="both", expand=True)
        self.tree_meds.bind("<<TreeviewSelect>>", self.on_med_select)
        self.refresh_meds()

    def on_med_select(self, event):
        sel = self.tree_meds.selection()
        if not sel: return
        item = self.tree_meds.item(sel)['values']
        self.selected_med_id = item[0]
        self.ent_name.delete(0, tk.END); self.ent_name.insert(0, item[1])
        self.ent_price.delete(0, tk.END); self.ent_price.insert(0, str(item[4]).replace(" ₽", ""))
        self.ent_unit.set(item[3])
        self.rx_var.set(1 if "💊" in str(item[2]) else 0)
        self.btn_save_med.config(text="ОБНОВИТЬ", bg=COLORS["success"])
        self.btn_del_med.grid()

    def save_medicine(self):
        n, p, u, r = self.ent_name.get(), self.ent_price.get(), self.ent_unit.get(), self.rx_var.get()
        if n and p.isdigit():
            if self.selected_med_id:
                self.cur.execute("UPDATE medicines SET name=?, rx=?, unit=?, price=? WHERE id=?", (n, r, u, int(p), self.selected_med_id))
            else:
                self.cur.execute("INSERT INTO medicines (name, rx, unit, price) VALUES (?, ?, ?, ?)", (n, r, u, int(p)))
            self.conn.commit(); self.refresh_meds(); self.clear_med_form()

    def delete_medicine(self):
        if self.selected_med_id and messagebox.askyesno("Удаление", "Удалить лекарство и остатки?"):
            self.cur.execute("DELETE FROM medicines WHERE id=?", (self.selected_med_id,))
            self.conn.commit(); self.refresh_meds(); self.clear_med_form()

    def clear_med_form(self):
        self.selected_med_id = None
        self.ent_name.delete(0, tk.END); self.ent_price.delete(0, tk.END); self.rx_var.set(0)
        self.btn_save_med.config(text="СОХРАНИТЬ", bg=COLORS["accent"]); self.btn_del_med.grid_remove()

    def refresh_meds(self):
        for i in self.tree_meds.get_children(): self.tree_meds.delete(i)
        for row in self.cur.execute("SELECT * FROM medicines"):
            r = list(row); r[2] = "💊 Рецепт" if r[2]==1 else "Нет"; r[4] = f"{r[4]} ₽"
            self.tree_meds.insert("", "end", values=r)

    # --- РАЗДЕЛ: СКЛАД И КАССА ---
    def show_stock(self):
        self.clear_content()
        
        # ФИЛЬТРЫ
        filter_f = tk.Frame(self.content, bg=COLORS["surface"], padx=15, pady=10)
        filter_f.pack(fill="x", pady=(0, 15))
        
        tk.Label(filter_f, text="🔍 Поиск:", bg=COLORS["surface"], fg="white").pack(side="left")
        self.ent_search = tk.Entry(filter_f, width=15); self.ent_search.pack(side="left", padx=5)
        self.ent_search.bind("<KeyRelease>", lambda e: self.refresh_stock())

        tk.Label(filter_f, text="📅 Срок:", bg=COLORS["surface"], fg="white").pack(side="left", padx=(10, 0))
        self.ent_date_f = tk.Entry(filter_f, width=12); self.ent_date_f.pack(side="left", padx=5)
        
        tk.Button(filter_f, text="Найти", command=self.refresh_stock, bg=COLORS["border"], fg="white").pack(side="left", padx=5)
        tk.Button(filter_f, text="Сортировать А-Я", command=self.toggle_sort, bg=COLORS["accent"], fg=COLORS["bg"], font=("bold", 8)).pack(side="left", padx=10)
        tk.Button(filter_f, text="Сброс", command=self.reset_filters, bg=COLORS["border"], fg="white").pack(side="left")

        main_container = tk.Frame(self.content, bg=COLORS["bg"])
        main_container.pack(fill="both", expand=True)

        # СКЛАД (ЛЕВО)
        left_side = tk.Frame(main_container, bg=COLORS["bg"])
        left_side.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        self.tree_stock = ttk.Treeview(left_side, columns=("ID", "Название", "Кол-во", "Срок"), show="headings", height=8)
        for c in ("ID", "Название", "Кол-во", "Срок"): self.tree_stock.heading(c, text=c); self.tree_stock.column(c, anchor="center")
        self.tree_stock.pack(fill="both", expand=True, pady=10)

        action_f = tk.Frame(left_side, bg=COLORS["bg"])
        action_f.pack(fill="x")

        f_cart = tk.LabelFrame(action_f, text=" Продажа ", bg=COLORS["surface"], fg=COLORS["accent"], padx=15, pady=10)
        f_cart.pack(side="left", fill="y", expand=True)
        tk.Label(f_cart, text="Кол-во:", bg=COLORS["surface"], fg="white").pack(side="left")
        self.ent_qty_cart = tk.Entry(f_cart, width=8); self.ent_qty_cart.pack(side="left", padx=5)
        tk.Button(f_cart, text="В ЧЕК", command=self.add_to_cart, bg=COLORS["accent"], fg=COLORS["bg"], font=("bold", 9)).pack(side="left", padx=5)

        f_rec = tk.LabelFrame(action_f, text=" Приемка ", bg=COLORS["surface"], fg=COLORS["success"], padx=15, pady=10)
        f_rec.pack(side="left", fill="y", expand=True, padx=(10, 0))
        self.cb_med_rec = ttk.Combobox(f_rec, width=15); self.cb_med_rec.pack(side="left", padx=2)
        self.ent_qty_rec = tk.Entry(f_rec, width=5); self.ent_qty_rec.pack(side="left", padx=2)
        self.ent_exp_rec = tk.Entry(f_rec, width=10); self.ent_exp_rec.insert(0, "2026-12-31"); self.ent_exp_rec.pack(side="left", padx=2)
        tk.Button(f_rec, text="ОК", command=self.add_to_stock, bg=COLORS["success"], fg=COLORS["bg"]).pack(side="left")

        # КАССА (ПРАВО)
        right_side = tk.Frame(main_container, bg=COLORS["surface"], padx=20, pady=20)
        right_side.pack(side="right", fill="both")
        
        tk.Label(right_side, text="🛒 ТЕКУЩИЙ ЧЕК", bg=COLORS["surface"], fg=COLORS["accent"], font=("bold", 12)).pack()
        
        self.tree_cart = ttk.Treeview(right_side, columns=("N", "Q", "S"), show="headings", height=10)
        self.tree_cart.heading("N", text="Товар"); self.tree_cart.heading("Q", text="Кол."); self.tree_cart.heading("S", text="Сумма")
        self.tree_cart.column("N", width=140); self.tree_cart.column("Q", width=40); self.tree_cart.column("S", width=70)
        self.tree_cart.pack(fill="both", expand=True, pady=10)

        self.lbl_total = tk.Label(right_side, text="0 ₽", bg=COLORS["surface"], fg=COLORS["success"], font=("bold", 22))
        self.lbl_total.pack(pady=10)

        tk.Button(right_side, text="❌ УДАЛИТЬ ИЗ ЧЕКА", command=self.remove_from_cart, 
                  bg=COLORS["danger"], fg="white", font=("bold", 9), pady=5).pack(fill="x", pady=5)

        # ТА САМАЯ КНОПКА
        tk.Button(right_side, text="ФИНАЛИЗИРОВАТЬ ЧЕК", command=self.finalize_receipt, 
                  bg=COLORS["success"], fg=COLORS["bg"], font=("Segoe UI", 11, "bold"), pady=15).pack(fill="x", pady=5)

        self.refresh_stock(); self.update_receive_cb(); self.update_cart_ui()

    def toggle_sort(self):
        self.stock_sort_alpha = not self.stock_sort_alpha
        self.refresh_stock()

    def refresh_stock(self):
        for i in self.tree_stock.get_children(): self.tree_stock.delete(i)
        search, date = f"%{self.ent_search.get()}%", self.ent_date_f.get()
        query = "SELECT s.id, m.name, s.qty, s.exp FROM stock s JOIN medicines m ON s.med_id = m.id WHERE m.name LIKE ?"
        params = [search]
        if date: query += " AND s.exp = ?"; params.append(date)
        if self.stock_sort_alpha: query += " ORDER BY m.name ASC"
        else: query += " ORDER BY s.id DESC"
        for row in self.cur.execute(query, params): self.tree_stock.insert("", "end", values=row)

    def reset_filters(self):
        self.ent_search.delete(0, tk.END); self.ent_date_f.delete(0, tk.END)
        self.stock_sort_alpha = False; self.refresh_stock()

    def add_to_cart(self):
        sel = self.tree_stock.selection()
        qty = self.ent_qty_cart.get()
        if sel and qty.isdigit() and int(qty) > 0:
            sd = self.tree_stock.item(sel)['values']
            if int(qty) <= sd[2]:
                res = self.cur.execute("SELECT m.id, m.price FROM medicines m JOIN stock s ON m.id = s.med_id WHERE s.id = ?", (sd[0],)).fetchone()
                self.cart.append({'stock_id': sd[0], 'med_id': res[0], 'name': sd[1], 'qty': int(qty), 'price': res[1], 'sum': int(qty)*res[1]})
                self.update_cart_ui(); self.ent_qty_cart.delete(0, tk.END)
            else: messagebox.showwarning("ОШИБКА", "Недостаточно продукции на складе")

    def remove_from_cart(self):
        sel = self.tree_cart.selection()
        if sel:
            idx = self.tree_cart.index(sel[0])
            self.cart.pop(idx); self.update_cart_ui()

    def update_cart_ui(self):
        for i in self.tree_cart.get_children(): self.tree_cart.delete(i)
        total = sum(i['sum'] for i in self.cart)
        for item in self.cart: self.tree_cart.insert("", "end", values=(item['name'], item['qty'], f"{item['sum']} ₽"))
        self.lbl_total.config(text=f"{total} ₽")

    def finalize_receipt(self):
        if not self.cart: return
        rid = str(uuid.uuid4())[:8].upper()
        total = sum(i['sum'] for i in self.cart)
        date_now = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.cur.execute("INSERT INTO receipts VALUES (?, ?, ?)", (rid, date_now, total))
        for i in self.cart:
            self.cur.execute("INSERT INTO sales (receipt_id, med_id, qty, price_at_sale) VALUES (?, ?, ?, ?)", (rid, i['med_id'], i['qty'], i['price']))
            self.cur.execute("UPDATE stock SET qty = qty - ? WHERE id = ?", (i['qty'], i['stock_id']))
        self.cur.execute("DELETE FROM stock WHERE qty <= 0")
        self.conn.commit(); self.cart = []; self.update_cart_ui(); self.refresh_stock()
        messagebox.showinfo("Успех", f"Чек {rid} сохранен в журнал!")

    def add_to_stock(self):
        m, q, exp = self.cb_med_rec.get(), self.ent_qty_rec.get(), self.ent_exp_rec.get()
        if m and q.isdigit():
            mid = m.split(" | ")[0]
            self.cur.execute("INSERT INTO stock (med_id, qty, exp) VALUES (?, ?, ?)", (mid, int(q), exp))
            self.conn.commit(); self.refresh_stock(); self.ent_qty_rec.delete(0, tk.END)

    def update_receive_cb(self):
        self.cb_med_rec['values'] = [f"{r[0]} | {r[1]}" for r in self.cur.execute("SELECT id, name FROM medicines")]

    # --- РАЗДЕЛ: ЖУРНАЛ ПРОДАЖ ---
    def show_sales(self):
        self.clear_content()
        pan = tk.PanedWindow(self.content, orient="vertical", bg=COLORS["bg"], sashwidth=4)
        pan.pack(fill="both", expand=True)
        f1 = tk.Frame(pan, bg=COLORS["bg"])
        self.tree_receipts = ttk.Treeview(f1, columns=("ID", "Дата", "Сумма"), show="headings")
        for c in ("ID", "Дата", "Сумма"): self.tree_receipts.heading(c, text=c); self.tree_receipts.column(c, anchor="center")
        self.tree_receipts.pack(fill="both", expand=True); self.tree_receipts.bind("<<TreeviewSelect>>", self.on_receipt_click)
        pan.add(f1)
        f2 = tk.Frame(pan, bg=COLORS["bg"])
        self.tree_details = ttk.Treeview(f2, columns=("M", "Q", "P"), show="headings")
        for c, h in zip(("M", "Q", "P"), ("Товар", "Кол-во", "Цена")): self.tree_details.heading(c, text=h); self.tree_details.column(c, anchor="center")
        self.tree_details.pack(fill="both", expand=True)
        pan.add(f2)
        for row in self.cur.execute("SELECT * FROM receipts ORDER BY date DESC"): self.tree_receipts.insert("", "end", values=row)

    def on_receipt_click(self, event):
        sel = self.tree_receipts.selection()
        if not sel: return
        rid = self.tree_receipts.item(sel)['values'][0]
        for i in self.tree_details.get_children(): self.tree_details.delete(i)
        for row in self.cur.execute("SELECT m.name, s.qty, s.price_at_sale FROM sales s JOIN medicines m ON s.med_id = m.id WHERE s.receipt_id = ?", (rid,)):
            self.tree_details.insert("", "end", values=row)

if __name__ == "__main__":
    root = tk.Tk(); app = PharmacyApp(root); root.mainloop()
