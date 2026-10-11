# Yol Haritası

Her faz kendi içinde veritabanı, API, arayüz ve testlerle tamamlanır.

## Faz 1 — Altyapı

- [x] Kök repo, dokümanlar, `docker-compose.yml`
- [x] `api/` NestJS iskeleti (config, common, infrastructure, health, Swagger, Pino)
- [x] `web/` React iskeleti (router, query, shadcn, Tailwind, i18n, Orval)
- [x] Cursor kuralları ve MCP ayarları (her repo için ayrı)
- [x] ESLint, Prettier, Husky, commitlint, Dockerfile, GitHub Actions

## Faz 2 — Platform çekirdeği

- [x] Kimlik doğrulama: JWT + rotasyonlu refresh token, şifre sıfırlama, TOTP 2FA
- [x] Çoklu şirket ve şube (tenant bağlamı)
- [x] Kullanıcılar, roller, izinler (`module:action`, CASL)
- [x] Denetim kaydı (audit log)
- [x] Bildirimler (veritabanı + Socket.IO + e-posta kuyruğu)
- [x] Dosya yönetimi (S3 uyumlu depolama: RustFS)
- [x] Belge numaralandırma serileri
- [x] Ayarlar: para birimi, döviz kuru, KDV, birimler
- [x] Onay akışı (workflow) motoru
- [x] Frontend: giriş, yerleşim, tema, dil, yetkili menü, DataTable, yönetim sayfaları

## Faz 3 — İnsan Kaynakları

- [x] Departman (hiyerarşik) ve pozisyon tanımları
- [x] Personel kartı: kişisel, istihdam ve iletişim bilgileri; sistem kullanıcısına bağlama; işten çıkış
- [x] Organizasyon şeması (yönetici ilişkisinden)
- [x] İzin türleri, yıllık bakiyeler (kıdeme göre hak ediş), resmi tatiller
- [x] İzin talebi: iş günü hesabı, çakışma ve bakiye kontrolü, workflow ile çok adımlı onay, iptal
- [x] Self-servis: "İzinlerim" ekranı, bakiye kartları
- [ ] Puantaj (devam takibi)
- [ ] Vardiya planlama

## Faz 4 — Zimmet ve Demirbaş

- [x] Demirbaş kategorileri (varsayılan faydalı ömür) ve depolama konumları (şubeye bağlı)
- [x] Demirbaş kartı: otomatik demirbaş no, seri no, marka/model, fiziksel durum, satın alma ve garanti
- [x] QR etiket (demirbaş sayfasına bağlantı, PNG indirme)
- [x] Personele / departmana / konuma zimmet, iade (durum ve konumla) ve tek adımda devir
- [x] Zimmet tutanağı: yazdırılabilir / PDF, personelin elektronik onayı, bildirim
- [x] Bakım ve onarım kaydı (bakımdayken zimmetlenemez), kullanım dışı bırakma (hurda / kayıp)
- [x] Doğrusal amortisman: aylık tutar, birikmiş amortisman, net defter değeri, yıllık tablo
- [x] İşten çıkış kontrolü: üzerinde zimmet bulunan personelin çıkışı engellenir
- [x] Self-servis: "Zimmetlerim" ekranı
- [ ] Envanter sayımı (QR ile sayım oturumu, fark raporu)

## Faz 5 — Stok ve Depo

- [x] Ürün kategorileri (hiyerarşik), depolar (şubeye bağlı)
- [x] Ürün kartı: stoklu ürün / hizmet, birim, KDV, alış-satış fiyatı, minimum stok, barkod
- [x] Varyantlar (renk, beden vb. nitelikler); her ürünün en az bir varyantı vardır
- [x] Stok hareketleri: giriş, çıkış, depolar arası transfer, düzeltme; işlendiği anda kesinleşir
- [x] Satır kilidi ile eşzamanlı güvenli bakiye, eksi stok engeli, hareketli ağırlıklı ortalama maliyet
- [x] Lot takibi (son kullanma tarihi, FEFO sıralı lot listesi) ve seri numarası takibi
- [x] Stok kartı (hareket defteri, bakiye), depo bazında stok, stok değeri, Excel'e aktarma
- [x] Stok sayımı: depo bakiyesinin anlık görüntüsü, sayılan miktar, farklar için otomatik düzeltme fişi
- [x] Minimum stok uyarısı: kritik seviyenin altına inişte stok yöneticilerine bildirim
- [ ] Rezervasyon (satış siparişine ayrılan stok)
- [ ] Barkod okutarak sayım

## Faz 6 — Satın Alma

Talep, tedarikçi teklifi, teklif karşılaştırma, sipariş, mal kabul, onay akışı.

## Faz 7 — Satış

Teklif, sipariş, irsaliye, fatura, iade.

## Faz 8 — Cari ve Finans

Cari hesaplar, tahsilat / ödeme, kasa ve banka, çek / senet, yaşlandırma raporu.

## Faz 9 — Dashboard ve Raporlama

KPI kartları, grafikler, filtrelenebilir raporlar, Excel / PDF dışa aktarma.

## Faz 10+ — Genişletme

CRM, bordro, masraf ve harcırah, işe alım, performans ve eğitim, proje yönetimi, destek / ticket,
sözleşme yönetimi, bütçe, araç ve filo, muhasebe, e-Fatura simülasyonu, üretim (MRP).

## Son — Canlı demo

Backend: Render veya Railway. Frontend: Vercel.
