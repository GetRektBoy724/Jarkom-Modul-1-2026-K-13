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

---

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

## Soal 14

> Setelah gagal mengakses FTP, Eiri melancarkan serangan brute-force terhadap form login web Alice. Analisis file capture wired_bruteforce.pcapng untuk mengidentifikasi alamat IP penyerang, target IP beserta port yang diserang, password user lain_admin yang berhasil ditembus, serta web server software dan versi yang dilaporkan pada response header.

---

### Analisis

Kita buka file pcap-nya memakai WireShark lalu langsung filter dengan "http"

![soal14-filterhttp](assets/soal14-filterhttp.png)

Kita langsung cari request POST yang menghasilkan response 200 OK dengan cara meng-scroll ke paling bawah.

![soal14-postreturnok](assets/soal14-postreturnok.png)

Kita buka packet request POST nya tadi, dan kita bisa mendapatkan username dan passwordnya. Di satu packet ini, kita juga bisa mendapatkan IP penyerang, IP target, dan portnya.

![soal14-postreqpacket](assets/soal14-postreqpacket.png)

Dan di packet response dari POST request tadi, kita bisa mendapatkan webserver software dan versi yang digunakan.

![soal14-postrespacket](assets/soal14-postrespacket.png)

### Hasil yang didapatkan

- IP Penyerang : 172.26.7.50
- IP yang diserang : 172.26.7.100
- Port yang diserang : 8080
- Username : lain_admin
- Password : wired_pr0tocol_7
- Webserver software dan versi : Apache 2.4.62
- Flag : KOMJAR26{W1r3d_Brut3_FQTsG25AhaGkqnrr4oXOG1ejr}

## Soal 15

> Eiri menyusup ke ruang server dan memasang perangkat keyboard USB berbahaya pada node Alice. Buka file capture wired_usb_hid.pcap, identifikasi Vendor ID dan Product ID perangkat USB dari deskriptor USB, alamat nomor device USB, serta pesan rahasia yang berhasil dicuri dari keystroke.

---

### Analisis

File capture berisi trafik USB (bukan Ethernet). Device descriptor pada frame awal berisi field idVendor dan idProduct:

![soal15-vendorproduct](assets/soal15-vendorproduct.png)

- Vendor ID: 0x046d (Logitech)
- Product ID: 0xc31c

Alamat device USB terlihat pada kolom source paket data HID: `2.7.1` berarti bus 2, device address 7, endpoint 1. Semua 60 paket keystroke berasal dari device address 7.

Pesan rahasia didekode dari paket HID Input Report (usb.capdata): setiap paket "USB INTERRUPT in" berisi 8 byte dengan byte ke-3 adalah keycode HID. Mengonversi keycode ke karakter (tabel HID Usage Keyboard, memperhitungkan modifier Shift padabyte pertama) menghasilkan pesan `Wired_Protocol_7_is_alive_2026`

![soal15-datarahasia](assets/soal15-datarahasia.png)
```
frame 26: 02 00 1a 00 00 00 00 00
          │  │  │
          │  │  └─ keycode 0x1a = 'w' key
          │  └──── reserved (selalu 00)
          └─────── modifier = 0x02 = Left Shift
```

### Hasil yang didapatkan

- Vendor ID: 0x046d (Logitech)
- Product ID: 0xc31c
- Pesan rahasia : `Wired_Protocol_7_is_alive_2026`
- Flag : KOMJAR26{USB_K3ystr0k3_tB8aNg7YhlAEqo61xn3CpihSQ}

## Soal 16

> Eiri meletakkan file malware di server. Dari file capture wired_ftp_theft.pcap, lakukan analisis lalu lintas FTP untuk mengidentifikasi alamat IP server FTP penyerang, banner software FTP yang digunakan, kredensial login penyerang, serta ukuran (size in bytes) dari file malware knights_payload.exe yang diunduh.

---

### Analisis

File capture memuat beberapa sesi FTP. Filter `ftp` memperlihatkan tiga server FTP berbeda; sesi yang melibatkan transfer malware diidentifikasi dari perintah "RETR knights_payload.exe", yaitu sesi antara 10.7.3.50 (client) dan 198.51.100.7 (server FTP penyerang).

![soal16-trafficftpattacker](assets/soal16-trafficftpattacker.png)

Dari traffic diatas, sudah keliatan semuanya bahwa:
- IP server FTP penyerang: 198.51.100.7
- Banner software FTP: "Welcome to Wired FTP Server (vsftpd 3.0.5)" - vsftpd 3.0.5
- Kredensial login penyerang: knights_agent / N4v1_s3cur3_2026
- Ukuran file malware knights_payload.exe: 524288 bytes

### Hasil yang didapatkan

- IP server FTP penyerang: 198.51.100.7
- software FTP: "vsftpd 3.0.5"
- Kredensial login penyerang: knights_agent:N4v1_s3cur3_2026
- Ukuran file malware knights_payload.exe: 524288
- Flag : KOMJAR26{FTP_Th3ft_7URCBhOeqDltM5Bg3e25pfmLB}

## Soal 17

> Alice membuat halaman web di node-nya. Eiri memanfaatkan celah untuk mengunduh payload berbahaya ke sistem Alice. Analisis file capture wired_http_c2.pcap untuk mengidentifikasi nama domain (Host) tempat malware diunduh, alamat IP server penyerang, nama file executable malware yang diunduh, serta kode status HTTP yang dikembalikan.

---

### Analisis

File capture memuat beberapa sesi HTTP dari dua host berbeda. Filter `http.request` memperlihatkan tiga request: GET style.css ke cdnstore.io, GET / ke protocol7.co.jp, dan satu request pengunduhan file executable:

![soal17-httprequests](assets/soal17-httprequests.png)

![soal17-executabledownload](assets/soal17-executabledownload.png)

Sebelum request tersebut, terdapat query DNS untuk wired-update.net yang terjawab dengan alamat 203.0.113.42 - berarti domain malware tersebut di-resolve ke IP server penyerang. Respons dari server:

![soal17-dnsrequest](assets/soal17-dnsrequest.png)

![soal17-executabledownloadresponse](assets/soal17-executabledownloadresponse.png)

Payload respons diawali byte `4d 5a` ("MZ") — signature header file executable Windows (PE), mengonfirmasi bahwa file yang diunduh memang executable.

### Hasil yang didapatkan

- Domain (Host) tempat malware diunduh: wired-update.net
- IP server penyerang: 203.0.113.42
- Nama file executable malware: navi_agent.exe
- Kode status HTTP: 200 (OK)
- Flag : KOMJAR26{Navi_C2_D0wnl04d_Wc0u3xBFzqbnuTbeoN2T1KpMr}

## Soal 18

> Eiri mengubah taktik penyerangan dengan menanamkan file malware menggunakan protokol file sharing SMB. Analisis file capture wired_smb_transfer.pcapng untuk mengidentifikasi nama protokol jaringan yang dieksploitasi, IP pengirim dan penerima, folder tujuan penyimpanan malware pada sistem korban, serta nama file executable malware yang ditransfer.

---

### Analisis

File capture memuat satu sesi TCP ke port 445 milik 10.7.1.50 — port dan layanan Server Message Block (SMB2). Alur sesinya:

1. Negotiate Protocol Request/Response
2. Session Setup Request/Response
3. Tree Connect Request  Tree: \\10.7.1.50\ADMIN$
4. Create Request  File: System32\wired_trojan_payload.exe
5. Write Request    Len:1028 Off:0 File: System32\wired_trojan_payload.exe
6. Close Request/Response

![soal18-smbtraffic](assets/soal18-smbtraffic.png)

Penyerang (10.7.3.100) melakukan autentikasi lalu terhubung ke share administratif ADMIN$ milik korban (10.7.1.50). Share ADMIN$ dipetakan ke direktori C:\Windows, sehingga file malware ditulis langsung ke folder tersebut pada sistem korban. Pola seperti ini (menulis executable ke System32 lewat ADMIN$) adalah ciri khas teknik lateral movement ala PsExec.

### Hasil yang didapatkan

- Protokol yang dieksploitasi: smb2
- IP pengirim: 10.7.3.100
- IP penerima: 10.7.1.50
- Folder tujuan pada sistem korban: System32
- Nama file malware: wired_trojan_payload.exe
- Flag : KOMJAR26{SMB_Tr4nsf3r_pK35VHFyu7H2OTYZBKPrcKtAD}

## Soal 19

> Eiri meneror jaringan dengan mengirimkan email pemerasan melalui protokol SMTP tanpa enkripsi. Analisis file capture wired_smtp_threat.pcap pada stream TCP terkait, identifikasi alamat email korban yang ditargetkan, password korban yang diklaim bocor oleh penyerang, jenis malware yang diinfeksikan, batas waktu (dalam hari) yang diberikan, serta MailClientID yang tercantum pada pesan.

---

### Analisis

File capture memuat beberapa sesi SMTP pada port 25. Sesi yang memuat email pemerasan diidentifikasi dari percakapan antara 185.234.72.19 (penyerang, domain darkwired.net) dan 203.0.113.100 (mail server mail.protocol7.co.jp) pada paket nomer 86. 

![soal19-malicioussmtptraffic](assets/soal19-malicioussmtptraffic.png)

![soal19-malicioussmtppacket](assets/soal19-malicioussmtppacket.png)


### Hasil yang didapatkan

- Alamat email korban: victim@protocol7.co.jp
- Password korban yang diklaim bocor: pr0tocol_7_user
- Jenis malware: ransomware 
- Batas waktu yang diberikan: 3 (hari)
- MailClientID: 7719980706
- Flag : KOMJAR26{SMTP_Ext0rt10n_1V3mzalfNgD9bn9g0uwWBCAKf}

## Soal 20

> Untuk rencana pamungkasnya, Eiri menyembunyikan komunikasi malware di balik saluran terenkripsi TLS. Namun Alice telah menyediakan file keylog untuk mendekripsi lalu lintas data tersebut. Analisis file capture wired_tls_decrypt.pcapng bersama keyslogfile.txt untuk mengidentifikasi versi protokol TLS yang dinegosiasikan, nama domain (SNI) yang diakses, alamat IP server HTTPS penyerang, User-Agent yang digunakan, serta HTTP request method dan path yang tersembunyi di dalam sesi dekripsi.

---

### Analisis

File capture memuat satu sesi TCP ke port 443 milik 93.184.216.34, seluruh payloadnya terenkripsi TLS sehingga tidak dapat dibaca langsung. Informasi yang tetap terlihat dibaca dari handshake TLS: paket ClientHello memuat Server Name Indication (SNI) `example.com` - nama domain yang diminta client (dikirim sebelum enkripsi aktif, sehingga tetap terlihat). ServerHello menjawab dengan version `0x0303` dan cipher suite `0xc02f` (TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256), versi TLS yang dinegosiasikan adalah TLS 1.2.

![soal20-tlstraffic](assets/soal20-tlstraffic.png)

![soal20-tlsclienthello](assets/soal20-tlsclienthello.png)

Isi sesi didekripsi dengan memuat keyslogfile.txt ke Wireshark (Edit -> Preferences -> Protocols -> TLS -> (Pre)-Master-Secret log filename). File tersebut berisi baris CLIENT_RANDOM yang menyimpan pre-master secret hasil SSLKEYLOGFILE, sehingga Wireshark dapat menurunkan kunci sesi dan membaca isi terenkripsinya. Setelah dekripsi, muncul packet HTTP di dalam trafficnya :

![soal20-httptraffic](assets/soal20-httptraffic.png)

### Hasil yang didapatkan 

- Versi protokol TLS yang dinegosiasikan: TLSv1.2
- Nama domain (SNI) yang diakses: example.com
- Alamat IP server HTTPS: 93.184.216.34
- User-Agent yang digunakan: curl/7.62.0
- HTTP request method dan path tersembunyi: HEAD /
- Flag : KOMJAR26{TLS_D3crypt_GN2q1316UYbJ9Irwl4LgUzngQ}
