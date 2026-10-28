// TASK-56 (phan cua Hung): load test cac endpoint KHONG goi LLM — dang nhap, xem cho agent,
// xem chi tiet agent, xem vi. Phan chat (goi LLM qua proxy) la phan cua Khoa, dung alias gia
// trong LiteLLM de khong ton phi (docs/tasks/2026-10-19/tasks.md muc 6).
//
// Chay (backend o localhost:8081, can Docker):
//   docker run --rm -i -v "$PWD/loadtest:/scripts" grafana/k6:0.54.0 run \
//     -e BASE=http://host.docker.internal:8081/api /scripts/browse.js
//
// Moi VU dung tai khoan RIENG (tao trong setup): Conduit giu 1 phien refresh/user, nen dung chung
// 1 tai khoan se khong giong nguoi dung that.
import http from "k6/http";
import { check, sleep, group } from "k6";

const BASE = __ENV.BASE || "http://host.docker.internal:8081/api";
const VUS = Number(__ENV.VUS || 20);
const PASSWORD = "loadtest-password-123";
const JSON_HEADERS = { "Content-Type": "application/json" };

export const options = {
  scenarios: {
    browse: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: VUS }, // tang dan
        { duration: "1m", target: VUS }, // giu tai
        { duration: "15s", target: 0 }, // giam
      ],
      gracefulRampDown: "10s",
    },
  },
  // Nguong dat (khoa truoc khi chay). Dang nhap bam BCrypt nen tach rieng, nguong rong hon.
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:list_agents}": ["p(95)<500"],
    "http_req_duration{endpoint:get_agent}": ["p(95)<500"],
    "http_req_duration{endpoint:wallet}": ["p(95)<500"],
    "http_req_duration{endpoint:login}": ["p(95)<1500"],
    checks: ["rate>0.99"],
  },
};

export function setup() {
  const run = Date.now();
  const users = [];
  for (let i = 0; i < VUS; i++) {
    const email = `load.${run}.${i}@conduit.dev`;
    const res = http.post(
      `${BASE}/auth/register`,
      JSON.stringify({ email, password: PASSWORD, full_name: `Load ${i}` }),
      { headers: JSON_HEADERS, tags: { endpoint: "setup_register" } },
    );
    if (res.status !== 201) {
      throw new Error(`setup: register ${email} -> ${res.status} ${res.body}`);
    }
    users.push(email);
  }
  const list = http.get(`${BASE}/agents?size=20`).json();
  const agentIds = (list.items || []).map((a) => a.id);
  if (agentIds.length === 0) {
    throw new Error("setup: khong co agent published nao de xem — chay e2e_test.sh truoc de tao du lieu");
  }
  return { users, agentIds };
}

export default function (data) {
  const email = data.users[(__VU - 1) % data.users.length];
  let token;

  group("login", () => {
    const res = http.post(`${BASE}/auth/login`, JSON.stringify({ email, password: PASSWORD }), {
      headers: JSON_HEADERS,
      tags: { endpoint: "login" },
    });
    check(res, { "login 200": (r) => r.status === 200 });
    token = res.json("access_token");
  });
  const auth = { headers: { Authorization: `Bearer ${token}` } };

  // Mot phien duyet: vai luot xem cho va chi tiet agent, xem vi, nghi giua cac thao tac.
  for (let i = 0; i < 5; i++) {
    group("browse", () => {
      const page = http.get(`${BASE}/agents?size=12`, { tags: { endpoint: "list_agents" } });
      check(page, { "list 200": (r) => r.status === 200 });

      const id = data.agentIds[Math.floor(Math.random() * data.agentIds.length)];
      const detail = http.get(`${BASE}/agents/${id}`, { ...auth, tags: { endpoint: "get_agent" } });
      check(detail, {
        "detail 200": (r) => r.status === 200,
        // D8: nguoi xem khong phai chu agent thi KHONG duoc nhan system prompt, ke ca khi tai cao.
        "detail hides instructions": (r) => !(r.body || "").includes('"instructions"'),
      });

      const wallet = http.get(`${BASE}/wallet`, { ...auth, tags: { endpoint: "wallet" } });
      check(wallet, { "wallet 200": (r) => r.status === 200 });
    });
    sleep(1);
  }
}
