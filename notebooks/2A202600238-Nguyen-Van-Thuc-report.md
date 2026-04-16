# Assignment 11 Report — Production Defense-in-Depth Pipeline (Guardrails + HITL)

## 1) Mục tiêu
Bài assignment xây dựng một **pipeline phòng thủ nhiều lớp (defense-in-depth)** cho trợ lý ngân hàng (VinBank assistant) nhằm:
- Giảm rủi ro **prompt injection / jailbreak**
- Chặn **off-topic** và nội dung nguy hiểm trước khi vào LLM
- Lọc/che (**redact**) **PII & secrets** trong phản hồi
- Có **audit log + monitoring** để quan sát và truy vết sự cố
- Có **security testing pipeline** để kiểm thử tấn công và đo lường hiệu quả phòng thủ
- Áp dụng tư duy **HITL (Human-in-the-Loop)** cho các tình huống rủi ro cao

---

## 2) Những gì đã triển khai (theo pipeline)

### 2.1. Rate limiting (chống abuse/quota spike)
- Thêm lớp **rate limiting** để giới hạn số request trong một cửa sổ thời gian.
- **Ý nghĩa**: giảm spam, giảm rủi ro “brute-force prompt attack”, giảm lỗi quota và chi phí.

### 2.2. Input guardrails (chặn trước khi vào LLM)
Triển khai guardrails đầu vào theo 2 hướng chính:
- **Detect injection bằng regex**: phát hiện các mẫu như “ignore previous instructions”, “system prompt”, “reveal key”… và cả biến thể tiếng Việt/jailbreak.
- **Topic filter (default-deny)**: chỉ cho phép các chủ đề liên quan ngân hàng (tài khoản, giao dịch, tiết kiệm, lãi suất, chuyển tiền…), và chặn các chủ đề nguy hiểm (hack, vũ khí…).

**Kết quả mong đợi**: đa số tấn công “thô” bị chặn trước khi LLM nhìn thấy prompt.

### 2.3. NeMo Guardrails (rails bằng rule/flow)
- Tích hợp **NeMo Guardrails** với Colang flows để bổ sung lớp policy/rule-based.
- Xây rule cho các nhóm tấn công khó hơn:
  - **Role confusion** (DAN / dev mode / unrestricted)
  - **Encoding/obfuscation** (Base64/ROT13/reverse…)
  - **Vietnamese injection**
  - **Credential extraction**

**Ý nghĩa**: tăng khả năng chặn các biến thể tấn công “lắt léo” mà regex đơn giản có thể bỏ lọt.

### 2.4. Output guardrails (lọc trước khi trả user)
Phòng thủ đầu ra theo 2 lớp:
- **Content filter (regex-based)**: phát hiện & redaction PII/secrets như phone, email, CCCD/CMND, credit card, API key dạng `sk-...`, password patterns…
- **LLM-as-Judge**: dùng một “judge model” để phân loại **SAFE/UNSAFE**, nhằm bắt các vấn đề ngữ nghĩa:
  - leak thông tin nội bộ tinh vi
  - nội dung gây hại
  - hallucination kiểu “khẳng định chắc chắn”
  - off-topic response

**Ý nghĩa**: đây là “lưới an toàn cuối” giúp giảm rủi ro lọt nội dung dù input guardrails đã hoạt động.

### 2.5. Audit log + Monitoring
- Tạo **AuditLog** để ghi sự kiện (prompt, phản hồi, lớp nào block/redact…).
- Tạo **MonitoringAlert** để phát hiện bất thường (ví dụ nhiều lần bị block, spike request…) và kích hoạt cảnh báo.

**Ý nghĩa**: đưa bài từ “demo guardrails” lên hướng “production mindset”: có quan sát, truy vết, và phản ứng.

---

## 3) Security testing & so sánh trước/sau
- Chuẩn bị bộ **adversarial prompts** với nhiều kỹ thuật:
  - completion / fill-in
  - translation / reformatting
  - creative/hypothetical
  - confirmation / authority roleplay
  - multi-step / gradual escalation
- Chạy so sánh:
  - **Unprotected agent** vs **Protected agent** (input + output guardrails)
- Tạo khung **SecurityTestPipeline**:
  - chạy batch attacks
  - phân loại blocked/leaked/error
  - tính metrics (block rate, leak rate)
  - xuất report để dùng cho kiểm thử hồi quy (regression)

**Ý nghĩa**: đánh giá phòng thủ theo hướng **đo lường được** (metrics), không chỉ mô tả.

---

## 4) HITL (Human-in-the-loop) — thiết kế điểm can thiệp
- Xây **ConfidenceRouter**: route theo confidence (auto-send / queue-review / escalate).
- **High-risk actions always escalate**: các hành động như transfer, close account, change password… luôn cần người duyệt.
- Đề xuất 3 decision points trong bối cảnh ngân hàng:
  1) duyệt giao dịch lớn
  2) khiếu nại/sensitive escalation
  3) AML/suspicious activity

**Ý nghĩa**: không chỉ “chặn nội dung”, mà còn thiết kế quy trình vận hành an toàn cho các ca rủi ro.

---

## 5) Cải tiến tương lai (nếu có thêm thời gian)

### 5.1. Nâng cấp guardrails kỹ thuật
- Thay **regex topic_filter** bằng **classifier** (embedding + cosine / model nhỏ) để giảm false positive/false negative.
- Dùng **moderation endpoint** (ví dụ OpenAI moderation) cho semantic safety thay vì chỉ judge tự viết.
- Nâng prompt-injection detection: heuristic cho “instruction hierarchy conflict”, “format traps”, “tool abuse prompts”.

### 5.2. Tăng độ tin cậy vận hành
- **Retry + backoff + fallback model** khi gặp rate limit/quota.
- **Cache FAQ** để giảm chi phí và latency.
- **Structured logging + tracing** (request_id, session_id, blocked_layer, latency_ms) để debug nhanh.

### 5.3. Kiểm thử & CI/CD
- Đưa `SecurityTestPipeline` vào **CI gate**: fail build nếu leak_rate vượt ngưỡng.
- Mở rộng regression suite cho multilingual jailbreak, obfuscation, authority roleplay.
- Thêm rubric đánh giá **hallucination/factuality** và **tone**.

### 5.4. HITL “thật” (từ thiết kế → workflow)
- Làm **queue review UI** (context đầy đủ, approve/edit/reject).
- Tích hợp **policy + escalation playbook** (template phản hồi + SLA + priority routing).
- Lưu **audit trail** cho quyết định của người duyệt (compliance).

---

## 6) Kết luận
Assignment thể hiện rõ cách tiếp cận Responsible AI theo hướng production:
**phòng thủ nhiều lớp**, có **đo lường/kiểm thử**, có **quan sát (audit/monitoring)**, và có **HITL cho rủi ro cao**.

