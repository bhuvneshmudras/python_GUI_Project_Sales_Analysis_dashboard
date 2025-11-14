import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

# -------------------- DATABASE CONFIG --------------------
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"  # change for your MySQL password
DB_NAME = "sales_dashboard"


# -------------------- INITIAL SETUP --------------------
def setup_database():
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cur.execute(f"USE {DB_NAME}")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(50) NOT NULL,
            role ENUM('admin','salesperson') NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            category VARCHAR(50),
            price DECIMAL(10,2),
            quantity INT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales(
            id INT AUTO_INCREMENT PRIMARY KEY,
            salesperson_id INT,
            product_id INT,
            region VARCHAR(50),
            quantity INT,
            price DECIMAL(10,2),
            date DATE,
            FOREIGN KEY(salesperson_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    # Default users
    cur.execute("INSERT IGNORE INTO users(username,password,role) VALUES('admin','admin123','admin')")
    cur.execute("INSERT IGNORE INTO users(username,password,role) VALUES('john','pass123','salesperson')")
    cur.execute("INSERT IGNORE INTO users(username,password,role) VALUES('emma','emma123','salesperson')")

    # Sample products
    sample_products = [
        ('Laptop Pro 15"', 'Electronics', 1299.99, 10),
        ('Wireless Headphones', 'Accessories', 199.99, 25),
        ('Smartwatch', 'Wearables', 249.99, 18),
        ('Mechanical Keyboard', 'Accessories', 119.99, 30),
        ('4K Monitor', 'Electronics', 399.99, 15),
        ('Bluetooth Speaker', 'Audio', 89.99, 20)
    ]
    cur.executemany("""
        INSERT IGNORE INTO products(name,category,price,quantity)
        VALUES(%s,%s,%s,%s)
    """, sample_products)

    conn.commit()
    conn.close()


setup_database()


# -------------------- MAIN APP --------------------
class SalesDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("💼 Sales Data Analysis Dashboard")
        self.root.geometry("1100x700")
        self.conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        self.cursor = self.conn.cursor()
        self.current_user = None
        self.show_login()

    # ---------- LOGIN ----------
    def show_login(self):
        for w in self.root.winfo_children(): w.destroy()
        f = tk.Frame(self.root, bg="#1a1a1a");
        f.pack(fill="both", expand=True)
        tk.Label(f, text="🔐 Login", font=("Arial", 22, "bold"), bg="#1a1a1a", fg="white").pack(pady=20)
        tk.Label(f, text="Username", bg="#1a1a1a", fg="white").pack()
        self.user_entry = tk.Entry(f, width=30);
        self.user_entry.pack(pady=5)
        tk.Label(f, text="Password", bg="#1a1a1a", fg="white").pack()
        self.pass_entry = tk.Entry(f, show="*", width=30);
        self.pass_entry.pack(pady=5)
        tk.Button(f, text="Login", bg="#00bfff", fg="white", width=15, command=self.login).pack(pady=20)
        tk.Label(f, text="Default logins: admin/admin123 | john/pass123 | emma/emma123",
                 bg="#1a1a1a", fg="gray").pack()

    def login(self):
        user, pw = self.user_entry.get(), self.pass_entry.get()
        self.cursor.execute("SELECT id, role FROM users WHERE username=%s AND password=%s", (user, pw))
        row = self.cursor.fetchone()
        if row:
            self.current_user = row
            if row[1] == 'admin':
                self.admin_dashboard()
            else:
                self.sales_dashboard()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    # ---------- SALESPERSON DASHBOARD ----------
    def sales_dashboard(self):
        for w in self.root.winfo_children(): w.destroy()
        f = tk.Frame(self.root, bg="#121212");
        f.pack(fill="both", expand=True)
        tk.Label(f, text="🧾 Salesperson Dashboard", font=("Arial", 20, "bold"), bg="#121212", fg="#00ffff").pack(
            pady=10)

        bf = tk.Frame(f, bg="#121212");
        bf.pack()
        tk.Button(bf, text="➕ Add Order", bg="#00bfff", fg="white", command=self.add_order).grid(row=0, column=0,
                                                                                                 padx=10)
        tk.Button(bf, text="🗑️ Delete Order", bg="#ff5555", fg="white", command=self.delete_order).grid(row=0, column=1,
                                                                                                        padx=10)
        tk.Button(bf, text="📦 Product List", bg="#2ecc71", fg="white", command=self.show_products).grid(row=0, column=2,
                                                                                                        padx=10)
        tk.Button(bf, text="📊 Sales Summary", bg="#ffa500", fg="white", command=self.sales_summary).grid(row=0,
                                                                                                         column=3,
                                                                                                         padx=10)
        tk.Button(bf, text="Logout", bg="gray", fg="white", command=self.show_login).grid(row=0, column=4, padx=10)

        cols = ("ID", "Product", "Region", "Qty", "Price", "Date")
        self.sales_tree = ttk.Treeview(f, columns=cols, show="headings")
        for c in cols: self.sales_tree.heading(c, text=c)
        self.sales_tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_sales()

    def add_order(self):
        win = tk.Toplevel(self.root);
        win.title("Add Order");
        win.geometry("400x400");
        win.config(bg="#1a1a1a")
        tk.Label(win, text="Select Product", bg="#1a1a1a", fg="white").pack()
        df = pd.read_sql("SELECT name FROM products", self.conn)
        prod_var = tk.StringVar()
        combo = ttk.Combobox(win, values=df["name"].tolist(), textvariable=prod_var, state="readonly")
        combo.pack(pady=5)
        tk.Label(win, text="Region", bg="#1a1a1a", fg="white").pack();
        region = tk.Entry(win);
        region.pack(pady=5)
        tk.Label(win, text="Quantity", bg="#1a1a1a", fg="white").pack()
        qty_var = tk.StringVar()
        qty = tk.Entry(win, textvariable=qty_var);
        qty.pack(pady=5)
        tk.Label(win, text="Total Price ($)", bg="#1a1a1a", fg="white").pack()
        price_var = tk.StringVar()
        price = tk.Entry(win, textvariable=price_var, state="readonly");
        price.pack(pady=5)

        unit_price = [0]  # use list to hold mutable float accessible in nested function

        def update_price(*args):
            try:
                q = int(qty_var.get())
                if q < 0:
                    price_var.set("0.00")
                    return
                total = unit_price[0] * q
                price_var.set(f"{total:.2f}")
            except:
                price_var.set("0.00")

        def autofill(_):
            prod = prod_var.get()
            if not prod:
                unit_price[0] = 0
                price_var.set("0.00")
                return
            self.cursor.execute("SELECT price, quantity FROM products WHERE name=%s", (prod,))
            res = self.cursor.fetchone()
            if res:
                unit_price[0] = float(res[0])
                stock = int(res[1])
                # When product changes, reset quantity to 1 if empty or > stock
                try:
                    q = int(qty_var.get())
                    if q <= 0 or q > stock:
                        qty_var.set("1")
                except:
                    qty_var.set("1")
                update_price()
            else:
                unit_price[0] = 0
                price_var.set("0.00")

        combo.bind("<<ComboboxSelected>>", autofill)
        qty_var.trace_add("write", update_price)

        def save():
            prod = prod_var.get()
            reg = region.get()
            q_str = qty_var.get()
            if not prod or not reg or not q_str.isdigit():
                messagebox.showwarning("Warning", "Please fill all fields correctly!")
                return
            q = int(q_str)
            if q <= 0:
                messagebox.showwarning("Warning", "Quantity must be greater than zero!")
                return
            # Check stock
            self.cursor.execute("SELECT id, quantity FROM products WHERE name=%s", (prod,))
            res = self.cursor.fetchone()
            if not res:
                messagebox.showerror("Error", "Product not found!")
                return
            pid, stock = res
            if q > stock:
                messagebox.showwarning("Stock", f"Only {stock} units available!")
                return
            # Insert sale
            self.cursor.execute("""INSERT INTO sales(salesperson_id, product_id, region, quantity, price, date)
                                   VALUES(%s, %s, %s, %s, %s, %s)""",
                                (self.current_user[0], pid, reg, q, unit_price[0], datetime.now().strftime("%Y-%m-%d")))
            # Update stock
            self.cursor.execute("UPDATE products SET quantity=quantity-%s WHERE id=%s", (q, pid))
            self.conn.commit()
            messagebox.showinfo("Saved", "Order added.")
            win.destroy()
            self.load_sales()

        tk.Button(win, text="Add Order", bg="#00bfff", fg="white", command=save).pack(pady=15)

    def load_sales(self):
        for i in self.sales_tree.get_children(): self.sales_tree.delete(i)
        df = pd.read_sql("""SELECT s.id,p.name,s.region,s.quantity,s.price,s.date
                          FROM sales s JOIN products p ON s.product_id=p.id
                          WHERE s.salesperson_id=%s""", self.conn, params=(self.current_user[0],))
        for _, r in df.iterrows(): self.sales_tree.insert("", 'end', values=tuple(r))

    def delete_order(self):
        sel = self.sales_tree.selection()
        if not sel: return
        oid = self.sales_tree.item(sel[0])['values'][0]
        self.cursor.execute("DELETE FROM sales WHERE id=%s", (oid,));
        self.conn.commit();
        self.load_sales()

    def show_products(self):
        df = pd.read_sql("SELECT * FROM products", self.conn)
        w = tk.Toplevel(self.root);
        w.title("Products");
        w.geometry("600x400")
        t = ttk.Treeview(w, columns=df.columns.tolist(), show="headings")
        for c in df.columns: t.heading(c, text=c)
        for _, r in df.iterrows(): t.insert("", 'end', values=tuple(r))
        t.pack(fill="both", expand=True)

    def sales_summary(self):
        df = pd.read_sql("""SELECT date, quantity * price as revenue, region FROM sales
                            WHERE salesperson_id=%s""", self.conn, params=(self.current_user[0],))
        if df.empty:
            messagebox.showinfo("Info", "No sales")
            return

        fig, ax = plt.subplots(1, 3, figsize=(15, 5))

        # Sales Over Time (line plot)
        d = df.groupby("date")["revenue"].sum()
        ax[0].plot(d.index, d.values, marker='o', color='#1f77b4')
        ax[0].set_title("Sales Over Time", fontsize=14, fontweight='bold')
        ax[0].set_xlabel("Date")
        ax[0].set_ylabel("Revenue ($)")
        ax[0].grid(True, linestyle='--', alpha=0.5)
        for label in ax[0].get_xticklabels():
            label.set_rotation(45)
            label.set_horizontalalignment('right')

        # Region Revenue (bar chart)
        r = df.groupby("region")["revenue"].sum()
        bars = ax[1].bar(r.index, r.values, color='#ff7f0e')
        ax[1].set_title("Revenue by Region", fontsize=14, fontweight='bold')
        ax[1].set_xlabel("Region")
        ax[1].set_ylabel("Revenue ($)")
        ax[1].grid(axis='y', linestyle='--', alpha=0.5)
        for label in ax[1].get_xticklabels():
            label.set_rotation(45)
            label.set_horizontalalignment('right')

        # Region Share (pie chart)
        ax[2].pie(r.values, labels=r.index, autopct="%1.1f%%", startangle=140, textprops={'fontsize': 10})
        ax[2].set_title("Region Share", fontsize=14, fontweight='bold')

        plt.tight_layout(pad=3)
        plt.show()

    # ---------- ADMIN DASHBOARD ----------
    def admin_dashboard(self):
        for w in self.root.winfo_children(): w.destroy()
        f = tk.Frame(self.root, bg="#0d0d0d");
        f.pack(fill="both", expand=True)
        tk.Label(f, text="👨‍💼 Admin Dashboard", font=("Arial", 20, "bold"), bg="#0d0d0d", fg="#00ffff").pack(pady=10)
        tk.Button(f, text="➕ Add Product", bg="#00bfff", fg="white", command=self.add_product).pack(pady=5)
        tk.Button(f, text="🗑️ Delete Product", bg="#ff5555", fg="white", command=self.delete_product).pack(pady=5)
        tk.Button(f, text="👥 Manage Salespersons", bg="#ffa500", fg="white", command=self.manage_salespersons).pack(
            pady=5)
        tk.Button(f, text="📈 View Analytics", bg="#2ecc71", fg="white", command=self.analytics).pack(pady=5)
        tk.Button(f, text="Logout", bg="gray", fg="white", command=self.show_login).pack(pady=5)

        self.prod_tree = ttk.Treeview(f, columns=("ID", "Name", "Category", "Price", "Qty"), show="headings")
        for c in ("ID", "Name", "Category", "Price", "Qty"): self.prod_tree.heading(c, text=c)
        self.prod_tree.pack(fill="both", expand=True, padx=20, pady=20)
        self.load_products()

    def load_products(self):
        for i in self.prod_tree.get_children(): self.prod_tree.delete(i)
        df = pd.read_sql("SELECT * FROM products", self.conn)
        for _, r in df.iterrows(): self.prod_tree.insert("", 'end', values=tuple(r))

    def add_product(self):
        win = tk.Toplevel(self.root);
        win.title("Add Product");
        win.geometry("400x400");
        win.config(bg="#1a1a1a")
        entries = {}
        for field in ["Name", "Category", "Price", "Quantity"]:
            tk.Label(win, text=field, bg="#1a1a1a", fg="white").pack(pady=5)
            e = tk.Entry(win);
            e.pack(pady=5);
            entries[field] = e

        def save():
            try:
                self.cursor.execute("""INSERT INTO products(name,category,price,quantity)
                                       VALUES(%s,%s,%s,%s)""",
                                    (entries["Name"].get(), entries["Category"].get(),
                                     float(entries["Price"].get()), int(entries["Quantity"].get())))
                self.conn.commit();
                messagebox.showinfo("Added", "Product added")
                win.destroy();
                self.load_products()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(win, text="Add", bg="#00bfff", fg="white", command=save).pack(pady=20)

    def delete_product(self):
        sel = self.prod_tree.selection()
        if not sel: return
        pid = self.prod_tree.item(sel[0])['values'][0]
        self.cursor.execute("DELETE FROM products WHERE id=%s", (pid,))
        self.conn.commit();
        self.load_products()

    def manage_salespersons(self):
        win = tk.Toplevel(self.root);
        win.title("Manage Salespersons");
        win.geometry("600x400");
        win.config(bg="#1a1a1a")
        tk.Label(win, text="Salesperson Accounts", bg="#1a1a1a", fg="white", font=("Arial", 14, "bold")).pack(pady=10)
        cols = ("ID", "Username");
        tree = ttk.Treeview(win, columns=cols, show="headings")
        for c in cols: tree.heading(c, text=c)
        tree.pack(fill="both", expand=True, padx=20, pady=10)

        def load_salespeople():
            for i in tree.get_children(): tree.delete(i)
            self.cursor.execute("SELECT id,username FROM users WHERE role='salesperson'")
            for r in self.cursor.fetchall(): tree.insert("", 'end', values=r)

        load_salespeople()

        # Add form
        frm = tk.Frame(win, bg="#1a1a1a");
        frm.pack(pady=10)
        tk.Label(frm, text="Username", bg="#1a1a1a", fg="white").grid(row=0, column=0)
        u = tk.Entry(frm);
        u.grid(row=0, column=1)
        tk.Label(frm, text="Password", bg="#1a1a1a", fg="white").grid(row=1, column=0)
        p = tk.Entry(frm, show="*");
        p.grid(row=1, column=1)

        def add_user():
            try:
                self.cursor.execute("INSERT INTO users(username,password,role) VALUES(%s,%s,'salesperson')",
                                    (u.get(), p.get()))
                self.conn.commit()
                load_salespeople()
                messagebox.showinfo("Added", "Salesperson added")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(frm, text="Add Salesperson", bg="#00bfff", fg="white", command=add_user).grid(row=2, column=0,
                                                                                                columnspan=2, pady=10)

    def analytics(self):
        df = pd.read_sql("""SELECT p.category, SUM(s.quantity * s.price) AS revenue
                            FROM sales s JOIN products p ON s.product_id=p.id
                            GROUP BY p.category""", self.conn)
        if df.empty:
            messagebox.showinfo("Info", "No sales data available")
            return
        fig, ax = plt.subplots(1, 2, figsize=(12, 5))

        # Revenue by Category (bar)
        ax[0].bar(df["category"], df["revenue"], color="#007acc")
        ax[0].set_title("Revenue by Category", fontsize=14, fontweight='bold')
        ax[0].set_xlabel("Category")
        ax[0].set_ylabel("Revenue ($)")
        ax[0].grid(axis='y', linestyle='--', alpha=0.5)
        for label in ax[0].get_xticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment('right')

        # Top 5 Products by Revenue (bar)
        df2 = pd.read_sql("""SELECT p.name, SUM(s.quantity * s.price) AS revenue
                            FROM sales s JOIN products p ON s.product_id=p.id
                            GROUP BY p.name ORDER BY revenue DESC LIMIT 5""", self.conn)
        ax[1].bar(df2["name"], df2["revenue"], color="#ff6600")
        ax[1].set_title("Top 5 Products by Revenue", fontsize=14, fontweight='bold')
        ax[1].set_xlabel("Product")
        ax[1].set_ylabel("Revenue ($)")
        ax[1].grid(axis='y', linestyle='--', alpha=0.5)
        for label in ax[1].get_xticklabels():
            label.set_rotation(45)
            label.set_horizontalalignment('right')

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = SalesDashboard(root)
    root.mainloop()
