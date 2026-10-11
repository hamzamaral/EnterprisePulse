# EnterprisePulse ERP

Modüler, çok şirketli (multi-tenant) ve kurumsal seviyede bir ERP sistemi.

| Repo | Açıklama | Teknoloji |
| --- | --- | --- |
| [`api/`](api) — `enterprise-pulse-api` | Backend (modüler monolit) | NestJS 11, Prisma, PostgreSQL, Redis, BullMQ, Socket.IO |
| [`web/`](web) — `enterprise-pulse-web` | Frontend (SPA) | React 19, Vite, TanStack Router/Query/Table, shadcn/ui, Tailwind 4 |

Bu kök klasör; yol haritası, mimari dokümanlar ve yerel geliştirme altyapısını (`docker-compose.yml`) içerir.
`api/` ve `web/` kendi git geçmişleri olan bağımsız repolardır.

## Hızlı başlangıç

Gereksinimler: Node 22 LTS, pnpm 9, Docker.

```bash
# 1) Altyapı (PostgreSQL, Redis, RustFS, Mailpit)
cp .env.example .env
docker compose up -d

# 2) Backend
cd api
cp .env.example .env
pnpm install
pnpm db:deploy
pnpm db:seed
pnpm start:dev            # http://localhost:3000/api, Swagger: http://localhost:3000/docs

# 3) Frontend
cd ../web
cp .env.example .env
pnpm install
pnpm dev                  # http://localhost:5173
```

### Tek komutla tam sistem (Docker)

Kaynak koddan imajları derleyip API + web'i birlikte çalıştırır (veritabanı ilk açılışta migrate edilir):

```bash
docker compose --profile app up -d --build
cd api && pnpm install && pnpm db:seed   # demo verisi (aynı PostgreSQL'e host üzerinden bağlanır)
# http://localhost:8080
```

### Testler

| Repo | Komut | Kapsam |
| --- | --- | --- |
| api | `pnpm test` | Birim testleri (Jest) |
| api | `pnpm test:e2e` | Gerçek veritabanıyla HTTP testleri (Supertest) |
| web | `pnpm test` | Birim/bileşen testleri (Vitest + Testing Library) |
| web | `pnpm e2e` | Tarayıcı testleri (Playwright, API çalışıyor olmalı) |

Her iki repoda GitHub Actions; lint, format, tip kontrolü, testler ve Docker imaj derlemesini çalıştırır.
Commit mesajları [Conventional Commits](https://www.conventionalcommits.org) biçimindedir (`feat(auth): ...`), Husky + commitlint ile denetlenir.

### Demo kullanıcılar

| Rol | E-posta | Şifre |
| --- | --- | --- |
| Sistem yöneticisi | `admin@enterprisepulse.dev` | `Admin123!` |
| Müdür | `manager@enterprisepulse.dev` | `Manager123!` |
| Personel | `employee@enterprisepulse.dev` | `Employee123!` |

### Yerel servisler

| Servis | Adres |
| --- | --- |
| API | http://localhost:3000/api |
| Swagger | http://localhost:3000/docs |
| Web | http://localhost:5173 |
| Mailpit (e-posta kutusu) | http://localhost:8025 |
| RustFS (S3) konsolu | http://localhost:9001 (`erpadmin` / `erpadmin123`) |

## Dokümanlar

- [Yol haritası](docs/roadmap.md)
- [Mimari](docs/architecture.md)
- [Mimari karar kayıtları (ADR)](docs/adr)

## Cursor ile çalışma

`EnterprisePulse.code-workspace` dosyasını açarak üç klasörü birlikte görebilirsiniz.
Her repo kendi Cursor kurallarını (`.cursor/rules`) ve MCP ayarlarını (`.cursor/mcp.json`) taşır;
`api/` veya `web/` ayrı açıldığında yalnızca o repoya ait kurallar ve MCP sunucuları yüklenir.

MCP sunucuları token'ları ortam değişkenlerinden okur. Gerekli değişkenler:

- `GITHUB_PERSONAL_ACCESS_TOKEN` — GitHub MCP
- `EP_DATABASE_URL` — PostgreSQL MCP (varsayılan: `postgresql://erp:erp@localhost:5432/enterprise_pulse`)
