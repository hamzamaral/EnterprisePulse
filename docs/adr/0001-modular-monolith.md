# ADR 0001 — Modüler monolit

- Durum: Kabul edildi
- Tarih: 2026-10-11

## Bağlam

ERP çok sayıda iş alanından (İK, zimmet, stok, satın alma, finans...) oluşur. Mikroservisler bağımsız
ölçekleme sağlar ama dağıtık işlem, ağ hataları, çoklu veritabanı ve operasyon yükü getirir.

## Karar

Tek bir NestJS uygulaması içinde, sınırları net modüllerden oluşan bir **modüler monolit** kullanılacak.
Modüller arası iletişim dışa açılan servisler ve domain event'leri ile yapılacak.

## Sonuçlar

- Tek deploy, tek veritabanı işlemi (transaction) ile tutarlılık kolay.
- Modül sınırları korunursa ileride bir modül ayrı servise taşınabilir.
- Sınırların korunması kod incelemesi ve Cursor kuralları ile denetlenir.
