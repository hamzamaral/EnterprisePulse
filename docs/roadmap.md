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
- [x] Vardiya tanımları (gece vardiyası dahil) ve haftalık vardiya planı; önceki haftayı kopyalama
- [x] Puantaj: self-servis giriş-çıkış ("Mesaim"), vardiya planı + izin + resmi tatilden aylık
      çizelge; geç kalma, devamsızlık, fazla mesai; İK düzeltmesi, Excel'e aktarma

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
- [x] Envanter sayımı: kapsamlı sayım oturumu, QR / demirbaş no / seri no ile okutma (kamera
      desteği), beklenmeyen demirbaş, durum güncelleme, yazdırılabilir fark raporu

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
- [x] Barkod / SKU okutarak sayım
- [x] Rezervasyon: onaylı satış siparişine ayrılan stok; kullanılabilir miktar = eldeki − rezerve

## Faz 6 — Satın Alma

- [x] Cari hesaplar (müşteri / tedarikçi): vade, kredi limiti, döviz; cari hareket defteri ve bakiye
- [x] Ortak ticari belge altyapısı: kalem, iskonto, KDV kırılımı, döviz kuru ve yerel para karşılığı
- [x] Satın alma talebi: personel self-servis, workflow ile onay, talep edene bildirim
- [x] Tedarikçi teklifleri ve karşılaştırma tablosu (kalem bazında en iyi net fiyat, en ucuz tam teklif)
- [x] Teklifi siparişe dönüştürme; diğer açık teklifler otomatik reddedilir
- [x] Satın alma siparişi: taslak düzenleme, onay, iptal; teslim alınan ve faturalanan miktarların takibi
- [x] Mal kabul: kısmi teslim, lot / son kullanma ve seri numarasıyla stoğa giriş (sipariş maliyetinden)
- [x] Alış faturası: üç yönlü eşleştirme (sipariş, teslim alınan, faturalanan), mükerrer fatura no
      kontrolü, vade hesabı, cari hesaba alacak kaydı, iptalde ters kayıt

## Faz 7 — Satış

- [x] Satış teklifi: geçerlilik süresi, süresi dolan teklifin işaretlenmesi, reddetme, siparişe dönüştürme
- [x] Satış siparişi: taslak düzenleme, onayda kredi limiti kontrolü (bakiye + açık siparişler), iptal
- [x] Stok rezervasyonu: onayda kullanılabilir stoktan ayırma, sonradan tamamlama, sevkte düşme;
      başka siparişe ayrılmış stok çıkış fişleriyle kullanılamaz
- [x] Sevk irsaliyesi: kısmi sevk, depodan lot / seri numarası seçimi, sevk adresi, yazdırılabilir irsaliye
- [x] Satış faturası: sevk edilen miktar kadar faturalama (hizmetler siparişsiz), vade, cari hesaba borç,
      iptalde ters kayıt
- [x] Satış iadesi: fatura kalemine bağlı kısmi iade, lot / seri ile stoğa geri giriş (ortalama maliyetten),
      cari hesaba alacak ve faturanın ödeme durumuna mahsup

## Faz 8 — Cari ve Finans

- [x] Cari hesaplar: müşteri / tedarikçi kartı, değişmez cari hareket defteri, yürüyen bakiyeli ekstre
- [x] Kasa ve banka hesapları: döviz bazında bakiye, açılış bakiyesi, hesap hareketleri; kasa eksiye düşmez
- [x] Tahsilat (TAH) ve ödeme (ODM): nakit, banka, çek, senet; kur ile yerel tutar
- [x] Faturalara kapama: otomatik (en eski vadeden) veya seçmeli; fatura kısmen ödendi / ödendi olur,
      iptalde kapamalar çözülür ve ters kayıt atılır
- [x] Çek / senet (CEK / SNT): portföy, bankaya verme, tahsil, tedarikçiye ciro, karşılıksız (tahsilat
      iptal edilir); kendi çekimizin vadesinde ödenmesi; her adım hareket geçmişine yazılır
- [x] Raporlar: yaşlandırma (0-30 / 31-60 / 61-90 / 90+ gün), nakit pozisyonu; Excel'e aktarma
- [x] Gösterge paneli: alacaklar, borçlar, vadesi geçenler, nakit pozisyonu, açık siparişler

## Faz 9 — Dashboard ve Raporlama

- [x] Gösterge paneli: yetkiye göre İK, zimmet ve stok KPI'ları, kritik stok listesi, self-servis
      kartları (kalan izin, zimmetlerim)
- [x] Grafikler: gösterge panelinde son 6 ayın satış / alış ve nakit akışı grafikleri (recharts)
- [x] Satış ve alış analizi: aylık, cari veya ürün bazında; şirket para biriminde, satış iadeleri düşülmüş;
      ilk 10 grafiği; dönem, cari ve gruplama filtreleri URL'de
- [x] Nakit akışı: hesap seçimi, dönem başı / sonu bakiye, aylık giriş / çıkış, belge türü kırılımı;
      dönem içinde iptal edilen kayıtlar ayıklanır
- [x] Tüm listelerde ve raporlarda Excel / PDF dışa aktarma (Türkçe karakterli PDF, sayfa numaraları)
- [x] Fatura detayından tek tıkla "Tahsilat al" / "Ödeme yap" (cari, tutar ve kapama hazır gelir)

## Faz 10 — CRM

- [x] Potansiyel müşteri (aday): kaynak, durum (yeni, görüşüldü, nitelikli, elendi, dönüştürüldü),
      tahmini değer, sorumlu; elenme nedeni ve yeniden açma
- [x] Adayı dönüştürme: yeni veya mevcut müşteri cariye bağlama, isteğe bağlı satış fırsatı açma,
      adayın aktivitelerini cariye taşıma
- [x] Satış fırsatı hattı: aşamalar (aday, nitelendirme, teklif, pazarlık, kazanıldı, kaybedildi),
      aşamaya göre varsayılan olasılık, ağırlıklı tutar, beklenen kapanış ve gecikme, kayıp nedeni
- [x] Sürükle-bırak pano ve liste görünümü; döviz cinsinden fırsatlar şirket para birimine çevrilir
- [x] Teklif entegrasyonu: fırsattan teklif hazırlama, teklif fırsatı "Teklif" aşamasına taşır,
      teklifin siparişe dönüşmesi fırsatı kazandırır
- [x] Aktiviteler: arama, toplantı, e-posta, görev, not; aday / fırsat / cari zaman çizelgesi,
      geciken ve bugünkü işler, sorumluya bildirim
- [x] Göstergeler: açık hat, ağırlıklı tutar, bu ay kazanılan, kazanma oranı (son 90 gün),
      gösterge panelinde CRM kartları, cari kartında fırsatlar ve aktiviteler

## Faz 11+ — Genişletme

Bordro, masraf ve harcırah, işe alım, performans ve eğitim, proje yönetimi, destek / ticket,
sözleşme yönetimi, bütçe, araç ve filo, muhasebe, e-Fatura simülasyonu, üretim (MRP).

## Son — Canlı demo

Backend: Render veya Railway. Frontend: Vercel.
