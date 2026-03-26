class UI:
    def __init__(self, service):
        self.service = service

    def show_menu(self):
        print("""
===== KEDAI KOPI INDAH RIA =====
1. Expresso  (10,5rb). 
2. Kopi Susu  (20,5rb). 
3. Kopi hitam sepahit hidup (8,0rb). 
4. Cetak penjualan. 
5. Cetak sisa stok. 
6. Cetak 5 pembeli terbanyak. 
7. Keluar
""")

    def input_order(self, menu_id):
        customer = input("Nama pelanggan: ")

        try:
            qty = int(input("Jumlah pesanan: "))
            if qty <= 0:
                print("[❌] Jumlah tidak valid.\n")
                return
        except:
            print("[❌] Jumlah harus angka.\n")
            return

        print("Memproses pesanan...\n")

        order, messages = self.service.order_coffee(customer, menu_id, qty)

        # CASE 1: transaksi gagal (stok/invalid)
        if order is None:
            for msg in messages:
                print(msg)
            print()
            return

        # CASE 2: butuh konfirmasi bonus
        if isinstance(order, str) and order == "CONFIRM_BONUS":
            for msg in messages:
                print(msg)

            jawab = input("Lanjut tanpa bonus? (y/n): ").lower()
            if jawab == "y":
                order, messages = self.service.order_coffee(customer, menu_id, qty, ignore_bonus=True)
            else:
                print("\n❌ Transaksi dibatalkan.\n")
                return

        # CASE 3: transaksi sukses
        print(f"Total: Rp{order.total}")
        for msg in messages:
            print(msg)
        print()

    def run(self):
        while True:
            self.show_menu()
            pilihan = input("Masukkan pilihan: ")

            if pilihan == "1":
                print("Anda memesan : Espresso (10,5rb)")
                self.input_order(1)

            elif pilihan == "2":
                print("Anda memesan : Kopi Susu (20.5 rb)")
                self.input_order(2)

            elif pilihan == "3":
                print("Anda memesan : Kopi pahit sepahit hidup (8.0 rb)")
                self.input_order(3)

            elif pilihan == "4":
                print("\n===== RIWAYAT PENJUALAN =====")
                orders = self.service.get_all_orders()

                if not orders:
                    print("Belum ada transaksi")
                else:
                    for o in orders:
                        print(
                            f"{o.customer_name} membeli {o.quantity}x {o.menu.name} "
                            f"(Total: Rp{o.total}) {'(Promo)' if o.promo_applied else ''}"
                        )

            elif pilihan == "5":
                stock = self.service.get_stock_report()
                print("\n===== SISA STOK =====")
                print(f"Kopi   : {stock.coffee_gram} gram")
                print(f"Susu   : {stock.condensed_milk_ml} ml")

            elif pilihan == "6":
                print("\n===== TOP 5 CUSTOMER =====")
                top = self.service.get_top_buyers()

                if not top:
                    print("Belum ada data.")
                else:
                    for name, amount in top:
                        print(f"{name} - Rp{amount}")

            elif pilihan == "7":
                print("\nTerima kasih sudah mampir di Kedai Kopi Ria ☕✨\n")
                break

            else:
                print("Invalid Input")
