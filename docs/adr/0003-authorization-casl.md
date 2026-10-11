# ADR 0003 — İzin tabanlı yetkilendirme (CASL)

- Durum: Kabul edildi
- Tarih: 2026-10-11

## Bağlam

Sabit rol kontrolleri (`if role === 'admin'`) büyüyen bir ERP'de yönetilemez hale gelir.

## Karar

İzinler `module:action` formatında veritabanında tutulur ve rollere atanır. Roller şirket bazında
kullanıcılara verilir. Çalışma anında kullanıcının izinlerinden bir CASL `Ability` üretilir.

## Sonuçlar

- Yeni rol tanımlamak kod değişikliği gerektirmez.
- Frontend aynı izin listesini kullanarak menü ve butonları gizler.
