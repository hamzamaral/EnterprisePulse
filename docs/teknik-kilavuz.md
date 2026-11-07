# EnterprisePulse — Teknik Kılavuz (NestJS / React)

Bu kılavuz, `c:\github\EnterprisePulse` kökündeki NestJS API (`api/`) ve React SPA (`web/`) için modül sınırlarını, HTTP sözleşmesini, veri modelini ve ekran karşılıklarını anlatır. Yollar depodaki gerçek dosyalara göredir. `api/` ve `web/` kendi git geçmişleri olan bağımsız repolardır; kök klasör docker altyapısını, yol haritasını ve bu dokümanı tutar.

## 0. Giriş

EnterprisePulse, tek PostgreSQL veritabanı üzerinde çalışan çok şirketli bir ERP’dir. Backend bir **modüler monolittir**: her iş alanı `api/src/modules/<modül>` altında kendi controller, servis ve DTO’suyla yaşar. Modüller birbirinin Prisma modellerine doğrudan yazmaz. Konuşma, modülün `exports` listesindeki servisler veya `@nestjs/event-emitter` olayları üzerinden olur. Kararın kaydı `docs/adr/0001-modular-monolith.md` içindedir.

Kiracı sınırı `companyId` kolonudur. Kullanıcı bir veya daha fazla şirkete `UserCompany` ile bağlanır. İstek, `Authorization: Bearer` access token’ı ve isteğe bağlı `x-company-id` / `x-branch-id` başlıklarıyla gelir. Aktif şirket ve şube `AsyncLocalStorage` tabanlı `RequestContext` ile katmanlara taşınır (`api/src/common/context/request-context.ts`).

Tipik istek yaşam döngüsü:

1. `RequestContextMiddleware` istek kimliği (`x-request-id`), IP ve user-agent yazar.
2. `ThrottlerGuard` dakikada 300 istek sınırını uygular (`AppModule`).
3. `JwtAuthGuard` Bearer token’ı doğrular. `@Public()` ile işaretli uçlar (giriş, yenileme, sağlık) bu adımdan geçer.
4. `JwtStrategy.validate` `AuthContextService.resolve` çağırır; kullanıcı, şirket, şube ve izin kodları Redis’te 60 saniye önbelleğe alınır (`auth:ctx:{userId}:{companyId}:{branchId}`).
5. `PermissionsGuard`, `@RequirePermissions` (hepsi) ve `@RequireAnyPermission` (en az biri) dekoratörlerini CASL ability ile kontrol eder.
6. Controller ince kalır; iş kuralı servistedir. DTO’lar `class-validator` ile doğrulanır.
7. Prisma yazmaları `auditExtension` tek kayıt `create` / `update` / `delete` için `audit_logs` satırı üretir.
8. Liste uçları `{ data, meta }` döner. `meta` alanları `page`, `pageSize`, `total`, `totalPages` şeklindedir (`api/src/common/pagination/paginate.ts`).

Hata gövdesi `AllExceptionsFilter` ile tekleştirilir: `statusCode`, `error`, `message`, `details`, `path`, `timestamp`, `requestId`. Prisma tekillik ihlalleri ve doğrulama hataları aynı şekle indirilir. Pino, `authorization` ve `cookie` başlıklarını logdan çıkarır; her satıra `requestId`, `userId`, `companyId` ekler.

Demo şirket **Pulse Teknoloji** (`PULSE`, şubeler `MERKEZ` / `ANK` / `IZM`) ve ikinci kiracı **Pulse Lojistik** (`PULSE-LOJ`) seed ile gelir. Kullanıcılar:

| Rol | E-posta | Şifre | Not |
| --- | --- | --- | --- |
| Süper yönetici | `admin@enterprisepulse.dev` | `Admin123!` | `isSuperAdmin`, her iki şirkete `admin` rolü |
| Müdür | `manager@enterprisepulse.dev` | `Manager123!` | Okuma ve seçili onay izinleri |
| Personel | `employee@enterprisepulse.dev` | `Employee123!` | Self-servis; dosya ve workflow başlatma |

Geliştirme adresleri: API `http://localhost:3000/api/v1`, Swagger `http://localhost:3000/docs`, web `http://localhost:5173`. Docker profili `app` ile web nginx `http://localhost:8080` üzerinden yayınlanır.

## 1. Backend stack

| Parça | Sürüm / seçim | Nerede |
| --- | --- | --- |
| Çalışma zamanı | Node.js `>= 22`, pnpm `9.15.9` | `api/package.json` `engines` |
| HTTP çerçevesi | NestJS 11 (`@nestjs/common`, `platform-express`) | `api/src/main.ts`, `app.module.ts`, `app.setup.ts` |
| Doğrulama | `class-validator` + `class-transformer`, global `ValidationPipe` (`whitelist`, `forbidNonWhitelisted`, `transform`) | `configureApp` |
| ORM | Prisma 6, çok dosyalı şema | `api/prisma/schema/*.prisma`, `api/prisma.config.ts` |
| Veritabanı | PostgreSQL 17 | `docker-compose.yml` servisi `postgres`, port `5432`, kullanıcı/parola/db varsayılanı `erp` / `erp` / `enterprise_pulse` |
| Önbellek ve kilit | Redis 7 + `ioredis` | port `6379`, `api/src/infrastructure/redis` |
| Kuyruk | BullMQ 5 + `@nestjs/bullmq` | `api/src/infrastructure/queue/queue.module.ts` |
| Gerçek zaman | Socket.IO 4, namespace `/ws` | `notifications.gateway.ts` |
| Kimlik | JWT access + httpOnly refresh çerezi, argon2, otplib TOTP | `auth` modülü |
| Yetki | CASL `@casl/ability` 6, kod biçimi `module:action` | `permissions.registry.ts`, `ability.factory.ts` |
| API sözleşmesi | `@nestjs/swagger` 11 | `api/src/swagger.ts`, geliştirmede `openapi.json` |
| Log | `nestjs-pino` | `AppModule` |
| E-posta | nodemailer → Mailpit SMTP `1025`, arayüz `8025` | `infrastructure/mail` |
| Nesne depolama | AWS SDK v3, S3 uyumlu RustFS | API portu `9000`, konsol `9001`, anahtar `erpadmin` / `erpadmin123`, kova `enterprise-pulse` |
| Güvenlik başlıkları | `helmet`, CORS `credentials: true`, `trust proxy` | `configureApp` |
| Yapılandırma | Zod `envSchema` | `api/src/config/env.ts`, `api/.env.example` |

HTTP yüzeyi `app.setGlobalPrefix('api')` ve URI sürümlemesi (`VersioningType.URI`, varsayılan `1`) ile oluşur. Controller `{ path: 'employees', version: '1' }` tanımı `GET /api/v1/employees` adresine denk gelir. Swagger UI `/docs`, ham belge `/docs-json` altındadır. Geliştirmede `main.ts` belgeyi `api/openapi.json` dosyasına yazar; üretimde bu yazım kapalıdır. `operationIdFactory` controller adını ve metot adını birleştirir (`usersFindAll` gibi), Orval bu kimliklerden kanca adı üretir.

Ortam değişkenleri (özet):

- `PORT` varsayılan `3000`, `LOG_LEVEL`, `NODE_ENV`.
- `CORS_ORIGINS` virgülle ayrılır, varsayılan `http://localhost:5173`. `WEB_APP_URL` şifre sıfırlama bağlantılarında kullanılır.
- `DATABASE_URL`, `REDIS_URL`.
- `JWT_ACCESS_SECRET` en az 32 karakter, `JWT_ACCESS_TTL_SECONDS` varsayılan `900` (15 dakika), `JWT_REFRESH_TTL_DAYS` varsayılan `7`.
- `S3_ENDPOINT`, `S3_REGION` (`us-east-1`), `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_BUCKET`.
- `MAIL_HOST`, `MAIL_PORT`, `MAIL_FROM`.

Docker Compose servisleri (`docker-compose.yml`):

| Servis | İmaj | Host portu | Rol |
| --- | --- | --- | --- |
| `postgres` | `postgres:17-alpine` | `5432` | Tek veritabanı |
| `redis` | `redis:7-alpine` | `6379` | Oturum bağlamı önbelleği ve BullMQ |
| `storage` | `rustfs/rustfs` | `9000` / `9001` | S3 API ve konsol |
| `mailpit` | `axllent/mailpit` | `1025` / `8025` | SMTP ve gelen kutusu |
| `api` | `./api` Dockerfile, profil `app` | içeride `3000` (host’a yayınlanmaz) | Üretim imajı |
| `web` | `./web` Dockerfile + nginx, profil `app` | `8080` → konteyner `80` | `API_UPSTREAM=http://api:3000` |

Altyapı: `docker compose up -d`. Tam yığın: `docker compose --profile app up -d --build`. API konteyneri veritabanı ilk açılışta migrate bekler; demo verisi host üzerinden `cd api && pnpm db:seed` ile yüklenir.

BullMQ kuyruk adları `QUEUES` sabitindedir. Varsayılan iş seçenekleri: 3 deneme, üstel geri çekilme (2 saniye), tamamlanan 1000 ve başarısız 5000 kayıt tutulur. Zamanlanmış işler `Europe/Istanbul` saat dilimindedir ve `NODE_ENV=test` iken kaydedilmez; e2e testleri aynı işi HTTP `POST .../run` veya `.../sync` ile tetikler.

| Kuyruk | İş | Cron | İşleyen |
| --- | --- | --- | --- |
| `mail` | E-posta gönderimi | olay anında | `infrastructure/mail/mail.processor.ts` |
| `contracts` | Yenileme, süre dolumu, hatırlatma | `0 7 * * *` | `contracts.processor.ts` |
| `budgets` | Bütçe aşım uyarısı | `30 7 * * *` | `budgets.processor.ts` |
| `fleet` | Belge ve bakım hatırlatması | `15 7 * * *` | `fleet.processor.ts` |
| `accounting` | Bekleyen belgelerin yevmiyeye alınması | `30 2 * * *` | `accounting.processor.ts` |
| `einvoice` | Simüle entegratör | her dakika `* * * * *`, ayrıca gönderim sonrası iş | `einvoice.processor.ts` |

Şema kuralları `api/prisma/schema/base.prisma` başlığında yazılıdır: UUID birincil anahtar, `@@map` ile snake_case tablo adları, yumuşak silme için `deletedAt`. İstemci `prisma generate` ile üretilir; migrate yolu `api/prisma/migrations`.

## 2. Frontend stack

| Parça | Sürüm / seçim | Nerede |
| --- | --- | --- |
| UI | React 19 | `web/package.json` |
| Derleme | Vite 8, `@vitejs/plugin-react`, `@` → `web/src` | `web/vite.config.ts` |
| Yönlendirme | TanStack Router, dosya tabanlı rotalar, `autoCodeSplitting` | `web/src/routes`, `web/src/app/router.tsx` |
| Sunucu durumu | TanStack Query 5 | `web/src/app/query-client.ts`, Orval kancaları |
| Tablolar | TanStack Table 8 | `web/src/shared/components/data-table` |
| Form | react-hook-form + Zod (`@hookform/resolvers`) | özellik diyalogları |
| Bileşenler | shadcn/ui (`web/components.json`), Radix, `web/src/shared/ui` | |
| Stil | Tailwind CSS 4 (`@tailwindcss/vite`), `tailwind-merge`, `class-variance-authority` | |
| Dil | i18next + react-i18next, `tr` ve `en`, varsayılan `tr` | `web/src/i18n` |
| Oturum | Zustand 5, kalıcı olan yalnızca `companyId` ve `branchId` (`ep-auth`) | `web/src/features/auth/auth.store.ts` |
| HTTP | axios, `withCredentials: true` | `web/src/api/http.ts` |
| İstemci üretimi | Orval 8, react-query + axios mutator | `web/orval.config.ts` |
| Grafik | recharts | `web/src/features/reports` |
| Dışa aktarma | `write-excel-file`, pdfmake | `data-table/export-excel.ts`, `export-pdf.ts` |
| Bildirim | sonner + socket.io-client | `use-notification-socket.ts` |
| Tema | next-themes, `class` özniteliği, sistem varsayılanı | `web/src/app/providers.tsx` |
| Test | Vitest + Testing Library; Playwright | `pnpm test`, `pnpm e2e` |

Geliştirme sunucusu port `5173`. `VITE_API_URL` boşken istekler aynı kökene gider; Vite `/api` ve `/socket.io` yolunu `VITE_API_PROXY_TARGET` (varsayılan `http://localhost:3000`) adresine proxyler. Böylece refresh çerezi ve WebSocket CORS ayarı gerektirmez. Ayrı host’ta `VITE_API_URL` ve `VITE_WS_URL` API kökenine set edilir (`web/.env.example`).

`http` interceptor’ı her istekte `Authorization`, `x-company-id`, `x-branch-id` ve `Accept-Language` yazar. 401 yanıtında (auth uçları hariç) tek bir `POST /api/v1/auth/refresh` paylaşılır; yeni access token ile istek bir kez yinelenir, yenileme başarısızsa oturum temizlenir. Access token bellektedir; localStorage’a yazılmaz.

Rotalar `web/src/routes` altındaki dosya ağacıdır. Kimlik sayfaları `login.tsx`, `forgot-password.tsx`, `reset-password.tsx`. Oturumlu kabuk `routes/_app.tsx` ve `app/layout/app-layout.tsx` içindedir. Menü `web/src/app/layout/navigation.ts` içindeki `NAVIGATION` dizisidir; her öğe bir `permission` (tek kod veya “herhangi biri”) taşıyabilir. `features/auth/can.tsx` aynı kodlarla düğmeleri gizler. Şirket değiştirici `company-switcher.tsx`, dil ve tema `preferences-menu.tsx` altındadır.

Sunucu verisi Query önbelleğindedir. İstemci durumu oturum, şirket ve tema ile sınırlıdır. API tipleri elle yazılmaz; `pnpm api:generate` OpenAPI’den `web/src/api/generated/endpoints` ve `web/src/api/generated/model` üretir.

## 3. Repo yapısı

### 3.1 `api/src`

```
api/src/main.ts                 bootstrap, swagger dosyası, listen(PORT)
api/src/app.module.ts           modül sırası, global guard ve filter
api/src/app.setup.ts            prefix, sürüm, pipe, helmet, cors, cookie
api/src/swagger.ts              OpenAPI başlığı ve global başlıklar
api/src/config/                 Zod env, AppConfigService
api/src/common/
  auth/                         AuthUser, AbilityFactory, has-permission
  context/                      RequestContext + middleware
  dates/date-only.ts            takvim günü (saat dilimi kayması olmadan)
  decorators/                   Public, CurrentUser, RequirePermissions, RequireAnyPermission
  filters/all-exceptions.filter.ts
  guards/                       JwtAuthGuard, PermissionsGuard
  money/document-totals.ts      satır, iskonto, KDV, kur, yerel tutar
  pagination/                   page, pageSize (1–100, varsayılan 20), sort allow-list
api/src/infrastructure/
  prisma/                       createPrismaClient + auditExtension
  redis/                        REDIS token
  queue/                        QUEUES
  storage/                      S3 upload, presigned GET
  mail/                         kuyruğa e-posta
api/src/modules/<modül>/        *.module.ts, *.controller.ts, *.service.ts, dto/
```

`AppModule` içe aktarma sırası platform çekirdeğini (audit, auth, organizations, users, roles, notifications, files, numbering, settings, workflow) iş modüllerinin önüne koyar. Prisma istemcisi genişletilmiş tiptir: servisler `PrismaService` enjekte eder ve `PrismaTx` ile `prisma.$transaction` kullanır. Numara ayırma çoğu zaman aynı transaction içine `NumberingService.next(companyId, code, tx)` olarak girer; `SELECT … FOR UPDATE` aynı numarayı iki isteğe vermez.

### 3.2 `web/src`

```
web/src/main.tsx, index.html
web/src/app/                    providers, router, query-client, layout
web/src/routes/                 TanStack dosya rotaları (__root, _app, login)
web/src/features/<alan>/        sayfa, diyalog, tablo, yerel yardımcı
web/src/api/http.ts             axios örneği ve Orval mutator `apiClient`
web/src/api/generated/          Orval çıktısı (elle düzenlenmez)
web/src/shared/ui/              shadcn bileşenleri
web/src/shared/components/      PageHeader, DataTable, ConfirmDialog, kamera okuyucu
web/src/shared/lib/             format, query anahtar yardımcıları, validation
web/src/i18n/locales/tr.json    ve en.json
```

Özellik klasörü iş kuralını yeniden hesaplamaz; sunucunun döndürdüğü durum ve tutarları gösterir. Ticari belgelerde ortak satır editörü `web/src/features/trade` altındadır (`document-lines-editor.tsx`, `document-math.ts`, `document-print.tsx`). Bu klasörün backend karşılığı tek modül değildir; purchasing, sales ve partners aynı toplam motorunu (`document-totals.ts`) kullanır.

### 3.3 Prisma dosyaları

Her iş alanı bir `*.prisma` dosyasıdır (`api/prisma/schema/`):

| Dosya | Modeller (özet) |
| --- | --- |
| `identity.prisma` | User, UserCompany, Role, Permission, RolePermission, UserRole, RefreshToken, PasswordResetToken |
| `organization.prisma` | Company, Branch |
| `platform.prisma` | AuditLog, Notification, FileObject, NumberSequence |
| `settings.prisma` | Currency, ExchangeRate, TaxRate, Unit, Setting |
| `workflow.prisma` | WorkflowDefinition, WorkflowStep, WorkflowInstance, WorkflowAction |
| `hr.prisma` | Department, Position, Employee, LeaveType, LeaveBalance, LeaveRequest, Holiday |
| `attendance.prisma` | Shift, ShiftAssignment, AttendanceRecord |
| `assets.prisma` | Asset, AssetAssignment, AssetMaintenance, AssetCount, … |
| `inventory.prisma` | Product, ProductVariant, Warehouse, StockBalance, StockLot, SerialNumber, StockMovement, StockCount, … |
| `partners.prisma` | BusinessPartner, PartnerLedgerEntry |
| `purchasing.prisma` | PurchaseRequest, SupplierQuote, PurchaseOrder, GoodsReceipt, PurchaseInvoice ve satırları |
| `sales.prisma` | SalesQuote, SalesOrder, StockReservation, DeliveryNote, SalesInvoice, SalesReturn ve satırları |
| `finance.prisma` | TreasuryAccount, TreasuryTransaction, PartnerPayment, PaymentAllocation, Cheque, ChequeEvent |
| `crm.prisma` | Lead, Opportunity, CrmActivity |
| `expenses.prisma` | ExpenseCategory, ExpenseReport, ExpenseLine |
| `projects.prisma` | Project, ProjectMember, ProjectTask, TimeEntry |
| `payroll.prisma` | SalaryRecord, PayrollParameter, PayrollPeriod, Payslip, PayslipItem |
| `recruitment.prisma` | JobPosting, Candidate, JobApplication, Interview, JobOffer, … |
| `performance.prisma` | Competency, ReviewCycle, PerformanceReview, PerformanceGoal, CompetencyRating |
| `training.prisma` | TrainingCourse, TrainingSession, TrainingEnrollment |
| `support.prisma` | Ticket, TicketCategory, TicketSlaPolicy, TicketComment, TicketEvent |
| `contracts.prisma` | ContractType, Contract, ContractEvent |
| `budgets.prisma` | BudgetItem, Budget, BudgetLine, BudgetEntry, BudgetEvent, BudgetAlert |
| `fleet.prisma` | Vehicle ve zimmet, km, yakıt, servis, belge |
| `accounting.prisma` | LedgerAccount, JournalEntry, JournalLine |
| `einvoice.prisma` | EInvoice, EInvoiceEvent |
| `production.prisma` | BillOfMaterials, BomLine, WorkOrder, WorkOrderComponent, ProductionRecord |

## 4. Platform çekirdeği

Bu bölüm auth, tenant, izin, denetim, bildirim, numaralandırma, dosya ve onay akışının ortak sözleşmesidir. Modül dosyalarının ayrıntısı sonraki bölümlerdedir.

### 4.1 Kimlik doğrulama

`api/src/modules/auth`. Uçlar `AuthController` (`/api/v1/auth`):

| Metot | Yol | Erişim |
| --- | --- | --- |
| POST | `/login` | public, gövde `LoginDto` (email, password, opsiyonel `otp`) |
| POST | `/refresh` | public, çerez `ep_refresh` |
| POST | `/logout` | public (çerezi siler) |
| GET | `/me` | Bearer, `MeResponseDto` (kullanıcı, şirketler, izinler) |
| POST | `/forgot-password` | public |
| POST | `/reset-password` | public |
| POST | `/change-password` | Bearer |
| POST | `/2fa/setup`, `/2fa/enable`, `/2fa/disable` | Bearer |

Şifre argon2 ile saklanır. Beş başarısız deneme hesabı 15 dakika kilitler (`MAX_FAILED_LOGINS`, `LOCK_MINUTES`). TOTP açıksa ilk yanıt `{ requiresTwoFactor: true }` döner; ikinci istek `otp` taşır. Access token gövdededir. Refresh token ham hali yalnızca `ep_refresh` httpOnly çerezinde durur; veritabanında SHA-256 özeti `RefreshToken` satırındadır. Yenileme token’ı döndürür. Çalınmış (iptal edilmiş) bir token tüm aileyi iptal eder. Aynı tarayıcı sekmeleri 10 saniyelik `ROTATION_GRACE_MS` penceresinde yeni dönmüş token’ı hâlâ kullanabilir. Şifre sıfırlama token’ı 60 dakika yaşar ve e-posta kuyruğuna gider. Başarılı giriş `AuditService.record` ile `LOGIN` eylemi yazar (Prisma extension giriş satırını görmez, çünkü şifre alanı yazımı gürültülü ve hassastır).

`AuthListener`, `USER_EVENTS.INVITED` olayında davet e-postası gönderir (`users.events.ts`).

Web: `web/src/features/auth` (`login-page.tsx`, `password-reset-pages.tsx`, `session.ts`, `use-session.ts`, `can.tsx`) ve rotalar `web/src/routes/login.tsx`, `forgot-password.tsx`, `reset-password.tsx`. Profil `web/src/features/profile/profile-page.tsx`, rota `/profile`.

### 4.2 Çoklu şirket ve şube

`api/src/modules/organizations`.

- `CompaniesController` → `/api/v1/companies`. İzinler `companies:read|create|update|delete`.
- `BranchesController` → `/api/v1/branches`. İzinler `branches:*`.
- Servisler `companies.service.ts`, `branches.service.ts`. DTO `dto/company.dto.ts`, `dto/branch.dto.ts`.
- Şema: `organization.prisma`.

`AuthContextService.load` sırası: istenen `x-company-id` kullanıcının `UserCompany` kaydında olmalı; başlık yoksa `isDefault` üyelik, o da yoksa ilk üyelik. Süper yönetici üyelik olmasa da şirketi açabilir. `x-branch-id` aktif şirkete ait değilse 403. Üyelikte `defaultBranchId` yedek şubedir. Rol ataması şirket bazındadır (`UserRole.companyId`).

Önbellek, rol veya üyelik değişince `invalidateUser`, rol izinleri değişince `invalidateAll` ile silinir. Bu çağrılar users ve roles servislerinden yapılır; aksi halde menü 60 saniye eski izinle kalır.

Web: `web/src/features/organization/companies-page.tsx`, `branches-page.tsx`. Rotalar `/companies`, `/branches`. Üst çubuk `company-switcher.tsx` şirket değiştirince `useAuthStore.setCompany` yazar ve Query önbelleği yeni başlıkla yeniden dolar.

### 4.3 İzinler (CASL)

Tek kaynak `api/src/modules/roles/permissions.registry.ts` içindeki `PERMISSION_REGISTRY`. Seed bu listeyi `permissions` tablosuna upsert eder. Kod `module:action` biçimindedir. `manage` eylem adı kullanılmaz; CASL’de `manage` jokerdir ve süper yöneticiye `can('manage', 'all')` olarak ayrıca verilir (`ability.factory.ts`).

Guard iki kümeyi ayırır:

- `@RequirePermissions('a', 'b')` kullanıcının **ikisinden** de geçmesini ister.
- `@RequireAnyPermission('workflow:start', 'purchasing:create')` birinin yetmesi demektir. Üretim MRP’sinin satın alma talebi bu kalıbı kullanır.

Self-servis uçların bir kısmında izin dekoratörü yoktur (örnek: kendi izin talebi, kendi bordrosu, kendi destek talebi). Bu, “giriş yapmış herkes kendi kaydını görür” kuralıdır; servis `employee.userId === currentUser` filtresini kendisi uygular. Başkasının kaydına geçmek ilgili `read` veya `create` iznini gerektirir.

Web menüsü aynı kodları okur. Yeni modül eklenince hem registry’ye eylem eklenir hem `navigation.ts` öğesine `permission` yazılır hem seed roller güncellenir. `admin` rolü `ALL_PERMISSION_CODES` alır ve `isSystem` işaretlidir. `manager` ve `employee` kod listeleri `api/prisma/seed.ts` içindeki `ROLE_PERMISSIONS` nesnesindedir.

### 4.4 Denetim (Prisma extension)

`api/src/infrastructure/prisma/audit.extension.ts`. Genişletilmiş istemci her tekil `create`, `update`, `delete` sonrası taban (genişletilmemiş) istemciyle `auditLog.create` çağırır; böylece denetim kaydı kendini denetlemez.

Atlanan modeller: `AuditLog`, `Notification`, `RefreshToken`, `PasswordResetToken`, `NumberSequence`, stok defter satırları (`StockBalance`, `LotBalance`, `StockTransaction`, `StockMovementLine`, `StockMovementSerial`, `StockCountLine`) ve `JournalLine`. Denetlenen belge üst kayıttır (hareket fişi, yevmiye fişi). `passwordHash`, `twoFactorSecret`, `tokenHash` değerleri `[REDACTED]` olur. `update` yalnızca değişen alanları yazar; `updatedAt` fark sayılmaz. Yazım hatası iş kuralını düşürmez, loglanır.

Okuma ucu `AuditController` `GET /api/v1/audit-logs`, izin `audit:read`. DTO `dto/audit-log.dto.ts`. Web: `web/src/features/audit/audit-logs-page.tsx`, rota `/audit-logs`.

### 4.5 Bildirimler

`NotificationsService` satır yazar ve `NotificationsGateway.emitToUser` ile `user:{userId}` odasına `notification` olayı yollar. İstemci `/ws` namespace’ine `auth: { token }` ile bağlanır (`use-notification-socket.ts`). Gelen olay sonner toast açar ve `notificationsFindMine` ile okunmamış sayaç sorgularını geçersiz kılar.

HTTP (`/api/v1/notifications`): kullanıcının kendi listesi, okundu işaretleme, okunmamış sayı. Başkasına bildirim göndermek `notifications:send` iznini kullanır. E-posta gereken akışlar (sözleşme, filo, bütçe, davet, şifre) `MailService` ile `mail` kuyruğuna iş koyar; SMTP Mailpit veya gerçek sunucudur.

Web: `notification-bell.tsx`, `notifications-page.tsx`, rota `/notifications`.

### 4.6 Numaralandırma

`NumberingService.next` şirket ve `code` için `number_sequences` satırını kilitler, yılı `resetYearly` ise çevirir, `nextValue` artırır ve `formatNumber` uygular (`number-format.ts`):

- `includeYear: true` → `ÖNEK-YIL-000042` (padding varsayılan 6)
- `includeYear: false` → `ÖNEK-000042`

e-Fatura serileri padding 9 kullanır (`EPF`, `EPA`). HTTP `/api/v1/number-sequences` liste, oluşturma ve güncelleme sunar; izinler `numbering:read` ve `numbering:update`. DTO `dto/number-sequence.dto.ts`.

Seed ile gelen seriler (`api/prisma/seed.ts` ve ilgili seed dosyaları):

| Kod | Önek | Belge |
| --- | --- | --- |
| `PURCHASE_REQUEST` | STA | Satın alma talebi |
| `PURCHASE_ORDER` | SAS | Satın alma siparişi |
| `SUPPLIER_QUOTE` | TKL | Tedarikçi teklifi |
| `GOODS_RECEIPT` | MKB | Mal kabul |
| `PURCHASE_INVOICE` | ALF | Alış faturası |
| `SALES_QUOTE` | STK | Satış teklifi |
| `SALES_ORDER` | SPS | Satış siparişi |
| `DELIVERY_NOTE` | IRS | İrsaliye |
| `SALES_INVOICE` | FTR | Satış faturası |
| `SALES_RETURN` | IAD | Satış iadesi |
| `COLLECTION` | TAH | Tahsilat |
| `PAYMENT` | ODM | Ödeme |
| `CHEQUE` | CEK | Çek |
| `PROMISSORY_NOTE` | SNT | Senet |
| `ASSET` | DMB | Demirbaş |
| `ASSET_ASSIGNMENT` | ZMT | Zimmet tutanağı |
| `ASSET_COUNT` | DSY | Demirbaş sayımı |
| `STOCK_MOVEMENT` | STH | Stok hareketi |
| `STOCK_COUNT` | SAY | Stok sayımı |
| `LEAVE_REQUEST` | IZN | İzin talebi |
| `EMPLOYEE` | PRS | Sicil (yıllık değil) |
| `PARTNER` | CAR | Cari (yıllık değil) |
| `LEAD` | ADY | Aday müşteri |
| `OPPORTUNITY` | FRS | Fırsat |
| `EXPENSE_REPORT` | MSF | Masraf formu |
| `PROJECT` | PRJ | Proje |
| `PAYROLL` | BRD | Bordro |
| `JOB_POSTING` | ILN | İş ilanı |
| `TICKET` | TKT | Destek talebi |
| `CONTRACT` | SZL | Sözleşme |
| `JOURNAL_ENTRY` | YEV | Yevmiye |
| `E_INVOICE` | EPF | e-Fatura (9 hane) |
| `E_ARCHIVE` | EPA | e-Arşiv (9 hane) |
| `WORK_ORDER` | ISE | İş emri |
| `PRODUCTION` | URT | Üretim fişi |

### 4.7 Dosyalar ve S3

`FilesService.upload` MIME beyaz listesi uygular (png, jpeg, webp, gif, pdf, düz metin, csv, zip, doc, docx, xls, xlsx). Üst sınır `MAX_FILE_SIZE` = 20 MB. Anahtar `{companyId}/{yıl}/{ay}/{uuid}{uzantı}` biçimindedir. `FileObject` şirkete, yükleyene ve isteğe bağlı `entityType` + `entityId` bağlantısına sahiptir. İndirme adresi 300 saniye imzalıdır.

Uç `/api/v1/files`. İzinler `files:read|create|delete`. Masraf fişi, sözleşme eki, destek eki, aday CV’si ve benzeri akışlar bu servisi veya aynı `StorageService`’i kullanır; bazı modüller kendi ek uçlarını da açar (örnek `POST /contracts/:id/attachments`).

### 4.8 Onay akışı (workflow)

`workflow.prisma`. Tanım `WorkflowDefinition` (şirket + `code` tekil) ve sıralı `WorkflowStep` (onaylayan `ApproverType`: rol veya kullanıcı). Belge `entityType` + `entityId` ile `WorkflowInstance` başlatır. Her karar `WorkflowAction` olur.

Olaylar (`workflow.events.ts`):

- `workflow.approved`
- `workflow.rejected`
- `workflow.cancelled`

Yükü `WorkflowFinishedEvent`: `instanceId`, `companyId`, `definitionCode`, `entityType`, `entityId`, `actorId`.

Dinleyenler ve tanım kodları:

| Kod | Başlatan | Dinleyen |
| --- | --- | --- |
| `LEAVE_REQUEST` | `leave-requests.service.ts` | `hr/leave.listener.ts` |
| `PURCHASE_REQUEST` | `purchase-requests.service.ts` | `purchasing/purchasing.listener.ts` |
| `EXPENSE_REPORT` | `expense-reports.service.ts` | `expenses/expenses.listener.ts` |

HTTP:

- `/api/v1/workflow/definitions` — `workflow:read|create|update`
- `/api/v1/workflow/instances` — liste `workflow:read`, `inbox` (izin gerekmez, kendi bekleyenleri), `POST` `workflow:start`, `approve` / `reject` / `cancel`

Web: `web/src/features/workflow` (`definitions-page.tsx`, `inbox-page.tsx`, `instances-page.tsx`, `instance-detail-page.tsx`). Rotalar `/workflow/definitions`, `/workflow/inbox`, `/workflow/instances`, `/workflow/instances/$id`. Gelen kutusu menüde genel grubun içindedir ve izin istemez; servis yalnızca kullanıcının rolüne veya kendisine düşen adımları döner.

### 4.9 Ayarlar (platform verisi)

`settings` modülü para birimi, kur, KDV ve birim tanımlarını tutar. Ayrıntı bölüm 30’dadır. Ticari belgeler kuru belge tarihindeki `ExchangeRate` kaydından alır; yerel tutar `document-totals.ts` ile hesaplanır. Şirket ayarı `Setting` satırında JSON’dur (`key`: `general`, `einvoice`, muhasebe kilidi vb.).

### 4.10 Sağlık

`HealthController` `@Public()` `GET /api/v1/health`. Terminus, `SELECT 1` ve `PING` ile `database` ve `redis` durumunu döner. Pino bu yolu otomatik loglamaz.

## 5. Auth modülü (dosya haritası)

Önceki bölüm sözleşmeyi anlattı. Dosyalar:

- `api/src/modules/auth/auth.module.ts`
- `auth.controller.ts`, `auth.service.ts`, `auth-context.service.ts`, `jwt.strategy.ts`, `auth.listener.ts`
- `dto/auth.dto.ts`

Web özelliği `web/src/features/auth`. Oturum açıldıktan sonra `GET /auth/me` izin listesini doldurur; menü ve `Can` bu listeye bakar. Şirket değişimi yeni access token üretmez; aynı token ile başlık değişir ve `AuthContextService` başka bir Redis anahtarı okur.

## 6. İnsan kaynakları (`hr`)

Modül `api/src/modules/hr`. `hr.module.ts` `WorkflowModule` ve `AssetsModule` içe aktarır (izin onayı ve işten çıkışta zimmet kontrolü). Dışa `EmployeesService` ve `AttendanceService` açılır; bordro, işe alım ve üretim bu servisleri kullanır.

Controller ve servis:

| Controller | Yol | Servis | DTO |
| --- | --- | --- | --- |
| `DepartmentsController` | `/departments` | `departments.service.ts` | `dto/organization.dto.ts` |
| `PositionsController` | `/positions` | `positions.service.ts` | aynı |
| `EmployeesController` | `/employees` | `employees.service.ts` | `dto/employee.dto.ts` |
| `LeaveTypesController` | `/leave-types` | `leave-settings.service.ts` | `dto/leave.dto.ts` |
| `HolidaysController` | `/holidays` | aynı | aynı |
| `LeaveBalancesController` | `/leave-balances` | aynı | aynı |
| `LeaveRequestsController` | `/leave-requests` | `leave-requests.service.ts` | aynı |
| `ShiftsController` | `/shifts` | `attendance.service.ts` | `dto/attendance.dto.ts` |
| `ShiftPlanController` | `/shift-plan` | aynı | aynı |
| `AttendanceController` | `/attendance` | aynı | aynı |

Personel kartı kişisel, iletişim ve istihdam alanlarını tutar; `userId` ile sistem kullanıcısına bağlanır. Sicil `EMPLOYEE` serisinden `PRS-000001` biçimindedir (yıl yok). Hiyerarşi `managerId` ve departman `parentId` ile kurulur. `GET /employees/org-chart` ve `GET /employees/me` self-servis uçlarıdır. `POST /employees/:id/terminate` işten çıkış yapar. Üzerinde açık zimmet varsa `AssetsModule` çıkışı reddeder.

İzin türleri kodla tekildir (`YILLIK`, `MAZERET`, `HASTALIK`, `UCRETSIZ`). Yıllık bakiye kıdeme göredir: 1–4 yıl 14, 5–14 yıl 20, 15+ yıl 26 gün (`seed.ts` `annualLeaveDays`, İş Kanunu md. 53 ile aynı tablo). İş günü hesabı `working-days.ts` (hafta sonu ve `Holiday`). Talep çakışma ve bakiye kontrolünden geçer, `LEAVE_REQUEST` akışını başlatır (seed’de 1. adım müdür rolü, 2. adım şirket yöneticisi). İptal ve ret `leave.listener.ts` bakiyeyi geri yazar. Ücretsiz izin bakiyesizdir ve bordro eksik gününe girer.

Vardiya geceyi kesebilir. Haftalık plan önceki haftadan kopyalanır. Puantaj self-servis giriş-çıkış, plan, izin ve resmi tatili birleştirir (`timesheet.ts`): geç kalma, devamsızlık, fazla mesai. İK düzeltmesi `attendance:update` ister. Kaynak `AttendanceSource` enum’udur.

İzin kodları: `departments:*`, `positions:*`, `employees:*`, `leave:read|create|update` (`create` başkası adına talep), `attendance:read|update`.

Web özelliği `web/src/features/hr`. Sayfalar: `employees-page.tsx`, `employee-detail-page.tsx`, `employee-form-dialog.tsx`, `departments-page.tsx`, `positions-page.tsx`, `org-chart-page.tsx`, `leave-requests-page.tsx`, `leave-settings-page.tsx`, `my-leave-page.tsx`, `shift-planning-page.tsx`, `timesheet-page.tsx`, `my-attendance-page.tsx`. Rotalar `web/src/routes/_app/hr/` altında: `/hr/employees`, `/hr/employees/$id`, `/hr/departments`, `/hr/positions`, `/hr/org-chart`, `/hr/leave-requests`, `/hr/leave-settings`, `/hr/my-leave`, `/hr/shifts`, `/hr/timesheet`, `/hr/my-attendance`.

## 7. Demirbaş ve zimmet (`assets`)

Dosyalar `api/src/modules/assets`: `assets.controller.ts` (beş controller), `assets.service.ts`, `asset-assignments.service.ts`, `asset-counts.service.ts`, `asset-settings.service.ts`, `asset-mappers.ts`, `depreciation.ts`, `dto/asset.dto.ts`, `dto/asset-count.dto.ts`.

| Controller | Yol |
| --- | --- |
| `AssetCategoriesController` | `/asset-categories` |
| `AssetLocationsController` | `/asset-locations` |
| `AssetsController` | `/assets` |
| `AssetCountsController` | `/asset-counts` |
| `AssetAssignmentsController` | `/asset-assignments` |

Demirbaş no `ASSET` → `DMB-YIL-######`. Kart seri no, marka, model, kategori (varsayılan faydalı ömür), konum (şubeye bağlı), fiziksel durum, satın alma ve garanti tutar. Durumlar `AssetStatus` / `AssetCondition`. QR, demirbaş sayfasına giden PNG’dir (`qrcode` paketi).

Zimmet `POST /assets/:id/assign` personele, departmana veya konuma gider (`assets:assign`). İade `return`, tek adımda devir `transfer`. Tutanak no `ASSET_ASSIGNMENT` (`ZMT-…`). Personel elektronik onay `POST /asset-assignments/:id/acknowledge` ile verilir; bildirim gider. Bakım kaydı açıkken zimmet yasaktır. Tamamlama `POST /assets/:id/maintenances/:maintenanceId/complete`. Hurda veya kayıp `POST /assets/:id/retire`.

Doğrusal amortisman `depreciation.ts` içindedir: aylık tutar, birikmiş amortisman, net defter değeri, yıllık tablo. Birim test `depreciation.spec.ts`.

Sayım `assets:count`. Oturum kapsamı açılır, `POST /asset-counts/:id/scan` demirbaş no, seri no veya QR ile satır işler. Beklenmeyen demirbaş ve durum güncellemesi satırdadır. `complete` farkları kapatır, `cancel` oturumu düşürür. Numara `ASSET_COUNT` (`DSY-…`).

`GET /asset-assignments/mine` izin dekoratörü olmadan kullanıcının kendi zimmetlerini döner.

Web `web/src/features/assets`: `assets-page.tsx`, `asset-detail-page.tsx`, `asset-form-dialog.tsx`, `asset-settings-page.tsx`, `asset-maintenance.tsx`, `assignments-page.tsx`, `assignment-document-page.tsx`, `my-assets-page.tsx`, `asset-counts-page.tsx`, `asset-count-detail-page.tsx`. Rotalar `/assets`, `/assets/$id`, `/assets/settings`, `/assets/assignments`, `/assets/assignments/$id`, `/assets/my`, `/assets/counts`, `/assets/counts/$id`. Kamera `web/src/shared/components/camera-scanner.tsx`.

## 8. Stok ve depo (`inventory`)

`api/src/modules/inventory`. Controller tek dosyada altı sınıftır (`inventory.controller.ts`). Servisler: `products.service.ts`, `inventory-settings.service.ts`, `stock.service.ts`, `stock-movements.service.ts`, `stock-counts.service.ts`, saf hesap `stock-math.ts` (`stock-math.spec.ts`). DTO `dto/catalog.dto.ts`, `dto/stock.dto.ts`.

| Controller | Yol |
| --- | --- |
| `ProductCategoriesController` | `/product-categories` |
| `WarehousesController` | `/warehouses` |
| `ProductsController` | `/products` ve `/:id/variants` |
| `StockController` | `/stock/items`, `/levels`, `/summary`, `/lots`, `/serials`, `/ledger` |
| `StockMovementsController` | `/stock-movements` |
| `StockCountsController` | `/stock-counts` |

Ürün `ProductType` stoklu veya hizmettir. Hizmet stok hareketi üretmez ve satış faturasında siparişsiz kesilebilir. Her ürünün en az bir `ProductVariant` kaydı vardır (renk, beden). Kategori ağaçtır. Depo şubeye bağlanır. Barkod ve SKU varyanttadır. KDV `TaxRate`, birim `Unit`.

Hareket türleri `StockMovementType`: giriş, çıkış, depolar arası transfer, düzeltme. Fiş işlendiği anda kesindir; numara `STOCK_MOVEMENT` (`STH-…`). Bakiye satır kilidiyle güncellenir, eksi stok reddedilir. Maliyet hareketli ağırlıklı ortalamadır (`stock-math.ts`). `TrackingType` none, lot veya seri olabilir. Lot’ta son kullanma tarihi vardır; çıkış FEFO sırasıdır. Seri `SerialStatus` ile tekil izlenir. Başka siparişe ayrılmış miktar serbest çıkışta kullanılamaz; kullanılabilir = eldeki − `StockReservation`.

Sayım `STOCK_COUNT` (`SAY-…`), izin `inventory:count`. Oturum depo bakiyesinin anlık görüntüsünü alır. Satır yama `PATCH /stock-counts/:id/lines`, barkodla ek satır `POST /:id/lines`. `complete` farklar için otomatik düzeltme fişi keser. Minimum stok eşiğinin altına inen varyant stok yöneticilerine bildirim yollar.

İzinler: `inventory:read|create|update|delete|move|count`. `move` fiş keser; kart düzenlemek `update` ister.

Web `web/src/features/inventory`: ürün listesi ve kart, hareket listesi ve formu, bakiye, sayım. Rotalar `/inventory`, `/inventory/products`, `/inventory/products/$id`, `/inventory/movements`, `/inventory/movements/new`, `/inventory/movements/$id`, `/inventory/counts`, `/inventory/counts/$id`, `/inventory/settings`.

## 9. Satın alma (`purchasing`)

`api/src/modules/purchasing`. Controller `purchasing.controller.ts`. Servisler: `purchase-requests.service.ts`, `supplier-quotes.service.ts`, `purchase-orders.service.ts`, `goods-receipts.service.ts`, `purchase-invoices.service.ts`. Dinleyici `purchasing.listener.ts`. DTO `dto/purchasing.dto.ts`. Modül `WorkflowModule`, stok ve cari servislerine bağlanır.

| Controller | Yol | Kritik izin |
| --- | --- | --- |
| `PurchaseRequestsController` | `/purchase-requests` | okuma `purchasing:read`; oluşturma self-servis veya `purchasing:create` |
| `SupplierQuotesController` | `/supplier-quotes` | `purchasing:create` / `update` |
| `PurchaseOrdersController` | `/purchase-orders` | onay `purchasing:approve` |
| `GoodsReceiptsController` | `/goods-receipts` | `purchasing:receive` |
| `PurchaseInvoicesController` | `/purchase-invoices` | `purchasing:create`, iptal `purchasing:update` |

Akış:

1. Personel talep açar (`STA-…`). `PURCHASE_REQUEST` workflow’u onaylar, reddeder veya iptal eder. Talep edene bildirim gider.
2. Tedarikçi teklifleri (`TKL-…`) kalem bazında karşılaştırılır: en iyi net fiyat ve en ucuz tam teklif. Kabul, teklifi siparişe (`SAS-…`) çevirir; aynı talebin diğer açık teklifleri reddedilir.
3. Sipariş taslakken düzenlenir, onaylanır veya iptal edilir. Satırlarda teslim alınan ve faturalanan miktar izlenir.
4. Mal kabul (`MKB-…`) kısmi olabilir. Lot, son kullanma ve seri ile stoğa **sipariş maliyetinden** giriş yapılır.
5. Alış faturası (`ALF-…`) üç yönlü eşleşir: sipariş, teslim, fatura. Aynı tedarikçide mükerrer fatura numarası reddedilir. Vade, belge tarihi + cari vade günüdür. Cari deftere alacak (bizim borcumuz) yazılır. İptal ters kayıt üretir ve stok/cari etkisini geri alır. Durumlar `InvoiceStatus` ve `PaymentStatus`.

Web `web/src/features/purchasing`: `requests-page.tsx`, `request-form-page.tsx`, `request-detail-page.tsx`, `quotes-page.tsx`, `quote-form-page.tsx`, `quote-detail-page.tsx`, `accept-quote-dialog.tsx`, `orders-page.tsx`, `order-form-page.tsx`, `order-detail-page.tsx`, `receipts-page.tsx`, `receipt-form-page.tsx`, `receipt-detail-page.tsx`, `invoices-page.tsx`, `invoice-form-page.tsx`, `invoice-detail-page.tsx`. Rotalar `/purchasing/requests`, `/orders`, `/quotes`, `/receipts`, `/invoices` ve `$id` / `new` / `edit.$id` varyantları. Satır editörü `features/trade`.

## 10. Satış (`sales`)

`api/src/modules/sales`. Controller `sales.controller.ts`. Servisler: `sales-quotes.service.ts`, `sales-orders.service.ts`, `delivery-notes.service.ts`, `sales-invoices.service.ts`, `sales-returns.service.ts`. Olay `sales.events.ts`: `sales.invoice.created` (`SalesInvoiceCreatedEvent`). DTO `dto/sales.dto.ts`.

| Controller | Yol | İzin |
| --- | --- | --- |
| `SalesQuotesController` | `/sales-quotes` | `sales:read|create`, ret `sales:update`, dönüşüm `sales:create` |
| `SalesOrdersController` | `/sales-orders` | onay `sales:approve`, iptal `sales:update`, ek rezerv `POST :id/reserve` |
| `DeliveryNotesController` | `/delivery-notes` | `sales:deliver` |
| `SalesInvoicesController` | `/sales-invoices` | `sales:invoice` (kesme ve iptal) |
| `SalesReturnsController` | `/sales-returns` | `sales:deliver` |

Teklif (`STK-…`) geçerlilik tarihi taşır; süresi dolan teklif işaretlenir, reddedilebilir veya siparişe (`SPS-…`) döner. Sipariş onayında cari kredi limiti kontrol edilir: bakiye + açık siparişler limite sığmalıdır. Onay, kullanılabilir stoktan `StockReservation` ayırır. Sevk (`IRS-…`) kısmi olabilir; depodan lot ve seri seçilir, sevk adresi yazılır, rezerv düşer. Fatura (`FTR-…`) sevk edilmiş miktar kadar kesilir. Hizmet satırları siparişsiz faturalanabilir. Cariye borç yazılır. İptal ters kayıt üretir. Satış iadesi (`IAD-…`) fatura kalemine bağlı ve kısmi olabilir; lot/seri ile stok **ortalama maliyetten** geri girer, cariye alacak yazılır ve faturanın ödeme durumuna mahsup edilir.

Fatura olayı e-Fatura modülüne gider (`einvoice.listener.ts`). Ayar `autoSend` ise zarf kuyruğa alınır.

Web `web/src/features/sales`. Rotalar `/sales/quotes`, `/sales/orders`, `/sales/deliveries`, `/sales/invoices`, `/sales/returns` ve form/detay sayfaları. Fatura detayından “Tahsilat al” finans formuna cari, tutar ve kapama ile döner.

## 11. Cari hesaplar (`partners`)

`api/src/modules/partners`. `PartnersController` `/api/v1/partners`: liste, kart, `GET :id/statement`, oluşturma, yama, silme. Servisler `partners.service.ts` (kart) ve `partner-ledger.service.ts` (defter). Ortak ticari hesap `trade.service.ts` ve `dto/trade.dto.ts` (satır, iskonto, KDV kırılımı, kur, yerel para). DTO `dto/partner.dto.ts`. Şema `partners.prisma`: `PartnerType` müşteri / tedarikçi / her ikisi, `LedgerDocumentType`.

Cari no `PARTNER` → `CAR-######` (yıllık reset yok). Kart vade günü, kredi limiti ve döviz taşır. Defter satırı değiştirilemez; bakiye yürüyen toplamdır. Ekstre `statement` ucundan gelir. Satın alma, satış, tahsilat ve ödeme modülleri deftere `PartnerLedgerService` ile yazar; iptal yeni satırla ters kayıt atar, eski satırı silmez.

İzin `partners:read|create|update|delete`. Cari arama kutuları satın alma, satış ve finans izinleriyle de açılır (registry yorumu).

Web `web/src/features/partners`: `partners-page.tsx`, `partner-detail-page.tsx`, `partner-form-dialog.tsx`, `partner-statement.tsx`. Rotalar `/partners`, `/partners/$id`. CRM fırsatları ve sözleşmeler kartın içine gömülür (`crm/partner-opportunities.tsx`, `contracts/party-contracts.tsx`).

## 12. Finans (`finance`)

`api/src/modules/finance`. Controller `finance.controller.ts`. Servisler: `treasury.service.ts`, `payments.service.ts`, `cheques.service.ts`, `finance-reports.service.ts`, `finance-math.ts` (`finance-math.spec.ts`). DTO `dto/finance.dto.ts`.

| Controller | Yol |
| --- | --- |
| `TreasuryAccountsController` | `/treasury-accounts` |
| `PaymentsController` | `/payments` |
| `ChequesController` | `/cheques` |
| `FinanceReportsController` | `/finance-reports` |

Kasa ve banka `TreasuryAccountType` ile ayrılır. Bakiye döviz bazındadır; açılış bakiyesi bir hareket olarak girer. Kasa eksiye düşmez. Tahsilat `COLLECTION` (`TAH-…`), ödeme `PAYMENT` (`ODM-…`). Yöntemler `PaymentMethod`: nakit, banka, çek, senet. Kur, yerel tutarı üretir. Belge durumları `PaymentRecordStatus`.

Fatura kapama `PaymentAllocation` ile olur: otomatik (en eski vade) veya seçmeli. Fatura kısmen ödendi veya ödendi olur. Tahsilat/ödeme iptali (`finance:approve`) kapamaları çözer ve ters kasa hareketi atar.

Çek ve senet `CHEQUE` / `PROMISSORY_NOTE` (`CEK` / `SNT`). Yön `ChequeDirection`, tür `ChequeKind`, durum `ChequeStatus`: portföy, bankaya verme, tahsil, tedarikçiye ciro, karşılıksız. Karşılıksız çek tahsilatı iptal eder. Kendi çekimiz vadesinde ödenir. Her adım `ChequeEvent` geçmişine yazılır.

Raporlar: yaşlandırma kovaları 0–30 / 31–60 / 61–90 / 90+ gün ve nakit pozisyonu. Excel/PDF DataTable dışa aktarmasıyla alınır. Gösterge paneli alacak, borç, vadesi geçen, nakit ve açık siparişi `finance:read` ile gösterir.

İzinler `finance:read|create|update|approve`. `create` tahsilat, ödeme ve çek açar; `approve` iptal eder.

Web `web/src/features/finance`: `accounts-page.tsx`, `account-detail-page.tsx`, `payments-page.tsx`, `payment-form-page.tsx`, `payment-detail-page.tsx`, `cheques-page.tsx`, `cheque-detail-page.tsx`, `aging-page.tsx`. Rotalar `/finance/accounts`, `/finance/collections`, `/finance/payments`, `/finance/cheques`, `/finance/aging`.

## 13. Raporlar (`reports`)

`api/src/modules/reports`. `ReportsController` `/api/v1/reports`:

- `GET /sales` → `sales:read`, `trade-reports.service.ts`
- `GET /purchases` → `purchasing:read`
- `GET /cash-flow` → `finance:read`, `cash-flow.service.ts`

Satış ve alış analizi aylık, cari veya ürün kırılımındadır; tutarlar şirket para birimindedir, satış iadeleri düşülür. Nakit akışı dönem başı ve sonu bakiye, aylık giriş/çıkış ve belge türü kırılımı verir; dönem içinde iptal edilen kayıtlar ayıklanır. Saf yardımcılar `report-math.ts`.

Web `web/src/features/reports`: `sales` ve `purchases` sayfaları, `cash-flow-page.tsx`, `dashboard-charts.tsx` (son 6 ay, recharts), `date-ranges.ts`. Rotalar `/reports/sales`, `/reports/purchases`, `/reports/cash-flow`. Gösterge paneli `web/src/features/dashboard/dashboard-page.tsx`, rota `/` (`routes/_app/index.tsx`). KPI’lar izne göre İK, zimmet, stok, CRM, masraf ve proje kartlarını seçer.

## 14. CRM (`crm`)

`api/src/modules/crm`. Controller `crm.controller.ts`. Servisler: `leads.service.ts`, `opportunities.service.ts`, `crm-activities.service.ts`, `crm-summary.service.ts`, `crm-support.service.ts`, `crm-math.ts`. DTO `dto/crm.dto.ts`.

| Controller | Yol |
| --- | --- |
| `CrmController` | `/crm/summary`, `/crm/members` |
| `LeadsController` | `/leads` |
| `OpportunitiesController` | `/opportunities`, `/opportunities/board` |
| `CrmActivitiesController` | `/crm-activities` |

Aday (`LEAD` / `ADY-…`) kaynak `LeadSource` ve durum `LeadStatus`: yeni, görüşüldü, nitelikli, elendi, dönüştürüldü. Elenme nedeni zorunlu olabilir; `reopen` adayı geri alır. `POST /leads/:id/convert` yeni veya mevcut cari açar, isteğe bağlı fırsat yaratır, aktiviteleri cariye taşır.

Fırsat (`OPPORTUNITY` / `FRS-…`) aşamaları `OpportunityStage`: aday, nitelendirme, teklif, pazarlık, kazanıldı, kaybedildi. Aşama varsayılan olasılığı belirler; ağırlıklı tutar olasılık × tutardır ve şirket para birimine çevrilir. `POST :id/stage` pano sürüklemesini karşılar. `win` / `lose` kapanış nedeni ister. Satış teklifi fırsattan üretilebilir; teklif aşamayı “teklif”e, siparişe dönüş teklifi fırsatı kazanılmışa taşır.

Aktivite türleri `CrmActivityType`: arama, toplantı, e-posta, görev, not. Geciken ve bugünkü işler sorumluya bildirim yollar. Özet: açık hat, ağırlıklı tutar, bu ay kazanılan, son 90 gün kazanma oranı.

İzin `crm:read|create|update|delete`. `update` aşama ve dönüşümü de kapsar.

Web `web/src/features/crm`: `leads-page.tsx`, `lead-detail-page.tsx`, `lead-form-dialog.tsx`, `convert-lead-dialog.tsx`, `opportunities-page.tsx`, `opportunity-detail-page.tsx`, `pipeline-board.tsx`, `activities-page.tsx`, `activity-timeline.tsx`. Rotalar `/crm/leads`, `/crm/leads/$id`, `/crm/opportunities`, `/crm/opportunities/$id`, `/crm/activities`.

## 15. Masraf ve harcırah (`expenses`)

`api/src/modules/expenses`. Controller `expenses.controller.ts`: `ExpenseCategoriesController` `/expense-categories`, `ExpenseReportsController` `/expense-reports`. Servisler `expense-categories.service.ts`, `expense-reports.service.ts`, `expense-math.ts`. Dinleyici `expenses.listener.ts`. DTO `dto/expense.dto.ts`.

Kategori `ExpenseCategoryKind`: fişli masraf, günlük harcırah, km ücretli araç. Kalem limiti ve fiş zorunluluğu kategori tanımındadır. Form (`EXPENSE_REPORT` / `MSF-…`) çok kalemlidir; dövizli fiş kayıt anındaki kurla yerel tutara çevrilir, KDV ayrıdır. Fiş görseli `POST /expense-reports/receipts` ve satır `receipt-url` ile `FileObject`’e bağlanır.

Personel yalnızca kendi formlarını görür. `expenses:create` başkası adına form açar. Gönderme `EXPENSE_REPORT` workflow’unu başlatır; geri çekme, ret ve yeniden gönderme aynı kodu dinler. Onaycı limit üstü ve eksik fiş uyarılarını görür. Ödeme `expenses:pay` ile kasa veya bankadan yapılır (`PAYMENT` hareketi ve nakit akışı). Ters kayıt ödemeyi geri alır. Onaylanan ve projeye bağlı form, proje maliyetine eklenir; iptalde düşülür.

Özet ucu `GET /expense-reports/summary`: onay bekleyen, ödeme bekleyen, bu ay ödenen, türe göre dağılım.

Web `web/src/features/expenses`: `my-expenses-page.tsx`, `expenses-page.tsx`, `expense-form-page.tsx`, `expense-detail-page.tsx`, `expense-settings-page.tsx`. Rotalar `/expenses/my`, `/expenses`, `/expenses/new`, `/expenses/$id`, `/expenses/edit.$id`, `/expenses/settings`.

## 16. Projeler (`projects`)

`api/src/modules/projects`. Controller `projects.controller.ts`. Servisler `projects.service.ts`, `project-tasks.service.ts`, `time-entries.service.ts`, `project-math.ts`. DTO `dto/project.dto.ts`.

| Controller | Yol |
| --- | --- |
| `ProjectsController` | `/projects` |
| `ProjectTasksController` | `/project-tasks` |
| `TimeEntriesController` | `/time-entries` |

Proje no `PROJECT` (`PRJ-…`). Kart müşteri cari, yönetici, `ProjectStatus` (planlandı, devam, beklemede, tamamlandı, iptal), tarih aralığı ve bütçe tutar. Geciken ve bütçesi aşan projeler işaretlenir. Ekip `ProjectMemberRole` lider veya üye ve saatlik maliyet taşır. Üye, `projects:read` olmadan kendi projesinde çalışır. Maliyetleri yönetici, lider ve `projects:read` görür.

Görev panosu `ProjectTaskStatus`: yapılacak, devam, incelemede, tamamlandı. Öncelik `ProjectTaskPriority`. Atama bildirim yollar. “Görevlerim” kullanıcının sorumlu olduğu kartları listeler.

Zaman çizelgesi haftalıktır; satır proje veya görevdir. Kapanan proje saat girişine kilitlenir. İşçilik maliyeti, giriş anındaki saatlik ücretle çarpılır (sonraki ücret değişikliği geçmişi bozmaz). Masraf entegrasyonu expenses modülündedir; proje detayı masraf, zaman ve bütçe kullanımını birlikte gösterir. Silme (`projects:delete`) yalnızca zaman kaydı olmayan projede geçerlidir.

Web `web/src/features/projects`: `projects-page.tsx`, `project-detail-page.tsx`, `project-form-dialog.tsx`, `project-members-card.tsx`, `task-board.tsx`, `task-form-dialog.tsx`, `my-tasks-page.tsx`, `timesheet-page.tsx`, `project-time-entries.tsx`, `project-expenses.tsx`. Rotalar `/projects`, `/projects/$id`, `/projects/my-tasks`, `/projects/timesheet`.

## 17. Bordro (`payroll`)

`api/src/modules/payroll`. Controller `payroll.controller.ts`. Servisler `payroll.service.ts`, `payroll-settings.service.ts`, `salaries.service.ts`, `payroll-math.ts` (`payroll-math.spec.ts`). DTO `dto/payroll.dto.ts`. Puantaj için `HrModule` export’u `AttendanceService` kullanılır.

| Controller | Yol |
| --- | --- |
| `PayrollPeriodsController` | `/payroll-periods` |
| `PayslipsController` | `/payslips` |
| `SalariesController` | `/salaries` |
| `PayrollParametersController` | `/payroll-parameters` |

Ücret geçmişi tarihli `SalaryRecord` satırlarıdır; değişim yüzdesi ve planlanan zam tutulur. Onaylı bordrosu olan aya geriye dönük ücret yazılmaz. Parametreler yıl bazındadır: asgari ücret, SGK tavanı, işçi ve işveren prim oranları, damga vergisi, fazla mesai katsayısı, gelir vergisi dilimleri. Seed 2026 değerlerini yükler (`seed-payroll.ts`).

Hesap `payroll-math.ts`: 30 gün esası, puantajdan eksik gün ve fazla mesai, ücretsiz izin düşümü, SGK matrahı tavan/taban, kümülatif gelir vergisi, asgari ücret gelir ve damga vergisi istisnası. Dönem `PayrollPeriodStatus`: taslak, onaylı, ödendi. Taslak yeniden hesaplanır; pusulaya ek kazanç ve kesinti `PayslipItem` (`PayslipItemKind`) olarak girer. Onay personele bildirim yollar. Ödeme tek hazine hareketidir (`BNK-MAAS` hesabı seed’de vardır); `payroll:pay` ters kayıtla geri alır. Numara `PAYROLL` (`BRD-…`).

Kendi pusulası izinsiz `GET` ile açılır. `payroll:read` tüm dönem ve ücretleri görür; `create` dönem açar ve taslağı düzenler; `update` ücret ve parametre; `approve` onay ve yeniden açma.

Web `web/src/features/payroll`: `payroll-periods-page.tsx`, `payroll-period-page.tsx`, `payslip-page.tsx`, `my-payslips-page.tsx`, `salaries-page.tsx`, `salary-history.tsx`, `payroll-settings-page.tsx`. Rotalar `/payroll`, `/payroll/$id`, `/payroll/payslips/$id`, `/payroll/my`, `/payroll/salaries`, `/payroll/settings`. Personel kartına ücret geçmişi gömülür.

## 18. İşe alım (`recruitment`)

`api/src/modules/recruitment`. Controller `recruitment.controller.ts`. Servisler: `job-postings.service.ts`, `candidates.service.ts`, `job-applications.service.ts`, `interviews.service.ts`, `recruitment-support.ts`, `recruitment-math.ts`. DTO `dto/recruitment.dto.ts`. İşe alım `EmployeesService` çağırır.

| Controller | Yol |
| --- | --- |
| `JobPostingsController` | `/job-postings` |
| `CandidatesController` | `/candidates` |
| `JobApplicationsController` | `/job-applications` |
| `InterviewsController` | `/interviews` |
| `JobOffersController` | `/job-offers` |

İlan (`JOB_POSTING` / `ILN-…`) departman, pozisyon, şube, çalışma şekli ve yeri, kadro, ücret aralığı, işe alım yöneticisi ve son başvuru tarihini tutar. `JobPostingStatus`: taslak, yayında, beklemede, kapalı. Aday havuzu iletişim, `CandidateSource`, beklenen ücret ve CV dosyası (`POST /candidates/:id/cv`, presigned `cv-url`) içerir. Aynı adayın aynı ilana ikinci başvurusu reddedilir.

Başvuru aşamaları `ApplicationStage`: başvurdu, ön değerlendirme, mülakat, teklif. `POST :id/move` panoyu günceller. Ret gerekçeli, aday çekilebilir, yeniden açılabilir. Notlar ve `ApplicationActivity` süreci yazar. Mülakat `InterviewType`, tarih, süre, yer ve katılımcılarla açılır; katılımcılara bildirim gider. `GET /interviews/mine` ve `PUT /interviews/:id/feedback` izin dekoratörü olmadan mülakatçının kendi puan, tavsiye (`InterviewRecommendation`) ve yorumunu alır. Herkes değerlendirince mülakat tamamlanır.

Teklif brüt ücret, başlangıç ve geçerlilik taşır (`accept` / `decline` / `withdraw`). `POST /job-applications/:id/hire` (`recruitment:hire`) kabul edilmiş teklifi personel kartına ve ilk `SalaryRecord` kaydına çevirir. Kadro dolunca ilan kapanır, yöneticiye bildirim gider.

Web `web/src/features/recruitment`. Rotalar `/recruitment`, `/recruitment/$id`, `/recruitment/candidates`, `/recruitment/candidates/$id`, `/recruitment/applications`, `/recruitment/applications/$id`, `/recruitment/interviews`.

## 19. Performans (`performance`)

`api/src/modules/performance`. Controller `performance.controller.ts`. Servisler `competencies.service.ts`, `review-cycles.service.ts`, `performance-reviews.service.ts`, `performance-support.ts`, `performance-math.ts`. DTO `dto/performance.dto.ts`.

| Controller | Yol |
| --- | --- |
| `CompetenciesController` | `/competencies` |
| `ReviewCyclesController` | `/review-cycles` |
| `PerformanceReviewsController` | `/performance-reviews` |
| `PerformanceGoalsController` | `/performance-goals` |

Yetkinlik kataloğu ad, açıklama, sıra ve aktiflik tutar. Dönemde kullanılmış yetkinlik silinemez. Dönem tarihler, öz değerlendirme ve yönetici son tarihleri, hedef ve yetkinlik ağırlıkları ile seçili yetkinlikleri taşır. `ReviewCycleStatus`: taslak, aktif, kapalı. Başlatma uygun personel için `PerformanceReview` açar, yöneticiyi değerlendiren yapar ve bildirim yollar.

Form en fazla 10 ağırlıklı hedef (`PerformanceGoal`) ve gerçekleşme yüzdesi alır. Öz değerlendirme ve yorum çalışana aittir. Yönetici puanı, `CompetencyRating`, güçlü yönler ve gelişim alanları ayrıdır. Geri gönderme, çalışan onayı ve İK’nın yeniden açması durum makinesindedir (`PerformanceReviewStatus`). Puanlar karşı tarafa durum uygun olana kadar gizlenir. `performance-math.ts` ağırlıklı hedef puanı, yetkinlik ortalaması, genel puan ve beş kademeli bant üretir. Dönem ve departman ortalaması ile dağılım özet uçlarındadır.

Çalışan kendi formunu, yönetici doğrudan bağlılarını izin kodu olmadan işler. `performance:read` her formu görür; `create|update|delete` katalog ve dönem içindir; `update` İK’nın değerlendiren gibi davranmasını ve kapalı formu açmasını da kapsar.

Web `web/src/features/performance`. Rotalar `/performance`, `/performance/cycles/$id`, `/performance/reviews/$id`, `/performance/competencies`, `/performance/my`.

## 20. Eğitim (`training`)

`api/src/modules/training`. Controller `training.controller.ts`. Servisler `training-courses.service.ts`, `training-sessions.service.ts`, `trainings.service.ts`, `training-support.ts`, `training-math.ts`. DTO `dto/training.dto.ts`.

| Controller | Yol |
| --- | --- |
| `TrainingCoursesController` | `/training-courses` |
| `TrainingSessionsController` | `/training-sessions` |
| `TrainingEnrollmentsController` | `/training-enrollments` |
| `TrainingsController` | `/trainings/mine`, `/summary`, `/compliance`, `/employees/:employeeId` |

Katalog kod, `TrainingCategory`, `TrainingFormat`, süre, sağlayıcı, zorunluluk ve sertifika geçerlilik süresi tutar. Oturum tarih, yer, eğitmen, kontenjan ve maliyet taşır (`TrainingSessionStatus`). Toplu katılım `POST /training-sessions/:id/enrollments`. Self-servis `POST|DELETE /training-sessions/:id/enroll-me`. Oturum iptali katılımcılara bildirim yollar. Tamamlama `POST :id/complete` katılan / katılmayan, sınav puanı ve sertifika bitişini yazar. Memnuniyet `PUT /training-enrollments/:id/feedback`.

Zorunlu eğitim uyumu personel × eğitim matrisidir: geçerli, süresi yaklaşan, süresi geçmiş, alınmamış; planlı oturum varsa gösterilir. Özet saat, maliyet ve kategori kırılımıdır.

Web `web/src/features/training`: `training-courses-page.tsx`, `training-sessions-page.tsx`, `training-session-page.tsx`, `my-trainings-page.tsx`, `compliance-page.tsx`, `employee-trainings.tsx`. Rotalar `/training`, `/training/courses`, `/training/sessions/$id`, `/training/my`, `/training/compliance`.

## 21. Destek talepleri (`support`)

`api/src/modules/support`. Controller `support.controller.ts`. Servisler `tickets.service.ts`, `ticket-categories.service.ts`, `support-summary.service.ts`, `support-helpers.ts`, `support-math.ts`. DTO `dto/support.dto.ts`.

| Controller | Yol |
| --- | --- |
| `TicketsController` | `/tickets` |
| `TicketCategoriesController` | `/ticket-categories` |
| `TicketSlaPoliciesController` | `/ticket-sla-policies` |

Talep no `TICKET` (`TKT-…`). Alanlar: konu, açıklama, kategori, `TicketPriority` (düşük, normal, yüksek, acil), talep sahibi, sorumlu. `TicketStatus`: açık, işlemde, bilgi bekleniyor, çözüldü, kapandı. Herkes kendi talebini açar, yorumlar ve dosya ekler (`POST :id/attachments`). Çözülen talebi sahibi puanlar veya yeniden açar; yanıtsız talebi geri çekebilir. Kategori varsayılan sorumluya otomatik atar; talebi olan kategori silinemez.

SLA `TicketSlaPolicy` öncelik başına ilk yanıt ve çözüm hedefidir. Bilgi beklerken çözüm saati durur. Öncelik değişince hedefler yeniden hesaplanır. Saat durumları: zamanında, riskli, aşıldı, karşılandı, durduruldu (`support-math.ts`). Destek ekibi `support:update` ile atar, üstlenir, durum ve öncelik değiştirir, dahili not düşer. `support:create` başkası adına talep açar. Geçmiş `TicketEvent` (`TicketEventType`).

Kuyruk görünümleri: bana atanan, atanmamış, SLA aşılan, bilgi bekleyen, onay bekleyen. Özet ortalama ilk yanıt, çözüm süresi, SLA uyumu, memnuniyet, ekip yükü ve 14 günlük trend (`GET /tickets/summary`).

Web `web/src/features/support`. Rotalar `/support`, `/support/my`, `/support/settings`, `/support/tickets/$id`.

## 22. Sözleşmeler (`contracts`)

`api/src/modules/contracts`. Controller `contracts.controller.ts`. Servisler `contracts.service.ts`, `contract-types.service.ts`, `contract-summary.service.ts`, `contract-helpers.ts`, `contract-math.ts`. İşlemci `contracts.processor.ts` (her gün 07:00, elle `POST /contracts/run`). DTO `dto/contract.dto.ts`.

Tür `ContractParty` (cari veya personel), `ContractFlow` (gelir, gider, parasal değil), varsayılan süre ve ihbar süresi. Sözleşmesi olan tür silinemez ve tarafı değiştirilemez. Sözleşme no `CONTRACT` (`SZL-…`). Alanlar: taraf, sorumlu, başlangıç / bitiş / imza, tutar, döviz, `ContractBillingCycle` (tek sefer, aylık, üç aylık, yıllık), açıklama, ekler (`POST :id/attachments`, presigned url).

`ContractStatus`: taslak, yürürlükte, sona erdi, feshedildi. Uçlar `activate`, `renew`, `terminate`, `cancel-termination`. İleri tarihli fesih geri alınabilir. Otomatik yenileme, fesih son gününe kadar bildirilmezse süreyi yenileme kadar uzatır. Hatırlatma bitişten veya fesih son gününden N gün önce sorumlu kullanıcıya bildirim ve e-posta yollar. Olaylar `ContractEvent` (`ContractEventType`). Özet yürürlük, bitiyor, fesih planı, para birimine göre yıllık gelir/gider ve 12 aylık takvimdir.

Web `web/src/features/contracts`. Rotalar `/contracts`, `/contracts/$id`, `/contracts/types`. Cari ve personel kartında `party-contracts.tsx`.

## 23. Bütçe (`budgets`)

`api/src/modules/budgets`. Controller `budgets.controller.ts`. Servisler `budgets.service.ts`, `budget-items.service.ts`, `budget-entries.service.ts`, `budget-actuals.service.ts`, `budget-math.ts`. İşlemci her gün 07:30, elle `POST /budgets/run`. DTO `dto/budget.dto.ts`.

Kalem kodu, `BudgetItemKind` (gelir/gider) ve `BudgetSource`: elle giriş, masraf raporu, bordro, satın alma faturası, satış faturası. Masraf veya ürün kategorisine eşlenir; kategorisiz “diğer” kalemi vardır. Bütçe yıl başına şirket geneli veya departmandır. On iki aylık plan boş, geçen yılın planından veya gerçekleşenden yüzde ile başlatılabilir. `BudgetStatus`: taslak, onaylı. Yeniden açma gerekçe ve revizyon numarası ister (`BudgetEvent`).

Gerçekleşen kaynaklar: onaylı masraflar, bordro işveren maliyeti, alış ve satış faturaları (iadeler düşülür), `BudgetEntry` elle kayıtları. Departman bütçesi alt departmanları kapsar. Karşılaştırma aylık ve yılbaşından bugüne plan / gerçekleşen, sapma, kullanım, kalem durumu (planda, planı aştı, aşım, geride) ve kaynak belge kırılımıdır. Uyarı yıllık planın %90’ı ve aşımında sorumluya gider (`BudgetAlert`, `BudgetAlertLevel`). Sahip kendi bütçesini `budgets:read` olmadan görür. `update` taslak ve plan; `approve` onay ve yeniden açma.

Web `web/src/features/budgets`. Rotalar `/budgets`, `/budgets/$id`, `/budgets/items`, `/budgets/entries`.

## 24. Araç ve filo (`fleet`)

`api/src/modules/fleet`. Controller `fleet.controller.ts`: `VehiclesController` `/vehicles`, yakıt listesi `/fuel-entries`. Servisler `vehicles.service.ts`, `fleet-fuel.service.ts`, `fleet-summary.service.ts`, `fleet-helpers.ts`, `fleet-math.ts`. İşlemci her gün 07:15, elle `POST /vehicles/run`. DTO `dto/fleet.dto.ts`.

Plaka Türkiye formatında doğrulanır ve şirket içinde tekildir. Kart marka, model, `VehicleFuelType`, `VehicleOwnership` (şirket, uzun veya kısa kiralık), kiralama bitişi, departman, bakım aralığı (km ve ay) tutar. `VehicleStatus` hizmet dışı olunca açık zimmet kapanır. Zimmet, devir (önceki zimmet aynı gün biter) ve teslim sürücüye bildirim yollar.

Km `VehicleOdometerReading`, kaynak `VehicleOdometerSource`: elle, yakıt, servis, zimmet. Geriye dönük okuma kronolojiyi bozamaz. Yakıt sürücünün kendi aracına girilir; depo dolumu ile L/100 km ve birim fiyat hesaplanır (`fleet-math.ts`). Bakım `VehicleServiceType`: periyodik, onarım, lastik, kaza. Sonraki bakım km ve tarih planlanır. Belgeler `VehicleDocumentType`: muayene, trafik sigortası, kasko, egzoz. Durum: geçerli, yaklaşıyor, süresi doldu, kayıt yok. Hatırlatma bitişe 30 gün kala ve bittiğinde yöneticiye ve sürücüye gider. Pano yıllık maliyet, km başına maliyet, ortalama tüketim ve son 12 ayı gösterir.

Sürücü kendi aracı, yakıt ve km için `fleet:read` gerekmez. `fleet:update` kart, zimmet, servis, belge ve hatırlatma işini yönetir.

Web `web/src/features/fleet`. Rotalar `/fleet`, `/fleet/$id`, `/fleet/fuel`, `/fleet/my`.

## 25. Muhasebe (`accounting`)

`api/src/modules/accounting`. Controller `accounting.controller.ts` üç sınıftır. Servisler `ledger-accounts.service.ts`, `journal.service.ts`, `accounting-posting.service.ts`, `accounting-reports.service.ts`. Saf modüller `accounting-chart.ts` (tekdüzen hesap planı), `accounting-rules.ts`, `accounting-math.ts`, `accounting-helpers.ts`. İşlemci her gece 02:30 ve `POST /accounting/run`. DTO `dto/accounting.dto.ts`.

| Controller | Yol |
| --- | --- |
| `AccountingController` | `/accounting/summary`, `/options`, `/settings`, `/pending`, `/run`, `/trial-balance`, `/balance-sheet`, `/income-statement` |
| `LedgerAccountsController` | `/ledger-accounts`, `POST /install`, `GET :id/ledger` |
| `JournalEntriesController` | `/journal-entries`, `POST :id/post`, `POST :id/reverse` |

Hesap planı tek tıkla `POST /ledger-accounts/install` kurulur. Sistem hesapları silinmez. Noktalı alt hesap (`120.01`) ana hesabın `LedgerAccountType` değerini alır ve bakiyesine eklenir. Pasife alma ve silme kuralları `accounting-rules.ts` içindedir.

Yevmiye `JOURNAL_ENTRY` (`YEV-…`). Taslakta borç = alacak şarttır. `JournalEntryStatus` taslak veya kesin. Kesinleştirme `accounting:approve`. Ters fiş aynı izni ister. Satırda cari ve personel kırılımı olabilir. `JournalLine` denetim dışı bırakılır; fiş denetlenir.

Otomatik fiş kaynakları `JournalSource`: satış ve alış faturası, satış iadesi, irsaliye maliyeti, stok hareketi, tahsilat ve ödeme (çek/senet ciro dahil), çek tahsili ve ödemesi, kasa ve cari açılışı, masraf formu ve ödemesi, bordro ve maaş ödemesi, üretim (710 / 711 / 721 / 731). İptal ters fiş üretir. Değişen bordro yeniden kaydolur. Dönem kilidi `PATCH /accounting/settings` (`accounting:close`) ile bir tarihe kadar fiş, ters kayıt ve otomatik kaydı engeller.

Raporlar: muavin (yürüyen bakiye, cari filtresi), mizan (alt hesaplı), bilanço (dönem kârı/zararı özkaynakta), tekdüzen gelir tablosu. Excel ve PDF DataTable dışa aktarmasıdır.

Web `web/src/features/accounting` ve `account-codes.ts`. Rotalar `/accounting`, `/accounting/accounts`, `/accounting/accounts/$id`, `/accounting/journal`, `/accounting/journal/new`, `/accounting/journal/$id`, `/accounting/journal/edit.$id`, `/accounting/trial-balance`, `/accounting/balance-sheet`, `/accounting/income-statement`.

## 26. e-Fatura simülasyonu (`einvoice`)

`api/src/modules/einvoice`. `EInvoiceController` `/api/v1/e-invoices`. Servis `einvoice.service.ts`, XML `einvoice-xml.ts`, kurallar `einvoice-rules.ts`, dinleyici `einvoice.listener.ts`, işlemci `einvoice.processor.ts`. DTO `dto/einvoice.dto.ts`. Şema `EInvoice`, `EInvoiceEvent`; enumlar `EInvoiceDirection`, `EInvoiceProfile`, `EInvoiceStatus`.

UBL-TR 2.1 (TR1.2) satıcı ve alıcı (VKN 10 hane veya TCKN 11 hane), satırlar, KDV kırılımı, kur ve ETTN üretir. Profil `TEMELFATURA` veya `TICARIFATURA`; e-Arşiv ayrı profildir. GİB numarası `E_INVOICE` (`EPF` + 9 hane) veya `E_ARCHIVE` (`EPA` + 9 hane) serisindendir. Ayar anahtarı `einvoice`: gönderici etiketi, varsayılan profil, `autoSend`. Cari kartında `eInvoiceAlias` varsa e-Fatura, yoksa e-Arşiv seçilir.

Simülasyon durumları: kuyrukta, gönderildi, alıcıya ulaştı, hata. Hata kodu ve doğrulama mesajı olay geçmişine yazılır. `POST /e-invoices/sync` elle tur atar; işlemci her dakika ve gönderim sonrası `EINVOICE_SYNC_JOB` ile aynı `sync` metodunu çağırır. Hatalı zarf `POST :id/resend`. Ticari faturada alıcı yanıtı 8 gün içinde kabul veya reddir; süre dolunca kabul sayılır (`einvoice-rules.ts`). e-Arşiv iptali satış faturasının iptal kurallarına bağlıdır. Gelen fatura `POST /simulate-incoming` ile üretilir; `respond` kabul/red, `record` (`einvoice:update` ve `purchasing:create`) alış faturasına aktarır.

Web `web/src/features/einvoice` (`einvoices-page.tsx`, `einvoice-detail-page.tsx`, `einvoice-rules.ts`). Rotalar `/e-invoices`, `/e-invoices/$id`. XML detay sayfasında gösterilir.

## 27. Üretim (`production`)

`api/src/modules/production`. Tek `ProductionController` `/api/v1/production`. Servisler `boms.service.ts`, `work-orders.service.ts`, `mrp.service.ts`, `production-math.ts`, `production-helpers.ts` (izin sabitleri `PRODUCTION_READ|UPDATE|RECORD`). DTO `dto/production.dto.ts`.

Uçlar: `GET /summary`, `GET /requirements`, `POST /requirements/purchase-request`, `GET|POST /boms`, `GET /boms/:id`, `GET /boms/:id/plan`, `PATCH|DELETE /boms/:id`, `GET|POST /work-orders`, `GET|PATCH /work-orders/:id`, `POST :id/release|cancel|complete`, `POST :id/records`.

Ürün ağacı parti miktarı, fire oranı, işçilik ve genel üretim gideri, varsayılan reçete bayrağı taşır. Döngü `boms.service` tarafından reddedilir. `GET /boms/:id/plan` çok seviyeli standart maliyet ve malzeme planı döner. İş emri no `WORK_ORDER` (`ISE-…`). `WorkOrderStatus`: taslak, serbest, üretimde, tamamlandı, iptal. Planlanan tarihler, malzeme deposu ve mamul deposu ayrıdır. Gecikme ve eksik kapatma işaretlenir.

Üretim kaydı `POST /work-orders/:id/records` (`production:record`) malzemeyi FEFO ile çıkarır, gerçekleşen tüketimi yazar, mamulü tam maliyetle ve lotla stoğa alır. Fiş no `PRODUCTION` (`URT-…`). MRP `GET /requirements` iş emri ve satış siparişi ihtiyacını, stok, açık satın alma ve açık üretimi netleştirir. Eksikler `POST /requirements/purchase-request` ile `PURCHASE_REQUEST` workflow’una veya yeni iş emrine döner. Muhasebe üretim fişi 710, 711, 721, 731 hesaplarını kullanır (`accounting-posting`).

Web `web/src/features/production` (`boms-page.tsx`, `bom-form-page.tsx`, `bom-page.tsx`, `work-orders-page.tsx`, `work-order-page.tsx`, `requirements-page.tsx`, `production-rules.ts`). Rotalar `/production`, `/production/boms`, `/production/boms/new`, `/production/boms/$id`, `/production/boms/edit/$id`, `/production/work-orders/$id`, `/production/requirements`.

## 28. Denetim, dosya, bildirim, numara

Bu dört modül platform bölümünde davranış olarak anlatıldı. Dosya karşılıkları:

| Modül | API | Web |
| --- | --- | --- |
| `audit` | `audit.controller.ts`, `audit.service.ts`, `dto/audit-log.dto.ts` | `features/audit/audit-logs-page.tsx`, `/audit-logs` |
| `files` | `files.controller.ts`, `files.service.ts`, `dto/file.dto.ts`, `infrastructure/storage` | Doğrudan liste sayfası yok; fiş, ek ve CV diyalogları generated `files` uçlarını çağırır |
| `notifications` | `notifications.controller.ts`, `notifications.service.ts`, `notifications.gateway.ts`, `dto/notification.dto.ts` | `features/notifications`, `/notifications` |
| `numbering` | `numbering.controller.ts`, `numbering.service.ts`, `number-format.ts`, `dto/number-sequence.dto.ts` | Seri bakım uçları generated client’tadır; önizleme `formatNumber` ile DTO `preview` alanından gelir |

`AuditModule` global kullanılmak üzere `AuditService.record` export eder. `FilesModule` ve `NumberingModule` diğer modüllerce içe aktarılır. `NotificationsModule` gateway’i süreç ömrü boyunca açıktır.

## 29. Kullanıcılar ve roller (`users`, `roles`)

### Kullanıcılar

`UsersController` `/api/v1/users`. Servis `users.service.ts`, olaylar `users.events.ts` (`USER_EVENTS.INVITED`), DTO `dto/user.dto.ts`. İzin `users:read|create|update|delete`.

Kullanıcı e-posta ile tekildir, `deletedAt` ile yumuşak silinir. Oluşturma davet olayını yayınlar; `AuthListener` bağlantıyı postalar. Üyelik `UserCompany` (şirket, varsayılan şirket, varsayılan şube) ve `UserRole` (şirket içi rol) birlikte yazılır. Servis, değişiklikten sonra `AuthContextService.invalidateUser` çağırır. Personel kartı `userId` ile bu kayda bağlanır; bir kullanıcının birden fazla şirket personeli olabilir.

Web `web/src/features/users/users-page.tsx`, `user-form-dialog.tsx`. Rota `/users`.

### Roller

`RolesController` `/api/v1/roles`, `PermissionsController` `GET /api/v1/permissions` (`roles:read`). Servis `roles.service.ts`. DTO `dto/role.dto.ts`. Registry `permissions.registry.ts` (`permissions.registry.spec.ts`).

Rol şirket içinde `code` ile tekildir. `isSystem` roller (seed `admin`) silinemez. İzin ataması `RolePermission` ara tablosudur; katalog `PERMISSION_REGISTRY` dışına çıkamaz. Kayıt sonrası `invalidateAll` Redis’teki tüm `auth:ctx:*` anahtarlarını tarar. Yeni rol kod değişikliği gerektirmez (`docs/adr/0003-authorization-casl.md`).

Web `web/src/features/roles`. Rota `/roles`.

## 30. Ayarlar (`settings`)

`SettingsController` `/api/v1/settings`. Servis `settings.service.ts`. DTO `dto/settings.dto.ts`. Şema `settings.prisma`.

| Yol | İçerik | İzin |
| --- | --- | --- |
| `GET|POST /currencies`, `PATCH /currencies/:code` | Para birimi | yazma `settings:update` |
| `GET|POST /exchange-rates` | Kur (alış/satış, tarih, kaynak) | `settings:read` / `update` |
| `GET|POST|PATCH /tax-rates` | KDV kartı | aynı |
| `GET|POST|PATCH /units` | Birim | aynı |
| `GET /company`, `PUT /company/:key` | Şirket JSON ayarı | `settings:read` / `update` |

Seed para birimleri TRY, USD, EUR, GBP. Kurlar günün UTC tarihine `source=manual` ile yazılır. KDV kodları `KDV20` (varsayılan), `KDV10`, `KDV1`, `KDV0`. Birimler ADET, KG, LT, M, M2, KOLI, SAAT. `general` ayarı `dateFormat: dd.MM.yyyy`, `timezone: Europe/Istanbul`, `fiscalYearStartMonth: 1`.

Web `web/src/features/settings/settings-page.tsx`. Rota `/settings`. Tarih ve para biçimi `web/src/shared/lib/format.ts` içinde `tr-TR` kurallarına uyar.

## 31. Workflow modülü (dosya haritası)

Davranış bölüm 4.8’dedir. Dosyalar:

- `workflow.module.ts`
- `workflow.controller.ts` — `WorkflowDefinitionsController`, `WorkflowInstancesController`
- `workflow.service.ts`, `workflow-definitions.service.ts`
- `workflow.events.ts`
- `dto/workflow.dto.ts`

Modül export edildiği için hr, purchasing ve expenses dinleyiciyi kendi modülünde tutar; workflow modülü belge tablolarına yazmaz. Yeni bir onaylı belge eklemek için: registry’ye izin gerekmez (mevcut `workflow:start` yeter), şirket için `WorkflowDefinition.code` seed veya API ile açılır, servis `WorkflowService.start` çağırır, `@OnEvent` ile kendi durumunu günceller.

## 32. Modüller arası sınırlar

Aşağıdaki oklar kodda gerçekten vardır. Ters yönde Prisma çağrısı yapılmamalıdır.

- `hr` → `workflow` (izin), `assets` (çıkışta zimmet).
- `purchasing` → `workflow`, `inventory` (mal kabul), `partners` (fatura defteri).
- `sales` → `inventory` (rezervasyon, sevk, iade), `partners`, olay ile `einvoice`.
- `finance` → `partners` (kapama), `treasury` hareketi masraf ve bordro ödemesinde de kullanılır.
- `expenses` → `workflow`, `files`, `finance` (ödeme), `projects` (maliyet).
- `payroll` → `hr` puantaj ve personel, `finance` maaş ödemesi, `accounting` fişi.
- `recruitment` → `hr` `EmployeesService.hire`, `files` (CV).
- `production` → `inventory` (reçete stoku, fiş), `purchasing` (talep), `accounting` (710 grubu).
- `accounting` → kaynak belgeleri okur, yevmiye yazar; kaynak modüller yevmiye satırına yazmaz.
- `budgets` → masraf, bordro, alış ve satış faturalarını gerçekleşen olarak okur.

Domain olayı eklemek `EventEmitterModule.forRoot({ wildcard: true })` sayesinde `workflow.*` dinlemelerine de izin verir. Yeni olay sabiti ilgili modülün `*.events.ts` dosyasında durur.

## 33. Seed, testler, komutlar ve OpenAPI

### 33.1 Seed

Komut, `api` dizininde:

```bash
pnpm db:deploy    # prisma migrate deploy
pnpm db:seed      # tsx prisma/seed.ts
pnpm db:reset     # migrate reset --force (veriyi siler, yeniden migrate ve seed)
pnpm db:studio
pnpm db:generate
pnpm db:migrate   # geliştirme: prisma migrate dev
```

`api/prisma.config.ts` şema klasörünü `prisma/schema` ve seed komutunu `tsx prisma/seed.ts` olarak bağlar. `seed.ts` sırası: izinler (`ALL_PERMISSION_CODES`), para birimleri ve günlük kur, iki şirket ve şubeler, numara serileri, KDV ve birimler, roller, kullanıcılar, İK (departman, pozisyon, personel, izin türü, bakiye, resmi tatil, izin workflow’u ve örnek talepler), ardından yan dosyalar:

| Dosya | İçerik |
| --- | --- |
| `seed-admin-profile.ts` | Yönetici personel profili, ek izin ve masraf örneği |
| `seed-attendance.ts` | Vardiya ve puantaj |
| `seed-inventory.ts` | Kategori, depo `MRK`, örnek ürün ve barkod, hareket, sayım |
| `seed-trade.ts` | `seedPartners`, `seedPurchasing` |
| `seed-sales.ts` | Teklif, sipariş, sevk, fatura |
| `seed-finance.ts` | Kasa, banka, tahsilat, çek |
| `seed-crm.ts` | Aday, fırsat, aktivite |
| `seed-expenses.ts` | Masraf türleri ve formlar |
| `seed-projects.ts` | Proje, görev, zaman |
| `seed-payroll.ts` | Parametre, ücret, dönem |
| `seed-recruitment.ts` | İlan, aday, mülakat, teklif |
| `seed-performance.ts` | Yetkinlik, dönem, form |
| `seed-training.ts` | Katalog (İSG, KVKK, oryantasyon, …) ve oturum |
| `seed-support.ts` | Kategori, SLA, talep |
| `seed-contracts.ts` | Tür ve sözleşme |
| `seed-budgets.ts` | Kalem ve yıllık plan |
| `seed-fleet.ts` | Araç, zimmet, yakıt, belge |
| `seed-accounting.ts` | Hesap planı ve örnek fiş |
| `seed-einvoice.ts` | Seri, etiket, örnek zarf |
| `seed-production.ts` | Reçete, iş emri, üretim fişi |

Seed idempotent upsert kullanır; ikinci çalıştırma demo kimliklerini çoğaltmaz, sayaçları mevcut belge adedinin ilerisine taşır.

### 33.2 Testler

API birim testleri Jest, `rootDir: src`, kalıp `.*\.spec\.ts$`. Çalıştırma `pnpm test`, izleme `pnpm test:watch`, kapsam `pnpm test:cov`. Kapsam dışı: `*.module.ts` ve `main.ts`. Mevcut spec dosyaları saf hesap ve kuralları kilitler: `ability.factory`, `document-totals`, `accounting-math`, `accounting-rules`, `depreciation`, `budget-math`, `contract-math`, `crm-math`, `einvoice-rules`, `einvoice-xml`, `expense-math`, `finance-math`, `fleet-math`, `timesheet`, `working-days`, `stock-math`, `number-format`, `payroll-math`, `performance-math`, `production-math`, `project-math`, `recruitment-math`, `report-math`, `permissions.registry`, `support-math`, `training-math`.

API e2e `pnpm test:e2e` → `jest --config ./test/jest-e2e.json --runInBand`. Ortam `test/setup-env.ts`, veritabanı `test/e2e-database.ts`, `test/global-setup.ts`. Supertest gerçek PostgreSQL’e gider. Dosyalar: `auth`, `hr`, `attendance`, `assets`, `inventory`, `partners`, `purchasing`, `sales`, `finance`, `reports`, `crm`, `expenses`, `projects`, `payroll`, `recruitment`, `performance`, `training`, `support`, `contracts`, `budgets`, `fleet`, `accounting`, `einvoice`, `production`.

Web birim/bileşen: `pnpm test` (Vitest, jsdom, `src/**/*.test.{ts,tsx}`). Örnekler `navigation.test.ts`, `session.test.ts`, `document-math.test.ts`, `account-codes.test.ts`, `einvoice-rules.test.ts`, `production-rules.test.ts`, `inventory-parsers.test.ts`, `date-ranges.test.ts`, `locales.test.ts`, `format.test.ts`, `validation.test.ts`. Tarayıcı: `pnpm e2e` (Playwright, `web/playwright.config.ts`, `web/e2e`). API’nin ayakta olması gerekir.

Her iki repoda GitHub Actions lint, format, tip, test ve Docker imajını çalıştırır. Commit mesajları Conventional Commits (`feat(auth): …`) ve `commitlint.config.mjs` + Husky ile denetlenir. `lint-staged` ESLint ve Prettier uygular.

### 33.3 pnpm komutları

API (`api/package.json`):

| Komut | İş |
| --- | --- |
| `pnpm start:dev` | `nest start --watch` |
| `pnpm start:debug` | inspect + watch |
| `pnpm start:prod` | `node dist/main` |
| `pnpm build` | `nest build` |
| `pnpm lint` / `lint:fix` | ESLint `src`, `test`, `prisma` |
| `pnpm format` / `format:check` | Prettier |
| `pnpm typecheck` | `tsc --noEmit` |
| `pnpm test` / `test:e2e` / `test:cov` | Jest |

Web (`web/package.json`):

| Komut | İş |
| --- | --- |
| `pnpm dev` | Vite `5173` |
| `pnpm build` | `tsc -b && vite build` |
| `pnpm preview` | statik önizleme |
| `pnpm lint` / `format` / `typecheck` | kalite |
| `pnpm test` / `test:watch` | Vitest |
| `pnpm e2e` | Playwright |
| `pnpm api:generate` | Orval |

Kökte paket yoktur. Altyapı komutları kökte `docker compose`, uygulama komutları ilgili repodadır.

### 33.4 OpenAPI istemci üretimi

1. API ayakta olsun (`pnpm start:dev`). Geliştirmede süreç `openapi.json` yazar ve `/docs-json` yayınlar.
2. Web dizininde `pnpm api:generate`.
3. Orval `web/orval.config.ts` girdiyi `OPENAPI_URL` veya `http://localhost:3000/docs-json` kabul eder.
4. Çıktı `mode: tags-split`, `client: react-query`, `httpClient: axios`, mutator `src/api/http.ts` içindeki `apiClient`. `clean: true` eski tag klasörlerini siler. `afterAllFilesWrite` Prettier çalıştırır.
5. Üretilen kancalar `web/src/api/generated/endpoints/<tag>/` altındadır. Şemalar `web/src/api/generated/model` altındadır. Özellik sayfaları bu kancaları import eder; DTO elle kopyalanmaz.

Swagger açıklaması istemciden `Authorization: Bearer` ve isteğe bağlı `x-company-id` / `x-branch-id` bekler (`swagger.ts`). `operationId` controller anahtarı + metot adıdır; controller yeniden adlandırılırsa üretilen fonksiyon adları değişir ve web importları güncellenmelidir.

### 33.5 Yerel ayağa kaldırma (özet)

```bash
# kök
cp .env.example .env
docker compose up -d

# api
cd api
cp .env.example .env
pnpm install
pnpm db:deploy
pnpm db:seed
pnpm start:dev

# web
cd ../web
cp .env.example .env
pnpm install
pnpm api:generate
pnpm dev
```

Kontrol listesi: `GET /api/v1/health` database ve redis `up`, Swagger `/docs` açılır, `admin@enterprisepulse.dev` ile `/login` oturum açar, şirket değiştirici Pulse Teknoloji ve Pulse Lojistik arasında geçer, gelen kutusu `/workflow/inbox` izin taleplerini gösterir, Mailpit `http://localhost:8025` davet ve hatırlatma postalarını tutar, RustFS konsolu `http://localhost:9001` yüklenen nesneyi gösterir.

### 33.6 Yeni modül eklerken

1. `api/prisma/schema/<modül>.prisma` modelini yaz, `pnpm db:migrate`.
2. `api/src/modules/<modül>` içinde module, controller, service, dto oluştur. Controller `{ path, version: '1' }`. Liste uçları `PaginationQueryDto` ve `paginated()` kullansın. Yazmalar `companyId` filtresi taşısın.
3. `PERMISSION_REGISTRY` içine `module:action` ekle. Uçlara `@RequirePermissions` koy. Self-servis ise serviste sahip filtresi olsun.
4. `AppModule` imports listesine modülü ekle.
5. Belge numarası gerekiyorsa `number_sequences` seed satırı ve `NumberingService.next` çağrısı aynı transaction’da olsun.
6. Onay gerekiyorsa workflow kodu ve `@OnEvent` dinleyicisi ekle; başka modülün tablosuna yazma.
7. `pnpm test` için saf kuralı `*.spec.ts` dosyasına, HTTP akışını `api/test/<modül>.e2e-spec.ts` dosyasına koy.
8. API’yi başlat, `pnpm api:generate` çalıştır.
9. `web/src/features/<modül>` sayfalarını ve `web/src/routes/_app/...` dosya rotasını ekle. Menü öğesini `navigation.ts` içine izin koduyla yaz. Metinleri `i18n/locales/tr.json` ve `en.json` içine koy.
10. Seed dosyası demo veriyi upsert etsin.
