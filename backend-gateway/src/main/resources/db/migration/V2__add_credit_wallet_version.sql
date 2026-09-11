-- Optimistic locking cho credit_wallets, bat buoc theo CLAUDE.md muc 4:
-- "moi deduction credit chay trong transaction voi row-level lock hoac
-- optimistic version (tranh so du am khi co concurrent request)".
ALTER TABLE credit_wallets ADD COLUMN version bigint NOT NULL DEFAULT 0;
