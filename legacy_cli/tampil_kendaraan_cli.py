import csv
from pathlib import Path

FOLDER_PROYEK = Path(__file__).resolve().parent
FILE_KENDARAAN = FOLDER_PROYEK / "kendaraan.csv"
KOLOM = ["ID Kendaraan", "Merek", "Model", "Tahun", "Plat Nomor", "Status"]


def muat_data():
    print("\n" + "=" * 92)
    print(" REGISTRASI KENDARAAN APEX GARAGE ".center(92))
    print("=" * 92)

    if not FILE_KENDARAAN.exists() or FILE_KENDARAAN.stat().st_size == 0:
        print("Belum ada data kendaraan.")
        print("Tambahkan kendaraan melalui menu 'Tambah Kendaraan'.\n")
        return

    with FILE_KENDARAAN.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # Lewati baris header.
        data = [row for row in reader if row]

    if not data:
        print("Belum ada data kendaraan.\n")
        return

    lebar = [14, 14, 18, 8, 16, 12]
    garis = "+" + "+".join("-" * (w + 2) for w in lebar) + "+"
    print(garis)
    print("|" + "|".join(f" {judul:<{w}} " for judul, w in zip(KOLOM, lebar)) + "|")
    print(garis)

    for row in data:
        row = (row + [""] * len(KOLOM))[:len(KOLOM)]
        cells = [str(value)[:w].ljust(w) for value, w in zip(row, lebar)]
        print("|" + "|".join(f" {value} " for value in cells) + "|")

    print(garis)
    print(f"Total kendaraan terdaftar: {len(data)}\n")


def main():
    muat_data()
    input("Tekan Enter untuk kembali ke menu utama...")


if __name__ == "__main__":
    main()
