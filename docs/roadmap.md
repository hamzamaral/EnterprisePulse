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

Varlık kartı (seri no, QR kod, garanti), personele / departmana / lokasyona zimmet, iade ve devir,
imzalı PDF tutanak, bakım ve arıza kaydı, amortisman, envanter sayımı, işten ayrılış iade kontrol listesi.

## Faz 5 — Stok ve Depo

Ürün kartı, varyant, çoklu depo, stok hareketleri, transfer, sayım, minimum stok uyarısı, lot / seri takibi.

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
