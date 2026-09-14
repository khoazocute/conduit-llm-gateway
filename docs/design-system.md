# Conduit design system — dev-console dark theme

Nguồn gốc: chuyển thể từ 1 bản Claude Design canvas prototype, đã lọc lại chỉ giữ phần token/class thuần CSS (không phụ thuộc component library nào). Toàn bộ định nghĩa thật nằm ở `frontend/app/globals.css` — file này chỉ là bản tóm tắt để tra cứu nhanh khi làm trang mới (kể cả vertical Credit+Chat+Payment của Khoa), không phải nguồn chân lý.

## Nguyên tắc

- Dark-only, không có toggle light/dark.
- Toàn bộ UI dùng class CSS thuần (`.card`, `.btn`, `.badge`...), không cần thư viện component nào — tránh phụ thuộc như shadcn/Base UI từng gây lỗi `render`-prop.
- Font: Geist (sans) + Geist Mono — đã load sẵn qua `next/font/google` trong `app/layout.tsx`, không cần thêm gì khi dùng ở trang mới.
- Chữ mono (`.mono`, `--font-mono`) dùng cho: nhãn/label viết hoa, giá trị số (`.num`), badge, breadcrumb kiểu `conduit://...`.

## Màu (CSS custom properties, khai báo ở `:root` trong `globals.css`)

| Token | Giá trị | Dùng cho |
|---|---|---|
| `--bg` | `#07080a` | nền toàn trang |
| `--panel` | `#0e1116` | nền `.card` |
| `--panel-2` | `#161a21` | nền phụ (header bảng, tab active) |
| `--border-hard` | `#2a313d` | viền card/input/button |
| `--border-soft` | `#161a21` | viền mờ (divider trong table) |
| `--text` | `#e6e8ec` | chữ chính |
| `--text-dim` | `#8a93a3` | chữ phụ |
| `--text-faint` | `#555c6b` | chữ mờ nhất (label, timestamp) |
| `--accent` | `#54f0a8` | màu nhấn chính (xanh lá — nút primary, badge thành công, giá free) |
| `--warn` / `--danger` / `--info` | `#ffb454` / `#ff6a6a` / `#7ab9ff` | badge/trạng thái cảnh báo, lỗi, thông tin |

## Thang chữ

`--t-1` (11px) → `--t-10` (48px), tăng dần. `--t-8` dùng cho `.page-title`, `--t-3`/`--t-4` cho body text.

## Component class chính (xem `globals.css` để biết đầy đủ)

- **Layout trang**: `.page` (padding chuẩn + max-width), `.page-header`, `.page-eyebrow` (breadcrumb kiểu `conduit://...`), `.page-title`, `.page-subtitle`.
- **App shell**: `.app` (grid topbar+sidebar+main), `.topbar`, `.sidebar` + `.nav-item`/`.is-active`, `.sidebar-user`. Xem `frontend/components/app-shell.tsx` — component dùng lại được, tự đổi nav item theo role thật từ `useAuth()`.
- **Card**: `.card`, `.card-flush` (không padding, dùng khi nhét `.table` vào), `.card-head`, `.card-body`.
- **Button**: `.btn` (mặc định), `.btn-primary`, `.btn-ghost`, `.btn-danger`, `.btn-sm`/`.btn-lg`.
- **Badge**: `.badge`, `.badge-accent` (thành công/published), `.badge-warn`, `.badge-danger`, `.badge-info`.
- **Form**: `.input`, `.textarea`, `.select`, `.label` (uppercase, mono, nhỏ).
- **Bảng**: `.table` (dùng trong `.card.card-flush`).
- **Segmented control** (thay cho tab/select): `.seg` + `button.is-active` — ví dụ ở `dashboard/page.tsx` (lọc theo status) và `admin/users/page.tsx`.
- **Avatar**: `components/agent-avatar.tsx` + `lib/agent-visual.ts` — màu/chữ cái đầu suy ra tất định từ `id`/title thật, **không bịa dữ liệu** (không rating/stat giả).
- **Utility**: `.row`/`.col`/`.cluster`/`.stack-sm/md/lg` (flex layout), `.dim`/`.faint`/`.mono`/`.accent`, `.divider`.

## Khi làm trang mới (vd. vertical Credit+Chat+Payment)

1. Bọc trong `(app)` route group nếu cần sidebar/topbar chuẩn (tự động có qua `app/(app)/layout.tsx`), hoặc `(auth)` nếu là màn hình auth-style (căn giữa, không sidebar).
2. Dùng lại class có sẵn trong `globals.css`, đừng tạo màu/style mới ngoài palette trên trừ khi thật sự cần token mới — nếu cần, thêm vào `:root` trong `globals.css` để giữ nhất quán toàn app.
3. Không thêm rating/rating giả, stat giả, hay field không có trong DTO backend thật — chỉ style những gì API thực sự trả về.
