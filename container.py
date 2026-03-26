# -- memutuskan mau pake database apa, SQL/Dict
from .database import SQLiteCoffeePersistence
# from ..mocks import MockPersistence

from .backend import CoffeeService, StockSubject, StockObserver, PromoSubject, PromoObserver
from .ui import UI

# Container cuma pasang"in aja 

class Container:
    def __init__(self, dbInit=False):
        self.dbInit = dbInit
        # conditional option
        # Karena Container itu bukan tempat menjalankan logika, tapi tempat memberikan konfigurasi.
        # Secara teori, Container merepresentasikan:
        # Aplikasi ini bisa dijalankan dalam beberapa mode.
        self.ui = None
        # Karena Container belum tahu UI-nya harus dibuat sebelum semua dependency lain siap.
        # nandain dulu dia exist atributnya

    def create_persistence(self):
        return SQLiteCoffeePersistence(init=self.dbInit)
        # return MockPersistence()
 
    def create_stock_subject(self):
        return StockSubject()
    
    def create_promo_subject(self):
        return PromoSubject()

    def create_service(self, persistence, stock_subject, promo_subject):
        return CoffeeService(persistence, stock_subject, promo_subject)
    
    def create_ui(self, service):
        return UI(service)
    
    def start(self):
        persistence = self.create_persistence()
        stock_subject = self.create_stock_subject()
        promo_subject = self.create_promo_subject()

        stock_observer = StockObserver()
        promo_observer = PromoObserver()

        stock_subject.add_observer(stock_observer)
        promo_subject.add_observer(promo_observer)

        service = self.create_service(persistence, stock_subject, promo_subject)
        self.ui = self.create_ui(service)

    def run(self):
        if self.ui is None:
            # kalo UI belum ada, dia start
            self.start()
        self.ui.run()