# Laporan Resmi Praktikum Modul 1 Jarkom

| No | Nama Anggota | NRP |
|---|---|---|
| 1. | Atik Putri Matulina | 5027251128 |
| 2. | Muhammad Syihan Zhafiri | 5027251052 |

> Prefix IP Kelompok: `10.70.x.x` (K-13) · Controller GNS3: `http://10.4.89.246` (Group A) · Image: `ardhptr21/debinet:latest`

## Soal 1

> Untuk mempersiapkan pembangunan The Wired, Lain yang berperan sebagai Router membuat tiga Switch/Gateway: Switch 1 menuju dua Entitas yaitu Alice dan Mika, Switch 2 menuju Chisa, sedangkan Switch 3 menuju Knights dan Eiri. Kelima Entitas tersebut dikonfigurasi sebagai Client di GNS3. [GUNAKAN PREFIX IP MASING-MASING KELOMPOK]

---

### Konfigurasi

Topologi dibangun dengan 1 router (Lain), 3 Ethernet switch, 5 client (`ardhptr21/debinet:latest`), dan 1 node NAT. Pembagian subnet menggunakan prefix kelompok K-13 yaitu `10.70.x.x` dengan satu /24 per switch:

| Subnet | Switch | Node | Interface | IP Address |
|---|---|---|---|---|
| 10.70.1.0/24 | SW1 | Lain | eth1 | 10.70.1.1/24 |
| | | Alice | eth0 | 10.70.1.2/24 |
| | | Mika | eth0 | 10.70.1.3/24 |
| 10.70.2.0/24 | SW2 | Lain | eth2 | 10.70.2.1/24 |
| | | Chisa | eth0 | 10.70.2.2/24 |
| 10.70.3.0/24 | SW3 | Lain | eth3 | 10.70.3.1/24 |
| | | Knights | eth0 | 10.70.3.2/24 |
| | | Eiri | eth0 | 10.70.3.3/24 |

Konfigurasi pada router Lain (`/etc/network/interfaces`) — interface eth1–eth3 sebagai gateway masing-masing subnet (eth0 pada WAN akan dikonfigurasi pada Soal 2):
```
auto eth1
iface eth1 inet static
    address 10.70.1.1
    netmask 255.255.255.0
auto eth2
iface eth2 inet static
    address 10.70.2.1
    netmask 255.255.255.0
auto eth3
iface eth3 inet static
    address 10.70.3.1
    netmask 255.255.255.0
```

Lain diberi 4 network adapter: eth0 untuk WAN/NAT (dikonfigurasi pada Soal 2),
serta eth1–eth3 sebagai gateway ketiga LAN sesuai konfigurasi di atas. Pada
sisi client, setiap Entitas dikonfigurasi IP statis dengan gateway mengarah ke
interface Lain di subnet masing-masing — contoh pada Alice
(`/etc/network/interfaces`):
```
auto eth0
iface eth0 inet static
    address 10.70.1.2
    netmask 255.255.255.0
    gateway 10.70.1.1
    up echo "nameserver 8.8.8.8" > /etc/resolv.conf
```
### Verifikasi

Hasil `ip -br a` pada node menunjukkan setiap interface telah memiliki IP sesuai skema pengalamatan di atas:

![verifikasi IP](assets/soal1-verifikasiip.png)

![topologi](assets/soal1-topologi.png)

## Soal 2

> Karena menurut Lain pada saat itu The Wired masih terisolasi dari dunia luar, konfigurasikan router Lain agar dapat tersambung langsung ke jaringan internet publik melalui NAT/DHCP pada interface eth0.

---
### Konfigurasi

Interface eth0 pada router Lain dikonfigurasi untuk meminta alamat secara
dinamis (DHCP) dari node NAT GNS3, yang menyediakan jembatan ke jaringan
 fisik host. DNS resolver 8.8.8.8 diatur agar Lain juga mampu melakukan
resolusi nama domain (`/etc/network/interfaces`):
```
auto eth0
iface eth0 inet dhcp
    up echo "nameserver 8.8.8.8" > /etc/resolv.conf
```
### Verifikasi

Setelah node dinyalakan, eth0 mendapatkan IP dari DHCP NAT dan router Lain
berhasil mencapai internet publik:

![test dhcp nat](assets/soal2-testdhcpnat.png)

## Soal 3

> Setelah router Lain terhubung ke internet, pastikan seluruh Entitas (Client) di bawah Switch 1, Switch 2, dan Switch 3 dapat saling terhubung dan berkomunikasi satu sama lain melalui konfigurasi routing.

---

### Konfigurasi

Tidak diperlukan konfigurasi routing tambahan. Router Lain secara otomatis mengenal ketiga subnet LAN (10.70.1.0/24, 10.70.2.0/24, 10.70.3.0/24) sebagai directly-connected network pada eth1-eth3, sehingga kernel Linux langsung membuat entri routing untuk masing-masing subnet. Pada sisi client, default gateway sudah diarahkan ke IP Lain di subnet masing-masing (10.70.x.1) pada konfigurasi Soal 1, sehingga paket antar-subnet otomatis diteruskan Lain:

![ip r dari lain](assets/soal3-iprlain.png)

### Verifikasi

Kami membuat script otomatis (dengan bantuan AI) yang terhubung ke konsol
telnet setiap node melalui GNS3 API, lalu menjalankan `ping` dari setiap
client ke seluruh client lain dan mencatat hasilnya sebagai matriks
konektivitas. Script tersebut juga otomatis menunggu hingga setiap node
selesai booting (interface eth0 sudah memiliki IP) sebelum pengujian
dimulai, sehingga hasilnya konsisten. Kode lengkap ada pada
`assets/soal3-verify_routing.py`.

Hasilnya, seluruh 20 kombinasi pengujian antar-client (termasuk semua
pasangan lintas subnet) berhasil:

![cross-client ping test](assets/soal3-pingtest.png)

## Soal 4

> Lain ingin agar setiap Entitas (Client) memiliki kemandirian di The Wired. Konfigurasikan firewall/iptables (NAT Masquerade) dan DNS resolver agar setiap Client dapat terhubung ke internet secara mandiri (dapat melakukan ping ke 8.8.8.8 dan membuka domain web google.com).

---

### Konfigurasi

Agar paket dari jaringan internal (10.70.x.x) dapat mencapai internet, router Lain perlu mengaktifkan IP forwarding dan menyamarkan (masquerade) alamat sumber paket menjadi IP publik eth0. Rule tersebut ditambahkan pada blok eth0 di `/etc/network/interfaces` dengan baris `up` agar otomatis aktif setiap node dinyalakan:
```
auto eth0
iface eth0 inet dhcp
    up echo "nameserver 8.8.8.8" > /etc/resolv.conf
    up sysctl -w net.ipv4.ip_forward=1
    up iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    up iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
    up iptables -A FORWARD -i eth2 -o eth0 -j ACCEPT
    up iptables -A FORWARD -i eth3 -o eth0 -j ACCEPT
    up iptables -A FORWARD -i eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT
```

Penjelasan tiap rule:
- `sysctl -w net.ipv4.ip_forward=1` - mengizinkan kernel meneruskan paket antar-interface (tanpa ini paket dari LAN tidak akan pernah keluar lewat eth0).
- `iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE` - NAT masquerade: source IP private (10.70.x.x) diganti menjadi IP DHCP eth0 saat paket keluar ke internet, sehingga balasan dari internet tahu harus kembali ke Lain.
- `iptables -A FORWARD -i eth1..3 -o eth0 -j ACCEPT` - mengizinkan trafik dari ketiga LAN keluar ke WAN.
- `iptables -A FORWARD -i eth0 -m state --state ESTABLISHED,RELATED -j ACCEPT` - mengizinkan paket balasan dari internet masuk kembali ke LAN (hanya untuk koneksi yang sudah dibangun dari dalam).

DNS resolver sudah dikonfigurasi pada tiap client sejak Soal 1 (`nameserver 8.8.8.8` di `/etc/resolv.conf`), sehingga client juga mampu melakukan resolusi nama domain.

### Verifikasi

Dari console client, dilakukan pengujian `ping` ke IP DNS publik (8.8.8.8) dan ke nama domain (google.com). Berikut hasil dari node Alice (10.70.1.2, SW1):

![ping dns and google @ alice](assets/soal4-alicepingtest.png)

Dan dari node Eiri (10.70.3.3, SW3) untuk mewakili subnet berbeda:

![ping dns and google @ eiri](assets/soal4-eiripingtest.png)

## Soal 5

> Eiri tetap berupaya menanamkan kekacauan ke dalam jaringan. Untuk mengantisipasi restart tiba-tiba, pastikan seluruh konfigurasi jaringan tidak hilang saat semua node di-restart. Buat script verifikasi di /root/cek_status.sh pada router Lain yang menampilkan ringkasan interface (ip -br a) dan status tabel NAT (iptables -t nat -L -v -n) setelah reboot.

### Konfigurasi

Karena node GNS3 berbasis container Docker yang bersifat ephemeral, konfigurasi jaringan harus dipasang agar otomatis aktif kembali setiap node dinyalakan. Seluruh konfigurasi jaringan (IP statis, gateway, DNS resolver, ip_forward, dan rule NAT MASQUERADE) sudah ditulis pada `/etc/network/interfaces` dengan baris `up` (Soal 1–4), sehingga dieksekusi ulang secara otomatis oleh `ifupdown` setiap boot. Hanya direktori `/root` yang persisten pada container, sehingga script verifikasi diletakkan di `/root/cek_status.sh`:

```
#!/bin/sh
echo "=== Ringkasan Interface (ip -br a) ==="
ip -br a
echo ""
echo "=== Status Tabel NAT (iptables -t nat -L -v -n) ==="
iptables -t nat -L -v -n
```

Script dibuat executable dengan `chmod +x /root/cek_status.sh`.

### Verifikasi

Sebagai simulasi restart tiba-tiba, seluruh node dihentikan kemudian
dinyalakan kembali. Setelah semua node up, `cek_status.sh` dijalankan pada
router Lain dan hasilnya menunjukkan seluruh konfigurasi tetap bertahan:

- Seluruh interface LAN tetap terpasang: eth1 `10.70.1.1`, eth2 `10.70.2.1`,
  eth3 `10.70.3.1`, dan eth0 kembali mendapat IP DHCP dari NAT.
- Rule `MASQUERADE` dan `FORWARD` pada tabel iptables tetap aktif (diterapkan
  ulang oleh baris `up` saat boot).

Sebelum reboot:

![soal5-beforereboot](assets/soal5-beforereboot.png)

Setelah reboot:

![soal5-afterreboot](assets/soal5-afterreboot.png)