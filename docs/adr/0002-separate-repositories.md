# ADR 0002 — Backend ve frontend için ayrı repolar

- Durum: Kabul edildi
- Tarih: 2026-10-11

## Bağlam

Backend ve frontend farklı yaşam döngülerine, CI süreçlerine ve deploy hedeflerine sahip.

## Karar

`enterprise-pulse-api` ve `enterprise-pulse-web` ayrı GitHub repoları olacak. Sözleşme (contract)
backend'in OpenAPI şemasıdır; frontend tipleri bu şemadan Orval ile üretilir.

## Sonuçlar

- Her repo kendi Cursor kuralları ve MCP ayarlarına sahip olur.
- API değişikliği frontend'de `pnpm api:generate` ile yansıtılır; tip uyumsuzluğu derleme hatası verir.
