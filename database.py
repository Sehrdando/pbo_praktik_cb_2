"""Penyimpanan SQLite dan operasi data APEX GARAGE PRO."""
import csv
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "apex_garage.db"
CSV_PATH = BASE_DIR / "kendaraan.csv"


class Database:
    def __init__(self, path=DB_PATH):
        self.path = Path(path)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS kendaraan (
                    id_kendaraan TEXT PRIMARY KEY,
                    merk TEXT NOT NULL,
                    model TEXT NOT NULL,
                    tahun TEXT NOT NULL,
                    plat_nomor TEXT NOT NULL,
                    jenis TEXT NOT NULL DEFAULT 'Mobil',
                    status TEXT NOT NULL DEFAULT 'Tersedia',
                    nomor_rangka TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS pelanggan (
                    id_pelanggan TEXT PRIMARY KEY,
                    nama TEXT NOT NULL,
                    no_hp TEXT NOT NULL,
                    alamat TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS servis (
                    id_servis TEXT PRIMARY KEY,
                    id_kendaraan TEXT NOT NULL,
                    id_pelanggan TEXT NOT NULL,
                    tanggal_masuk TEXT NOT NULL,
                    keluhan TEXT NOT NULL,
                    jenis_servis TEXT NOT NULL,
                    mekanik TEXT NOT NULL,
                    estimasi_selesai TEXT NOT NULL DEFAULT '',
                    biaya_jasa INTEGER NOT NULL DEFAULT 0,
                    biaya_suku_cadang INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'Menunggu',
                    catatan TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(id_kendaraan) REFERENCES kendaraan(id_kendaraan) ON UPDATE CASCADE,
                    FOREIGN KEY(id_pelanggan) REFERENCES pelanggan(id_pelanggan) ON UPDATE CASCADE
                );
                CREATE TABLE IF NOT EXISTS pembayaran (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_servis TEXT NOT NULL,
                    jumlah INTEGER NOT NULL CHECK(jumlah > 0),
                    tanggal TEXT NOT NULL,
                    metode TEXT NOT NULL DEFAULT 'Tunai',
                    catatan TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY(id_servis) REFERENCES servis(id_servis) ON UPDATE CASCADE ON DELETE CASCADE
                );
            """)
        self._migrate_legacy_csv()

    def _migrate_legacy_csv(self):
        """Impor CSV lama hanya jika tabel kendaraan masih kosong; CSV tidak diubah."""
        if not CSV_PATH.exists() or CSV_PATH.stat().st_size == 0:
            return
        with self.connect() as conn:
            if conn.execute("SELECT COUNT(*) FROM kendaraan").fetchone()[0] > 0:
                return
            try:
                with CSV_PATH.open("r", newline="", encoding="utf-8-sig") as file:
                    reader = csv.reader(file)
                    first = next(reader, None)
                    if not first:
                        return
                    # Header lama biasanya berupa nama kolom, tetapi dukung juga CSV tanpa header.
                    header_words = " ".join(first).lower()
                    rows = reader if ("kendaraan" in header_words or "merek" in header_words or "plat" in header_words) else iter([first, *reader])
                    for row in rows:
                        if not row or len(row) < 5:
                            continue
                        vehicle_id, merk, model, tahun, plate = [str(v).strip() for v in row[:5]]
                        status = str(row[5]).strip() if len(row) > 5 and row[5].strip() else "Tersedia"
                        if not all([vehicle_id, merk, model, tahun, plate]):
                            continue
                        try:
                            conn.execute(
                                "INSERT OR IGNORE INTO kendaraan (id_kendaraan, merk, model, tahun, plat_nomor, status) VALUES (?, ?, ?, ?, ?, ?)",
                                (vehicle_id, merk, model, tahun, plate, status),
                            )
                        except sqlite3.Error:
                            # Satu baris rusak tidak boleh menghentikan migrasi seluruh file.
                            continue
            except (OSError, csv.Error):
                return

    # Kendaraan
    def list_vehicles(self, search="", jenis="Semua"):
        sql = "SELECT * FROM kendaraan WHERE (id_kendaraan LIKE ? OR merk LIKE ? OR model LIKE ? OR plat_nomor LIKE ?)"
        q = f"%{search}%"
        params = [q, q, q, q]
        if jenis != "Semua":
            sql += " AND jenis = ?"
            params.append(jenis)
        sql += " ORDER BY created_at DESC, merk COLLATE NOCASE"
        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()

    def save_vehicle(self, data, original_id=None):
        with self.connect() as conn:
            if original_id:
                conn.execute("""UPDATE kendaraan SET id_kendaraan=?, merk=?, model=?, tahun=?, plat_nomor=?, jenis=?, status=?, nomor_rangka=? WHERE id_kendaraan=?""",
                             (*data, original_id))
            else:
                conn.execute("""INSERT INTO kendaraan (id_kendaraan, merk, model, tahun, plat_nomor, jenis, status, nomor_rangka) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", data)

    def delete_vehicle(self, vehicle_id):
        with self.connect() as conn:
            if conn.execute("SELECT 1 FROM servis WHERE id_kendaraan=? LIMIT 1", (vehicle_id,)).fetchone():
                raise ValueError("Kendaraan sudah memiliki riwayat servis dan tidak bisa dihapus.")
            conn.execute("DELETE FROM kendaraan WHERE id_kendaraan=?", (vehicle_id,))

    # Pelanggan
    def list_customers(self, search=""):
        q = f"%{search}%"
        with self.connect() as conn:
            return conn.execute("""SELECT p.*,
                (SELECT COUNT(DISTINCT s.id_kendaraan) FROM servis s WHERE s.id_pelanggan=p.id_pelanggan) AS jumlah_kendaraan
                FROM pelanggan p
                WHERE p.id_pelanggan LIKE ? OR p.nama LIKE ? OR p.no_hp LIKE ?
                ORDER BY p.created_at DESC, p.nama COLLATE NOCASE""", (q, q, q)).fetchall()

    def save_customer(self, data, original_id=None):
        with self.connect() as conn:
            if original_id:
                conn.execute("UPDATE pelanggan SET id_pelanggan=?, nama=?, no_hp=?, alamat=? WHERE id_pelanggan=?", (*data, original_id))
            else:
                conn.execute("INSERT INTO pelanggan (id_pelanggan, nama, no_hp, alamat) VALUES (?, ?, ?, ?)", data)

    def delete_customer(self, customer_id):
        with self.connect() as conn:
            if conn.execute("SELECT 1 FROM servis WHERE id_pelanggan=? LIMIT 1", (customer_id,)).fetchone():
                raise ValueError("Pelanggan sudah memiliki riwayat servis dan tidak bisa dihapus.")
            conn.execute("DELETE FROM pelanggan WHERE id_pelanggan=?", (customer_id,))

    def customers_for_combo(self):
        with self.connect() as conn:
            return conn.execute("SELECT id_pelanggan, nama, no_hp FROM pelanggan ORDER BY nama").fetchall()

    def vehicles_for_combo(self):
        with self.connect() as conn:
            return conn.execute("SELECT id_kendaraan, merk, model, plat_nomor FROM kendaraan ORDER BY merk, model").fetchall()

    # Servis
    def list_services(self, search="", status="Semua"):
        q = f"%{search}%"
        sql = """SELECT s.*, k.merk, k.model, k.plat_nomor, p.nama AS nama_pelanggan,
                  (s.biaya_jasa + s.biaya_suku_cadang) AS total_biaya,
                  COALESCE((SELECT SUM(pb.jumlah) FROM pembayaran pb WHERE pb.id_servis=s.id_servis),0) AS sudah_dibayar
                  FROM servis s JOIN kendaraan k ON s.id_kendaraan=k.id_kendaraan
                  JOIN pelanggan p ON s.id_pelanggan=p.id_pelanggan
                  WHERE (s.id_servis LIKE ? OR k.plat_nomor LIKE ? OR p.nama LIKE ? OR s.keluhan LIKE ?)"""
        params = [q, q, q, q]
        if status != "Semua":
            sql += " AND s.status = ?"
            params.append(status)
        sql += " ORDER BY s.created_at DESC"
        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()

    def create_service(self, data):
        with self.connect() as conn:
            conn.execute("""INSERT INTO servis (id_servis, id_kendaraan, id_pelanggan, tanggal_masuk, keluhan, jenis_servis, mekanik, estimasi_selesai, biaya_jasa, biaya_suku_cadang, status, catatan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", data)
            conn.execute("UPDATE kendaraan SET status='Dalam Servis' WHERE id_kendaraan=?", (data[1],))

    def update_service_status(self, service_id, status):
        with self.connect() as conn:
            conn.execute("UPDATE servis SET status=? WHERE id_servis=?", (status, service_id))
            row = conn.execute("SELECT id_kendaraan FROM servis WHERE id_servis=?", (service_id,)).fetchone()
            if row:
                active = conn.execute("SELECT COUNT(*) FROM servis WHERE id_kendaraan=? AND status NOT IN ('Selesai','Diambil Pelanggan')", (row[0],)).fetchone()[0]
                if active == 0:
                    conn.execute("UPDATE kendaraan SET status='Tersedia' WHERE id_kendaraan=?", (row[0],))
                else:
                    conn.execute("UPDATE kendaraan SET status='Dalam Servis' WHERE id_kendaraan=?", (row[0],))

    def add_payment(self, service_id, amount, method, note=""):
        with self.connect() as conn:
            service = conn.execute("SELECT biaya_jasa + biaya_suku_cadang AS total FROM servis WHERE id_servis=?", (service_id,)).fetchone()
            if not service:
                raise ValueError("Order servis tidak ditemukan.")
            paid = conn.execute("SELECT COALESCE(SUM(jumlah),0) FROM pembayaran WHERE id_servis=?", (service_id,)).fetchone()[0]
            due = int(service["total"]) - int(paid)
            if amount <= 0:
                raise ValueError("Nominal pembayaran harus lebih dari nol.")
            if amount > due:
                raise ValueError(f"Pembayaran melebihi sisa tagihan Rp{due:,.0f}.")
            conn.execute("INSERT INTO pembayaran (id_servis, jumlah, tanggal, metode, catatan) VALUES (?, ?, ?, ?, ?)",
                         (service_id, amount, date.today().isoformat(), method, note))

    def list_payments(self):
        with self.connect() as conn:
            return conn.execute("""SELECT pb.*, s.biaya_jasa+s.biaya_suku_cadang AS total_biaya,
                s.id_servis, p.nama AS nama_pelanggan, k.plat_nomor
                FROM pembayaran pb JOIN servis s ON pb.id_servis=s.id_servis
                JOIN pelanggan p ON s.id_pelanggan=p.id_pelanggan
                JOIN kendaraan k ON s.id_kendaraan=k.id_kendaraan
                ORDER BY pb.id DESC""").fetchall()

    def dashboard_stats(self):
        today = date.today().isoformat()
        with self.connect() as conn:
            vehicles = conn.execute("SELECT COUNT(*) FROM kendaraan").fetchone()[0]
            customers = conn.execute("SELECT COUNT(*) FROM pelanggan").fetchone()[0]
            today_services = conn.execute("SELECT COUNT(*) FROM servis WHERE tanggal_masuk=?", (today,)).fetchone()[0]
            active = conn.execute("SELECT COUNT(*) FROM servis WHERE status NOT IN ('Selesai','Diambil Pelanggan')").fetchone()[0]
            done = conn.execute("SELECT COUNT(*) FROM servis WHERE status IN ('Selesai','Diambil Pelanggan') AND tanggal_masuk=?", (today,)).fetchone()[0]
            revenue = conn.execute("SELECT COALESCE(SUM(jumlah),0) FROM pembayaran WHERE tanggal=?", (today,)).fetchone()[0]
            return {"vehicles": vehicles, "customers": customers, "today_services": today_services,
                    "active": active, "done": done, "revenue": revenue}

    def revenue_last_seven_days(self):
        days = [date.today() - timedelta(days=i) for i in range(6, -1, -1)]
        result = {d.isoformat(): 0 for d in days}
        with self.connect() as conn:
            rows = conn.execute("SELECT tanggal, SUM(jumlah) AS total FROM pembayaran WHERE tanggal >= ? GROUP BY tanggal", (days[0].isoformat(),)).fetchall()
        for row in rows:
            if row["tanggal"] in result:
                result[row["tanggal"]] = row["total"] or 0
        return [(d.strftime("%a"), result[d.isoformat()]) for d in days]

    def service_summary(self):
        with self.connect() as conn:
            return conn.execute("""SELECT jenis_servis, COUNT(*) AS jumlah FROM servis GROUP BY jenis_servis ORDER BY jumlah DESC LIMIT 5""").fetchall()

    def report_rows(self, start_date=None, end_date=None):
        sql = """SELECT s.id_servis, s.tanggal_masuk, p.nama AS pelanggan, k.plat_nomor,
                  s.jenis_servis, s.mekanik, s.status,
                  s.biaya_jasa+s.biaya_suku_cadang AS total,
                  COALESCE((SELECT SUM(pb.jumlah) FROM pembayaran pb WHERE pb.id_servis=s.id_servis),0) AS dibayar
                  FROM servis s JOIN pelanggan p ON s.id_pelanggan=p.id_pelanggan JOIN kendaraan k ON s.id_kendaraan=k.id_kendaraan"""
        clauses, params = [], []
        if start_date:
            clauses.append("s.tanggal_masuk >= ?")
            params.append(start_date)
        if end_date:
            clauses.append("s.tanggal_masuk <= ?")
            params.append(end_date)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY s.tanggal_masuk DESC"
        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()
