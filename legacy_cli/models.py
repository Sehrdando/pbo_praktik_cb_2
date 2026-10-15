"""Model domain APEX GARAGE PRO (PBO)."""
from dataclasses import dataclass


@dataclass
class Kendaraan:
    id_kendaraan: str
    merk: str
    model: str
    tahun: str
    plat_nomor: str
    status: str = "Tersedia"

    def to_list(self):
        return [self.id_kendaraan, self.merk, self.model, self.tahun, self.plat_nomor, self.status]

    def __str__(self):
        return f"{self.merk} {self.model} ({self.tahun}) • {self.plat_nomor}"


@dataclass
class Pelanggan:
    id_pelanggan: str
    nama: str
    no_hp: str
    alamat: str = ""

    def to_list(self):
        return [self.id_pelanggan, self.nama, self.no_hp, self.alamat]

    def __str__(self):
        return f"{self.nama} ({self.id_pelanggan})"


@dataclass
class Servis:
    id_servis: str
    id_kendaraan: str
    id_pelanggan: str
    keluhan: str
    jenis_servis: str
    mekanik: str
    biaya_jasa: int = 0
    biaya_suku_cadang: int = 0
    status: str = "Menunggu"

    @property
    def total_biaya(self):
        return self.biaya_jasa + self.biaya_suku_cadang
