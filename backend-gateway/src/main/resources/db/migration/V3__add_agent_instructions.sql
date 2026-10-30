-- System prompt rieng cua agent, theo mo hinh Claude Project (D8, docs/roadmap.md muc 4).
-- `introduction` giu vai tro mo ta cong khai tren cho; `instructions` la chi thi he thong
-- gui kem moi luot chat. Chi chu agent va admin duoc doc cot nay, KHONG tra cho nguoi mua
-- hay trang cong khai (GET /agents, GET /agents/{id} la permitAll).
-- NULL = agent khong co system prompt -> ChatService khong them luot system nao.
ALTER TABLE agents ADD COLUMN instructions text;
