from abc import ABC, abstractmethod
from .dtos import OrderDTO

from .database import ICoffeePersistence
# disini perlu import Interface dari db biar
# service bisa akses tipe tanpa tahu implementasi penyimpanannya.

# Subject : sumber event nya gitu - dan akan nyebarin informasi
# Observer : yang akan nerima event dan punya berbagai aksi

class IObserver(ABC): # -- interface/kontrak/janjian
    # anggap aja kayak followers, isubject itu boss gt
    # jadi semua observer (yang inherit) harus punya method update mau gimanapun implementasinya
    @abstractmethod
    def update(self, event):
        pass


class ISubject(ABC):  # -- interface/kontrak/janjian [anggap as a publisher]
    @abstractmethod
    def add_observer(self, observer):
        pass

    @abstractmethod
    def notify(self, event):
        pass


class StockSubject(ISubject):
    # implementasi dari ISubject 
    def __init__(self):
        # akan menyimpan semua observer 
        self.observers = []

    def add_observer(self, obs):
        self.observers.append(obs)

    def notify(self, event):
        return [obs.update(event) for obs in self.observers]
        # update > methode observer (promo/stok habis)

class PromoSubject(ISubject):
    # implementasi dari ISubject untuk promo
    def __init__(self):
        # akan menyimpan semua observer 
        self.observers = []

    def add_observer(self, obs):
        self.observers.append(obs)

    def notify(self, order):
        return [obs.update(order) for obs in self.observers]
        # update > methode observer untuk promo

# implementasi observer method nya karena aksinya beda jadi tiap class punya 1 aksi
class StockObserver(IObserver):
    def update(self, event):
        return f"[⚠] WARNING: Stok hampir habis untuk {event}"
        
class PromoObserver(IObserver):
    def update(self, order):
        return f"[🎉] Promo diterapkan untuk pelanggan {order.customer_name}"


# biar ada base dari backend 
# jadi udah ada janjiannya, nanti kalo mau di modif tetep bisa karena bergantung nya cuma sama abstraksinya ini
class ICoffeeService(ABC):
    @abstractmethod
    def order_coffee(self, customer_name: str, menu_id: int, qty: int):
        pass

class CoffeeService(ICoffeeService):
    # disini menerima interface melalui constructor (mengakses layer bayar [database] dengan parameter)
    def __init__(self, persistence: ICoffeePersistence, stock_subject: ISubject, promo_subject: ISubject):
        # perlu data - akses db layer, lalu stock dan promo itu observer pattern
        self.persistence = persistence
        self.stock_subject = stock_subject
        self.promo_subject = promo_subject

    def order_coffee(self, customer_name, menu_id, qty, ignore_bonus=False):
        # pas mau order kopi akan butuh apa aja -- parameter
                                  
        messages = []
        # tempat untuk misal ada warning stok kah, promo, dll

        menu_list = self.persistence.get_all_menu()
        # simply ambil semua menu dari db (persistence) lewat interface nya

        menu = next((m for m in menu_list if m.id == menu_id), None)
        # gaperlu loop manual, kalo ga ketemu akan auto None

        if not menu:
            return None, ["[❌] Menu tidak ditemukan"]
            # biar langsung stop

        total = menu.price * qty
        # hitung total harga tanpa promo

        previous_total = self.persistence.get_total_spent(customer_name)
        # hitung dulu total belanja sebelumnya

        promo_eligible = previous_total + total > 300000
        # kalau mencukupi promo akan diberlakukan

        stock = self.persistence.get_stock_report()
        need_coffee = menu.coffee_gram * qty
                    # menu. akses DTO nya
        need_milk = menu.condensed_milk_ml * qty
        # backend (service) akan akses ke db (persistence) 
        # harus tau dulu bahan cukup ga buat pesanan tersebut

        if stock.coffee_gram < need_coffee:
            return None, [f"[❌] Stok kopi tidak cukup. Sisa: {stock.coffee_gram}, butuh: {need_coffee}"]
        if stock.condensed_milk_ml < need_milk:
            return None, [f"[❌] Stok susu tidak cukup. Sisa: {stock.condensed_milk_ml}, butuh: {need_milk}"]
        # biar nantinya kalo emang ga cukup early exit aja, karena ga mungkin stok akan minus 

        free_item = next((m for m in menu_list if m.name.lower().startswith("kopi hitam")), None)
        # simply just checking aja kopi hitam ... (kopi hitam sepahit hidup) itu ada atau ga
        # gausa panjang karena pake startswith(), menu kopi hitam kan cuma satu
        # equal to :
        '''
        result = []
        for m in menu_list:
            if m.name.lower().startswith("kopi hitam"):
                result.append(m)

        if result:
            free_item = result[0]
        else:
            free_item = None
        '''
        # next() : kalo udh ketemu 1 yaudah ga akan loop lagi
        

        # sebelum buat order -- disini cuma cek, boleh kasi bonus ga
        # belum commit transaction
        # tapi kalau ternyata ga >300, ini akan di skip langsung buat order dan update stock
        if promo_eligible and free_item and not ignore_bonus:
        # cek : kena promo, kopi hitam ada, [ignore_bonus masih default (false) - not false = bonus masih dipertimbangin]
        # dapat bonus, free_item ada, belum kena konfirmasi
            # cek dulu stok buat free_item itu cukup ga
            extra_coffee = free_item.coffee_gram
            extra_milk = free_item.condensed_milk_ml

            # meminta konfirmasi user kalau memang free_item nya ga cukup stok nya
            # \ to be read as a full line
            if stock.coffee_gram < need_coffee + extra_coffee or \
               stock.condensed_milk_ml < need_milk + extra_milk:
                return "CONFIRM_BONUS", [  # pas ternyata pesanan dan bonus ga cukup sama stock nya
                    "🎁 Anda berhak bonus kopi hitam GRATIS, tetapi stok tidak mencukupi.",
                    "Apakah ingin melanjutkan TANPA bonus?"
                ]

        # order dibuat
        order = OrderDTO(customer_name, menu, qty, total, promo_eligible)
        # ini sebenernya termasuk 'encapsulation' 
        # karena data terbungkus dalam objek DTO
        # lagi buat order nya by OrderDTO (objek order sudah baawa objek menu didalamnya)

        self.persistence.update_stock(order)
        # ambil data(persistence) : nerima objek order karena order udah punya .menu
        # persistence otomatis akan bisa [order.menu.coffee_gram dan order.menu.condensed_milk_ml]
        # Persistence bisa tau menu karena OrderDTO bawa objek MenuDTO didalamnya
        # dan pas service (backend) buat order, udah ada semua info yg si persistence butuh
        # persistence cuma ambil order.menu dia ga nyari menu sendiri

        self.persistence.insert_order(order)
        # simpan order misalnya dalam SQL ini akan jalanin INSERT INTO orders .... values ...
        # kenapa update dulu baru insert, karena kalau stock gada, order gaboleh masuk

        # disini baru data di update dan bonus berlaku
        if promo_eligible and free_item and not ignore_bonus:
        # ga kena promo, stok bonus cukup, ignore_bonus = true
            free_order = OrderDTO(customer_name, free_item, 1, 0, True)

            self.persistence.update_stock(free_order)
            self.persistence.insert_order(free_order)
            messages += self.promo_subject.notify(order)
            messages.append(f"🎁 Bonus: 1x {free_item.name} diberikan GRATIS!")

        new_stock = self.persistence.get_stock_report()
        # abis buat order, sekarang mau update stock nya
        # sebagai trigger warning buat notify

        # aplikasi dari observer method 
        if new_stock.coffee_gram <= 500:
            messages += self.stock_subject.notify("Kopi")
        if new_stock.condensed_milk_ml <= 200:
            messages += self.stock_subject.notify("Susu")

        return order, messages
        # karena UI butuh dua hal ini

    # ini cuma lagi passing aja ke persistence karena UI gaboleh langsung akses data dia harus lewat service (backend)
    def get_all_orders(self):
        return self.persistence.get_all_orders()

    def get_stock_report(self):
        return self.persistence.get_stock_report()

    def get_top_buyers(self):
        return self.persistence.get_top_buyers()
