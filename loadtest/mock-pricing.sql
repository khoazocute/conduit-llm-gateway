-- TASK-56: gia 0 cho alias gia `conduit-mock` (proxy-configs/litellm/config.yaml), CHI dung o DB
-- local de load test. KHONG dua vao migration: production khong co alias nay.
-- Chay lai nhieu lan van an toan.
INSERT INTO model_pricing (provider, model, unit_type, price_usd_per_unit, effective_from)
SELECT 'openai', 'conduit-mock', u::unit_type, 0, '2026-01-01T00:00:00Z'
FROM unnest(ARRAY['token_input', 'token_output']) AS u
WHERE NOT EXISTS (SELECT 1 FROM model_pricing WHERE model = 'conduit-mock' AND unit_type = u::unit_type);
