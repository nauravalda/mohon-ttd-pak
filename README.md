# Tugas 4 II4031 2024: Aplikasi Transkrip Akademik Terenkripsi Bertandatangan

#### Daftar algoritma kriptografi yang digunakan atau diimplementasikan
- *RC4*: Algoritma enkripsi basisdata. Diimplementasikan sendiri.
- *Vigenere*: Angoritma enkripsi basisdata (dikombinasikan dengan RC4 untuk memperkuat enkripsi). Diimplementasikan sendiri.
- *RSA*: Algoritma enkripsi kunci publik untuk proses penandatanganan secara digital. Diimplementasikan sendiri.
- *SHA-3*: Algoritma hashing untuk proses penandatanganan secara digital. Menggunakan library.
- *AES*: Algoritma enkripsi berkas PDF. Menggunakan library.

#### Fitur aplikasi
- Pembangkitan pasangan kunci RSA
- Input data akademik mahasiswa, meliputi
  - Data mahasiswa
  - Data mata kuliah
  - Nilai mahasiswa
- Enkripsi-dekripsi basis data dengan algoritma RC4 yang diperkuat Vigenere
- Pembangkitan dan verifikasi tanda tangan digital pada tiap rekaman data akademik dengan algoritma RSA dan SHA-3
- Penampilan isi basis data
- Pembuatan dan verifikasi laporan transkrip akademik mahasiswa berbentuk dokumen PDF yang terenkripsi dengan algoritma AES

## Langkah instalasi
- Pasang Python versi 3.9 atau lebih baru
- Unduh atau lakukan kloning terhadap repo ini pada perangkat Anda
- Masuk ke folder repositori ini
- DISARANKAN: Buat environment Python baru khusus untuk projek ini
  - Buat environment baru dengan perintah `venv .`
  - (Linux/MacOS) Aktifkan environment baru dengan perintah `source bin/activate`
  - (Windows) Aktifkan environment baru dengan perintah `.\Scripts\activate.bat`
- Pasang modul-modul kebutuhan aplikasi menggunakan perintah `pip install -r requirements.txt`
- Jalankan perintah berikut untuk memulai server aplikasi:
```bash
flask run
```

## Langkah penggunaan program
- Buka `http://127.0.0.1:5000` di peramban web
- Bangkitkan seluruh kunci kriptografi yang diperlukan pada menu *Generate Key*
- Masukkan data akademik pada menu *Input data*
- Lihat data akademik mahasiswa pada menu *Show data*. Pada menu ini, terdapat pula opsi untuk  melakukan
  - enkripsi data akademik,
  - dekripsi data akademik,
  - pembangkitan tanda tangan digital,
  - verifikasi tanda tangan digital, dan
  - pengunduhan berkas transkrip akademik terenkripsi
- Lakukan dekripsi dan verifikasi berkas transkrip akademik yang telah diunduh pada menu *Decrypt & Verify*

## Anggota kelompok
- Aufar Ramadhan 18221163
- Naura Valda Prameswari 18221173
