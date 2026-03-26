import sqlite3 # cuma buat konek ke SQLite
from abc import ABC, abstractmethod # karena mau ada Interface (janjian)
from .dtos import OrderDTO, MenuDTO, IngredientStock
# kalo ga gini, dia akan return dalam bentuk tuple 


class ICoffeePersistence(ABC):
# ini cuma untuk janjian (mau bilang ke backend) -- polymorph
# kalo mau jadi persistence buat kopi harus punya function berikut
# jadi backend akan bisa jalan pake SQL/Dict(mock) karena interface nya sama

    @abstractmethod
    def get_all_orders(self):
        pass

    @abstractmethod
    def insert_order(self, order):
        pass

    @abstractmethod
    def update_stock(self, order):
        pass

    @abstractmethod
    def get_stock_report(self):
        pass
    
    @abstractmethod
    def get_top_buyers(self):
        pass

    @abstractmethod
    def get_all_menu(self):
        pass

    @abstractmethod
    def get_total_spent(self, customer_name: str):
        pass

import sys

class SQLiteCoffeePersistence(ICoffeePersistence):
    def __init__(self, init=False):
        if "--dbInit=true" in sys.argv:
        # sys.argv itu  list yang berisi argumen command line saat program dijalankan
        # jadi akan cek ada ga argumen tsb pas run python -m .....
            init = True

        self.conn = sqlite3.connect("kedai.db")
        # simply untuk buat koneksi ke database SQLite biar bisa berkomunikasi sama sql
        if init:
            self.reset_database()
        else:
            self.setup_database()

    # buat reset db kalau dbInit = true
    def reset_database(self):
        cursor = self.conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute("DROP TABLE IF EXISTS ingredient_stock")
        cursor.execute("DROP TABLE IF EXISTS menu")

        self.conn.commit()
        self.setup_database()

    def setup_database(self):
        cursor = self.conn.cursor()
        # cursor() dipake buat jalanin query sql di SQL 
        
        # tabel menu
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price INTEGER,
            coffee_gram INTEGER,
            condensed_milk_ml INTEGER DEFAULT 0
        );
    """)
        # tabel ingredient stock
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredient_stock(
            coffee_gram INTEGER, 
            condensed_milk_ml INTEGER
        );
        """)

        # tabel order
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            menu_id INTEGER,
            quantity INTEGER,
            total INTEGER,
            promo_applied INTEGER,
            FOREIGN KEY(menu_id) REFERENCES menu(id)
        );
    """)
 
        cursor.execute("SELECT COUNT(*) FROM menu")
        # nanya berapa jumlah dalam menu itu, info nya kan akan 1 angka doang, kalau kosong baru isi
        if cursor.fetchone()[0] == 0: # == 0 >> cek tabel kalo kosong baru isi tabel, [0] ambil isinya karena fetch akan return tuple
            # fetchone = cuma ambil 1 baris pertama aja -- tuple
            #            kalo kita uda tau hasilnya cuma 1 baris yauda fetchone aja
            #            walaupun yg diambil cuma 1 baris, dia masih tuple, jadi harus ambil isinya 
            # fetchall = akan ambil semua baris yang bentuknya list of tuple
            #            dipake kalo emang yang dibutuhin tu kumpulan data
            cursor.executemany("""INSERT INTO menu (id, name, price, coffee_gram, condensed_milk_ml)
            VALUES (?, ?, ?, ?, ?)""", 
            [
                # '?' buat bind sama parameter di bawah
            (1, "Expresso", 10500, 300, 0),
            (2, "Kopi Susu", 20500, 300, 200),
            (3, "Kopi Hitam", 8000, 300, 0)
            ])

        cursor.execute("SELECT COUNT(*) FROM ingredient_stock")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO ingredient_stock (coffee_gram, condensed_milk_ml) VALUES (7000, 3600)")

        self.conn.commit() # simpen permanen jadi kalau dbInit=false, data tersimpan

    def get_all_orders(self):
        cursor = self.conn.cursor() # buat komunikasi sama db
        cursor.execute("""
            SELECT o.customer_name, o.quantity, o.total, o.promo_applied,
               m.id, m.name, m.price, m.coffee_gram, m.condensed_milk_ml
            FROM orders o
            JOIN menu m ON o.menu_id = m.id
        """)
        # join menu dan order karena untuk cetak penjualan butuh kedua data dari dua tabel tersebut
        # tabel order kan cuma simpan beli menu id yg mana, tapi untuk harga, nama menu yg simpen kan tabel menu
    
        rows = cursor.fetchall() # ambil yang tadi udah di fetchall()
        orders = []

        for row in rows:
        #                 0-3 customer, qty, total, promo, 4-8 menu columns...
            menu = MenuDTO(row[4], row[5], row[6], row[7], row[8])
            # passing data nya pake DTO : nanti yg diterima dlm bentuk DTO bukan list of tuple 
            # meski hasil fetchall adalah list of tupple
            order = OrderDTO(
                customer_name=row[0],
                menu=menu,
                quantity=row[1],
                total=row[2],
                promo_applied=bool(row[3])
                )

            orders.append(order) # convert list of tupple jadi DTO trus append

        return orders

    def insert_order(self, order):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO orders (customer_name, menu_id, quantity, total, promo_applied)
        VALUES (?, ?, ?, ?, ?)""", 
        (
        order.customer_name,
        order.menu.id,
        order.quantity,
        order.total,
        1 if order.promo_applied else 0 # karena SQL gatau boolean(true/false), jadi di python store as 1 dan 0
        )) # order >> as DTO 
        self.conn.commit()

    def update_stock(self, order):
        cursor = self.conn.cursor()

        cursor.execute("""
            UPDATE ingredient_stock
            SET coffee_gram = coffee_gram - ?,
                condensed_milk_ml = condensed_milk_ml - ?
        """, (
        order.menu.coffee_gram * order.quantity, # karena cuma satu baris (single record stock) makanya cukup pakai , saja
        order.menu.condensed_milk_ml * order.quantity
        ))
        # order.menu artinya: 
        # Ambil atribut menu yang ada di dalam object order.
        # Karena menu adalah object MenuDTO, kamu bisa akses propertinya seperti itu
        # contoh Composition (HAS-A Relationship) dalam OOP: Order has a Menu.

        self.conn.commit()


    def get_top_buyers(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT customer_name, SUM(total) as total_spent
            FROM orders
            GROUP BY customer_name
            ORDER BY total_spent DESC
            LIMIT 5
        """)
        # ngambil dari tabel order, digabungin (group by), urutin dari yg tertinggi makanya DESCENDING, cuma ambil 5 aja
        return cursor.fetchall() # karena yg di return ke backend adalah list of tuple
    
    def get_stock_report(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT coffee_gram, condensed_milk_ml FROM ingredient_stock")
        row = cursor.fetchone() # tabel ini isinya cuma satu baris aja makanya fetchone aja 
        #                                   row[0], row[1] >> ini return tuple, kalau dari rubrik soal diminta penggunaan DTO untuk mengembalikan data ke layer atas. 
        return IngredientStock(coffee_gram=row[0], condensed_milk_ml=row[1])
    

    def get_all_menu(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, price, coffee_gram, condensed_milk_ml
            FROM menu
            ORDER BY id
        """)
        rows = cursor.fetchall()
        menus = []
        for row in rows: # convert dari tuple yg ada jadi DTO
            menus.append(MenuDTO(
                id=row[0],
                name=row[1],
                price=row[2],
                coffee_gram=row[3],
                condensed_milk_ml=row[4]
            ))
        return menus

    def get_total_spent(self, customer_name: str):
        # buat yg belum pernah belanja akan null (0) biar ga error
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(total), 0) 
            FROM orders
            WHERE customer_name = ?
        """, (customer_name,))
        row = cursor.fetchone()
        return row[0] if row else 0
