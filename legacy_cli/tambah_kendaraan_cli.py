import csv
from pathlib import Path
from models import Kendaraan

FOLDER_PROYEK = Path(__file__).resolve().parent
FILE_KENDARAAN = FOLDER_PROYEK / "kendaraan.csv"
HEADER_KENDARAAN = ["ID Kendaraan", "Merek", "Model", "Tahun", "Plat Nomor", "Status"]


def simpan_kendaraan():
    print("\n" + "=" * 46)
    print(" PENDAFTARAN KENDARAAN ".center(46))
    print("=" * 46)

    id_kendaraan = input("ID Kendaraan : ").strip()
    merk = input("Merek        : ").strip()
    model = input("Model        : ").strip()
    tahun = input("Tahun        : ").strip()
    plat_nomor = input("Plat Nomor   : ").strip()

    if not all([id_kendaraan, merk, model, tahun, plat_nomor]):
        print("\n[PERINGATAN] Semua kolom kendaraan wajib diisi.\n")
        return

    kendaraan = Kendaraan(id_kendaraan, merk, model, tahun, plat_nomor)
    file_baru = not FILE_KENDARAAN.exists() or FILE_KENDARAAN.stat().st_size == 0

    with FILE_KENDARAAN.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if file_baru:
            writer.writerow(HEADER_KENDARAAN)
        writer.writerow(kendaraan.to_list())

    print("\n[BERHASIL] Kendaraan berhasil didaftarkan.")
    print(kendaraan)
    print()


def main():
    while True:
        print("\n--- APEX GARAGE / PENDAFTARAN ---")
        print("1. Tambah Kendaraan")
        print("0. Kembali ke Menu Utama")
        pilihan = input("APEX > Pilih menu: ").strip()

        if pilihan == "1":
            simpan_kendaraan()
        elif pilihan == "0":
            print("Kembali ke menu utama.\n")
            break
        else:
            print("[PERINGATAN] Pilihan tidak valid.\n")


if __name__ == "__main__":
    main()
