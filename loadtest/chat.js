// TASK-56, phan chat (Khoa): load test luong chat qua app that, KHONG goi LLM co phi.
//
// Backend phai chay voi CHAT_ACTIVE_PROXY=litellm CHAT_DEFAULT_MODEL=conduit-mock: alias gia trong
// proxy-configs/litellm/config.yaml tra mock_response, khong goi nha cung cap nao. Moi luot van di
// qua dung duong that: JWT -> tao hoi thoai -> POST tin nhan (SSE) -> backend goi LiteLLM -> tru
// credit -> ghi messages/usage_logs/routing_decisions. Chi phan goi LLM la gia.
//
// Hai kich ban (chon bang SCENARIO):
//   many_users (mac dinh): moi nguoi dung ao la 1 tai khoan rieng, vi rieng - tinh huong that.
//   one_user           : tat ca nguoi dung ao dung CHUNG 1 tai khoan -> 1 vi bi tranh chap toi da.
//                        Phep thu cho loi tru credit dong thoi (ChatService.recordSuccessfulTurnWithRetry).
//
// Setup tu dang ky tai khoan + mua agent mien phi (AGENT_ID) de co vi 1.000.000 credit.
// Chay: xem docs/load-test.md.
import http from 'k6/http';
import { check, fail } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const BASE_URL = __ENV.BASE_URL || 'http://host.docker.internal:8081/api';
const SCENARIO = __ENV.SCENARIO || 'many_users';
const MAX_VUS = Number(__ENV.MAX_VUS || 25);
const PASSWORD = 'loadtest-password-123';
const JSON_HEADERS = { 'Content-Type': 'application/json' };

export const options = {
  scenarios: {
    chat: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: Math.ceil(MAX_VUS / 2) },
        { duration: '1m', target: Math.ceil(MAX_VUS / 2) },
        { duration: '30s', target: MAX_VUS },
        { duration: '1m', target: MAX_VUS },
        { duration: '20s', target: 0 },
      ],
      gracefulRampDown: '10s',
    },
  },
  setupTimeout: '120s',
  thresholds: {
    'http_req_failed{step:send_message}': ['rate<0.01'],
    'chat_turn_error': ['count==0'],
    'chat_turn_ms': ['p(95)<2000'],
  },
};

const chatTurnMs = new Trend('chat_turn_ms', true);
const chatTurnOk = new Counter('chat_turn_ok');
const chatTurnError = new Counter('chat_turn_error');
// Phan loai luot loi theo thong diep SSE `event:error` cua ChatService.
const errInsufficientCredit = new Counter('err_insufficient_credit');
const errWalletConflict = new Counter('err_wallet_conflict');
const errOther = new Counter('err_other');

function createBuyer(runId, i) {
  const email = `loadtest-${runId}-${i}@conduit.test`;
  const reg = http.post(`${BASE_URL}/auth/register`,
    JSON.stringify({ email, password: PASSWORD, full_name: `Load test ${i}` }), { headers: JSON_HEADERS });
  if (reg.status !== 201 && reg.status !== 200) {
    fail(`dang ky ${email} that bai: ${reg.status} ${reg.body}`);
  }
  const token = reg.json('access_token');
  const buy = http.post(`${BASE_URL}/agents/${__ENV.AGENT_ID}/purchases`,
    JSON.stringify({ payment_method: 'mock' }),
    { headers: { ...JSON_HEADERS, Authorization: `Bearer ${token}` } });
  if (buy.status !== 201 && buy.status !== 200) {
    fail(`mua agent cho ${email} that bai: ${buy.status} ${buy.body}`);
  }
  return token;
}

export function setup() {
  const runId = Date.now();
  const n = SCENARIO === 'one_user' ? 1 : MAX_VUS;
  const tokens = [];
  for (let i = 1; i <= n; i++) {
    tokens.push(createBuyer(runId, i));
  }
  return { tokens };
}

export default function (data) {
  const token = data.tokens[(__VU - 1) % data.tokens.length];
  const auth = { ...JSON_HEADERS, Authorization: `Bearer ${token}` };

  const conv = http.post(`${BASE_URL}/conversations`, JSON.stringify({ agent_id: __ENV.AGENT_ID }),
    { headers: auth, tags: { step: 'create_conversation', name: 'POST /conversations' } });
  if (!check(conv, { 'tao hoi thoai 201': (r) => r.status === 201 })) {
    return;
  }

  // SSE: backend gui `event:chunk`, `event:done` (hoac `event:error`) roi dong ket noi, nen
  // http.post doc het luong. Thoi gian cua request nay = mot luot chat tron ven.
  const msg = http.post(`${BASE_URL}/conversations/${conv.json('id')}/messages`,
    JSON.stringify({ content: `load test message from VU ${__VU} iteration ${__ITER}` }),
    {
      headers: { ...auth, Accept: 'text/event-stream' },
      // tag `name` gom URL co id hoi thoai thanh 1 chuoi metric (khong thi k6 canh bao >100.000 chuoi)
      tags: { step: 'send_message', name: 'POST /conversations/{id}/messages' },
      timeout: '60s',
    });

  const body = typeof msg.body === 'string' ? msg.body : '';
  const ok = check(msg, {
    'gui tin nhan 200': (r) => r.status === 200,
    'SSE ket thuc bang done': () => body.includes('event:done'),
  });
  chatTurnMs.add(msg.timings.duration);
  if (ok) {
    chatTurnOk.add(1);
    return;
  }
  chatTurnError.add(1);
  if (body.includes('Insufficient credit')) {
    errInsufficientCredit.add(1);
  } else if (body.includes('updated or deleted by another transaction')) {
    errWalletConflict.add(1);
  } else {
    errOther.add(1);
  }
}
