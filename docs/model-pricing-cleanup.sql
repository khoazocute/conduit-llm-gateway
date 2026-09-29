-- Dọn model_pricing về đúng 10 dòng (K2, xem docs/model-pricing-sources.md).
-- Không phải Flyway migration (model_pricing không có seed data trong
-- db/migration/, 18 dòng hiện có là chèn tay lúc test qua /admin/model-pricing
-- hoặc psql trực tiếp) — chạy tay 1 lần bằng psql, không thêm vào
-- backend-gateway/src/main/resources/db/migration/.
--
-- Tiêu chí "Đạt" của Phase B (roadmap.md mục 3.B): select count(*) from
-- model_pricing = 10, đúng 5 model trong pool (proxy-configs/litellm/config.yaml)
-- x 2 unit_type (token_input/token_output), dùng đúng alias (không phải tên
-- model đầy đủ) và effective_from mới nhất (2026-09-23 07:18:49+00).

-- Xem trước sẽ xoá gì (chạy thử trước khi DELETE thật):
-- SELECT provider, model, unit_type, price_usd_per_unit, effective_from
-- FROM model_pricing
-- WHERE NOT (
--     model IN ('gpt-4o-mini', 'gpt-4o', 'claude-haiku', 'claude-sonnet', 'gemini-flash')
--     AND effective_from = '2026-09-23 07:18:49+00'
-- )
-- ORDER BY model, unit_type;

DELETE FROM model_pricing
WHERE NOT (
    model IN ('gpt-4o-mini', 'gpt-4o', 'claude-haiku', 'claude-sonnet', 'gemini-flash')
    AND effective_from = '2026-09-23 07:18:49+00'
);

-- Xác nhận đúng tiêu chí Phase B (kỳ vọng: count = 10):
SELECT count(*) FROM model_pricing;

-- Xem lại toàn bộ 10 dòng còn lại:
SELECT provider, model, unit_type, price_usd_per_unit, credit_markup_multiplier, effective_from
FROM model_pricing
ORDER BY model, unit_type;
