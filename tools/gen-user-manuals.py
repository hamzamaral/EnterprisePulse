# -*- coding: utf-8 -*-
"""Generate printable user manuals for all EnterprisePulse stacks."""
from __future__ import annotations

import json
from pathlib import Path

META = Path(r"c:/github/EnterprisePulse.NET/src/EnterprisePulse.Core/Metadata/metadata.json")

DESC: dict[str, str] = {
    "": (
        "Kurumsal gösterge paneli. Oturumdaki kullanıcının yetkilerine göre KPI kartları gösterir: "
        "onay bekleyenler, okunmamış bildirimler, aktif kullanıcılar, İK (kalan izin, bugün izinde), "
        "demirbaş zimmetleri, stok ve finans özetleri. Kartlara tıklayınca ilgili liste veya self-servis "
        "sayfasına gider. Üst barda şirket/şube seçici, dil (TR/EN), tema, bildirim zili ve profil menüsü bulunur."
    ),
    "workflow/inbox": (
        "Onay kutusu. Kullanıcıya atanmış bekleyen onay adımlarını listeler (izin, zimmet, masraf vb.). "
        "Her satırda belge türü, talep sahibi ve özet görünür. Açınca belge özeti ile Onayla / Reddet "
        "(gerekçe) işlemleri yapılır. Süreç bitince belge durumu güncellenir ve bildirim gider."
    ),
    "hr/my-leave": (
        "Self-servis izin bakiyesi ve talepleri. Yıl bazında izin türü kartları (hak, kullanılan, bekleyen, kalan). "
        "Yeni talep: tür, tarih aralığı, gün hesabı, açıklama. Talepler durum etiketleriyle listelenir. "
        "Yönetici kendi bakiyesini görür; onay Onay Kutum üzerinden yürür."
    ),
    "hr/my-attendance": (
        "Mesai / giriş-çıkış self-servisi. Günlük mesai, geç kalma ve fazla mesai özeti. "
        "Personel kendi kayıtlarını görür; İK puantajda düzeltme yapabilir."
    ),
    "hr/org-chart": (
        "Organizasyon şeması. Departman ve yönetici hiyerarşisine göre personeli ağaç veya iç içe listede gösterir."
    ),
    "employees": (
        "Personel kartları listesi ve detay. Sicil, departman, pozisyon, yönetici, işe giriş, durum. "
        "Detayda izin, zimmet, ücret, eğitim, sözleşme sekmeleri (yetkiye göre)."
    ),
    "departments": "Departman tanımları. Kod, ad, üst departman, yönetici. Org şeması buradaki hiyerarşiyi kullanır.",
    "positions": "Pozisyon / unvan tanımları. Departman ilişkisi ve personel atamalarında kullanılır.",
    "leave-requests": "İK görünümü: tüm izin talepleri. Durum, tür, personel, tarih filtresi.",
    "leave-types": "İzin türü ayarları: yıllık, mazeret vb. Hak günü, taşıma, onay gereksinimi.",
    "hr/timesheet": "Aylık puantaj çizelgesi. Personel × gün: mesai, izin, resmi tatil, İK düzeltmeleri.",
    "shifts": "Vardiya tanımları ve haftalık plan. Gece vardiyası, kopyalama, personel ataması.",
    "expenses/my": "Personelin kendi masraf formları. Taslak, fiş eki, onaya gönderme, ödeme durumu.",
    "expense-reports": "Masraf formları (yönetici/finans). Onay, red, kasa/banka ödemesi, proje bağlantısı.",
    "expense-categories": "Masraf türleri: limit, fiş zorunluluğu, harcırah ve km ücreti.",
    "payroll/my": "Personelin kendi ücret pusulaları. Dönem, brüt, kesinti, net.",
    "payroll-periods": "Bordro dönemleri. Hesaplama, onay, maaş ödemesi ve geri alma.",
    "salary-records": "Ücret kayıtları ve geçmiş.",
    "payroll-parameters": "Yıllık bordro parametreleri, SGK / vergi dilimleri.",
    "recruitment/interviews": "Mülakatçıya atanmış mülakatlar. Puan, tavsiye, not.",
    "job-postings": "İş ilanları: yayınlama, bekletme, kapatma; başvuru hattına geçiş.",
    "candidates": "Aday havuzu, CV, profil.",
    "job-applications": "Başvurular ve aşama hattı. Teklif, ret, personele dönüştürme.",
    "performance/my": "Öz ve yönetici değerlendirme formları. Hedefler, yetkinlik puanları.",
    "training/my": "Kayıtlı eğitimler, zorunlu sertifikalar, geri bildirim.",
    "review-cycles": "Performans değerlendirme dönemleri: başlatma, kapatma, özet.",
    "competencies": "Yetkinlik kataloğu.",
    "training-sessions": "Eğitim oturumları: katılımcı, puan, maliyet.",
    "training-courses": "Eğitim kataloğu tanımları.",
    "training/compliance": "Zorunlu eğitim uyum matrisi (personel × kurs).",
    "support/my": "Self-servis destek: açma, yanıt, ek, çözüm onayı / yeniden açma, puan.",
    "tickets": "Destek kuyruğu: SLA, öncelik, atama, dahili not, durum geçişleri.",
    "ticket-categories": "Kategori, varsayılan sorumlu, SLA hedefleri.",
    "projects/my-tasks": "Kullanıcıya atanmış proje görevleri.",
    "projects/timesheet": "Haftalık zaman çizelgesi: projeye süre kaydı.",
    "projects": "Proje listesi ve detay: ekip, görevler, bütçe, ilerleme.",
    "assets/my": "Zimmetimdeki demirbaşlar; iade / onay bekleyenler.",
    "assets": "Demirbaş kartları: kategori, durum (zimmetli/depo/hurda/bakım), marka-model, QR.",
    "asset-assignments": "Zimmet / iade / devir kayıtları ve tutanak onayları.",
    "asset-counts": "Demirbaş sayımı ve fark raporu.",
    "asset-categories": "Demirbaş kategori ve amortisman ayarları.",
    "inventory": "Stok durumu: kalem, minimum altı, stok değeri, depo; kritik filtre.",
    "products": "Ürün ve varyantlar: SKU, barkod, lot/seri takibi, birim.",
    "stock-movements": "Stok fişleri: giriş, çıkış, transfer, düzeltme; lot/seri satırları.",
    "stock-counts": "Stok sayımı ve fark düzeltmesi.",
    "warehouses": "Depo ve stok kategori tanımları.",
    "work-orders": "Üretim iş emirleri: serbest bırakma, üretim kaydı, malzeme, kapatma.",
    "bill-of-materials": "Ürün ağacı (BOM): bileşenler, standart maliyet.",
    "production/requirements": "MRP / malzeme ihtiyacı: net ihtiyaç, talep veya iş emri.",
    "purchase-requests": "Satın alma talepleri ve onay.",
    "supplier-quotes": "Tedarikçi teklifleri ve karşılaştırma.",
    "purchase-orders": "Satın alma siparişleri: teslim / fatura miktarları.",
    "goods-receipts": "Mal kabul irsaliyeleri; stoğa giriş.",
    "purchase-invoices": "Alış faturaları; borç ve muhasebe bağlantısı.",
    "leads": "Potansiyel müşteriler; cariye / fırsata dönüştürme.",
    "opportunities": "Satış fırsatları: aşama, tutar, ağırlıklı değer, teklif bağlantısı.",
    "crm-activities": "Arama, toplantı, görev aktiviteleri; geciken / bugün.",
    "sales-quotes": "Satış teklifleri: kalemler, kabul ile siparişe dönüşüm.",
    "sales-orders": "Satış siparişleri: rezervasyon, sevk, faturalama durumu.",
    "delivery-notes": "Sevk irsaliyeleri; stok çıkışı.",
    "sales-invoices": "Satış faturaları: tahsilat durumu, e-fatura bağlantısı.",
    "sales-returns": "Satış iadeleri.",
    "business-partners": "Cari hesaplar (müşteri/tedarikçi): vade, kredi limiti, döviz, hareketler.",
    "treasury-accounts": (
        "Kasa ve banka hesapları. Kod, tür (kasa/banka), para birimi, IBAN, aktiflik. "
        "Hareketler tahsilat/ödeme/çek ile oluşur. Demo seed Pulse Teknoloji üzerindedir."
    ),
    "partner-payments": "Tahsilat ve ödemeler: yöntem, kasa/banka, fatura mahsupları.",
    "cheques": "Çek ve senet portföyü: yatırma, tahsil, ciro.",
    "finance/aging": "Alacak / borç yaşlandırma raporu.",
    "accounting": "Muhasebe paneli: kasa, alacak, borç, net kâr, aylık gelir-gider, bekleyen belgeleri muhasebeleştirme.",
    "journal-entries": "Yevmiye defteri: fiş listeleme, kesinleştirme, ters kayıt.",
    "ledger-accounts": "Tekdüzen hesap planı; alt hesap ekleme.",
    "accounting/trial-balance": "Mizan: dönem hareketleri ve bakiyeler.",
    "accounting/balance-sheet": "Bilanço raporu.",
    "accounting/income-statement": "Gelir tablosu.",
    "e-invoices": "e-Fatura kuyruğu: UBL-TR, GİB durum simülasyonu, gelen/giden.",
    "contracts": "Sözleşmeler: cari/personel, yürürlük, yenileme, fesih, ekler.",
    "contract-types": "Sözleşme türü tanımları.",
    "budgets": "Şirket / departman bütçeleri: plan vs gerçekleşen, sapma.",
    "budget-entries": "Gerçekleşen bütçe girişleri (kira, reklam vb.).",
    "budget-items": "Bütçe kalemi ve kategori eşlemesi.",
    "vehicles": "Filo araç kartları: sürücü, bakım, muayene, sigorta.",
    "vehicle-fuel-entries": "Yakıt defteri.",
    "fleet/my": "Sürücünün zimmetli araçları; yakıt ve km girişi.",
    "reports/sales": "Satış analizi raporu.",
    "reports/purchases": "Alış analizi.",
    "reports/cash-flow": "Nakit akışı.",
    "workflow-instances": "Tüm onay süreç örnekleri (yönetim).",
    "workflow-definitions": "Onay akış tanımları: adımlar, roller.",
    "companies": "Şirket (kiracı) kartları.",
    "branches": "Şube tanımları.",
    "users": "Kullanıcı hesapları ve şirket üyelikleri.",
    "roles": "Rol ve izin matrisi.",
    "audit-logs": "Denetim kaydı: kim, ne zaman, hangi alan değişti (okunabilir Geçmiş).",
    "settings": "Şirket ayarları: para birimi, kur, KDV, birim, numaralandırma, genel.",
}

STACKS = [
    {
        "name": "EnterprisePulse.NET",
        "out": Path(r"c:/github/EnterprisePulse.NET/docs/kullanici-kilavuzu.md"),
        "title": "EnterprisePulse.NET — Kullanıcı / Ekran Kılavuzu",
        "stack": "ASP.NET Core 10 API + Blazor (MudBlazor)",
        "web": "http://localhost:5101",
        "api": "http://localhost:5100",
        "note": "Liste ekranları çoğunlukla `/r/{kaynak}` rotasındadır.",
    },
    {
        "name": "EnterprisePulse.Java",
        "out": Path(r"c:/github/EnterprisePulse.Java/docs/kullanici-kilavuzu.md"),
        "title": "EnterprisePulse.Java — Kullanıcı / Ekran Kılavuzu",
        "stack": "Spring Boot 3.5 API + Vaadin 24",
        "web": "http://localhost:8181",
        "api": "http://localhost:8180",
        "note": "Liste ekranları `/r/{kaynak}` Vaadin rotalarındadır.",
    },
    {
        "name": "EnterprisePulse (NestJS / React)",
        "out": Path(r"c:/github/EnterprisePulse/docs/kullanici-kilavuzu.md"),
        "title": "EnterprisePulse — Kullanıcı / Ekran Kılavuzu",
        "stack": "NestJS 11 API + React 19 (Vite, TanStack, shadcn)",
        "web": "http://localhost:5173",
        "api": "http://localhost:3000/api",
        "note": "SPA rotaları `web/src/routes` altındadır; API `api/src/modules` içindedir.",
    },
]


def key_for(it: dict) -> str:
    page = it.get("page")
    if page is not None and page != "":
        return page
    if it.get("resource"):
        return it["resource"]
    return ""


def route_for(it: dict) -> str:
    if it.get("page") == "":
        return "/"
    if it.get("page"):
        return it["page"]
    if it.get("resource"):
        return f"r/{it['resource']}"
    return "(kök)"


def desc_for(it: dict) -> str:
    k = key_for(it)
    if k in DESC:
        return DESC[k]
    r = it.get("resource") or ""
    if r in DESC:
        return DESC[r]
    lab = it["label"]["tr"]
    return (
        f"**{lab}** ekranı. Metadata kaynaklı liste/form/detay akışı: arama, filtre, sayfalama, "
        "Yeni / düzenle, yetki kontrolü, dosya ekleri ve Geçmiş sekmeleri. Kayıtlar aktif şirkete bağlıdır."
    )


def main() -> None:
    meta = json.loads(META.read_text(encoding="utf-8"))
    for st in STACKS:
        lines: list[str] = []
        a = lines.append
        a(f"# {st['title']}")
        a("")
        a("> Bu belge tarayıcıdan veya editörden **PDF olarak yazdır** ile PDF’e dönüştürülebilir.")
        a("")
        a("## 0. Giriş")
        a("")
        a(f"- **Ürün / stack:** {st['name']} — {st['stack']}")
        a(f"- **Web:** `{st['web']}` · **API:** `{st['api']}`")
        a(
            "- **Demo:** `admin@enterprisepulse.dev` / `Admin123!`, "
            "`manager@…` / `Manager123!`, `employee@…` / `Employee123!`"
        )
        a(
            "- **Önemli:** Demo veri **Pulse Teknoloji · Genel Merkez** üzerindedir. "
            "Pulse Lojistik seçilirse çoğu liste boştur."
        )
        a(f"- {st['note']}")
        a("")
        a("Bölüm numaraları sol menü gruplarına, alt başlıklar menü öğelerine karşılık gelir "
          "(ör. **2. İnsan Kaynakları** → **2.1 İzinlerim**).")
        a("")
        a("---")
        a("")
        for i, sec in enumerate(meta["navigation"], 1):
            a(f"## {i}. {sec['label']['tr']}")
            a("")
            a(
                f"Menüdeki **{sec['label']['tr']}** grubu. Ekranlar yetkiye göre görünür veya gizlenir."
            )
            a("")
            for j, it in enumerate(sec.get("items") or [], 1):
                lab = it["label"]["tr"]
                a(f"### {i}.{j} {lab}")
                a("")
                a(f"- **Rota / kaynak:** `{route_for(it)}`")
                if it.get("resource"):
                    a(f"- **Metadata resource:** `{it['resource']}`")
                perms = it.get("permission") or []
                if perms:
                    a(f"- **İzinler:** {', '.join(f'`{p}`' for p in perms)}")
                a("")
                a(desc_for(it))
                a("")
                a("**Nasıl kullanılır:**")
                a("1. Menüden ilgili öğeyi açın.")
                a("2. Liste ise Ara / filtre ile kaydı bulun; **Yeni** veya satır detayı.")
                a("3. Formu kaydedin; onaylı belgeler **Onay Kutum**’a düşer.")
                a("4. Detayda **Geçmiş**, **Dosyalar** ve durum aksiyonlarını kullanın.")
                a("")
            a("---")
            a("")
        a("## Ek A. Ortak kalıplar")
        a("")
        a("- **Liste:** arama, rozetler, sayfalama, + Yeni")
        a("- **Form/detay:** doğrulama, ilişkili seçiciler, durum butonları")
        a("- **Onay:** çok adımlı workflow, red gerekçesi, bildirim")
        a("- **Çok şirket:** üst bar şirket/şube seçici → `companyId` bağlamı")
        a("")
        a("## Ek B. İlgili belgeler")
        a("")
        a("- Teknik kılavuz: [`teknik-kilavuz.md`](teknik-kilavuz.md)")
        a("- Kısa başlangıç: kök `README.md`")
        a("")
        st["out"].parent.mkdir(parents=True, exist_ok=True)
        st["out"].write_text("\n".join(lines), encoding="utf-8")
        print("Wrote", st["out"], "chars", st["out"].stat().st_size)


if __name__ == "__main__":
    main()
