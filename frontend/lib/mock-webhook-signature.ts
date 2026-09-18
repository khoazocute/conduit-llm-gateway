// Dev-only helper: computes the HMAC-SHA256 signature the mock payment
// webhook (`POST /payments/webhook/mock`) expects in the
// `X-Webhook-Signature` header. In a real payment gateway this signing
// happens on the gateway's server, never in the browser - this only exists
// because our "mock" gateway has no real server of its own, and the browser
// stands in for it during local testing (CLAUDE.md muc 7 security test still
// verifies the backend rejects a wrong signature, see PurchaseServiceTest /
// the curl test done earlier).
const MOCK_WEBHOOK_SECRET =
  process.env.NEXT_PUBLIC_MOCK_WEBHOOK_SECRET ?? "dev-only-mock-webhook-secret";

export async function signMockWebhookBody(rawBody: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(MOCK_WEBHOOK_SECRET),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(rawBody));
  return Array.from(new Uint8Array(signature))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}
