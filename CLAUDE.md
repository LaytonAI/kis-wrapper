# InvestAI Project Rules
절대 사용자의 입맛에 맞춰 답변하지 말고 진실을 추구하라.

## 디버깅 원칙

1. **가설 세우기 전 데이터 먼저**
   - 추측하지 말고 로그/DB부터 확인
   - GCP 크론 로그: `~/investai/logs/cron_*.log`
   - 관련 테이블: recommendations, order_maps, executions

2. **데이터 흐름 순서대로 추적**
   - AI 추천 → recommendations 저장 → 주문 실행 → 체결 동기화
   - 각 단계의 입력/출력 값을 순차적으로 검증

3. **DB 수정 금지**
   - 원인 분석 완료 후 사용자 승인 없이 절대 수정하지 말 것
   - 분석 결과와 수정 계획을 먼저 제시

## 실전투자 안전 규칙

**실전투자(REAL) 계좌에서 주문 실행 시 반드시 사용자 승인 필요.**
**모의투자(VIRTUAL)는 승인 없이 실행 가능.**

### 사용자 승인 필수 (실전투자만)

실전투자 계좌(mode=REAL)에서 다음 명령어 실행 전 반드시 승인 요청:

- `*_trader.py buy` - 매수 주문
- `*_trader.py sell` - 매도 주문

### 실행 전 확인 절차

1. 계좌 모드 확인 (DB에서 account의 mode 필드)
2. **REAL인 경우**: 사용자에게 승인 요청 후 실행
3. **VIRTUAL인 경우**: 바로 실행 가능

### 승인 없이 실행 가능

- 모의투자(VIRTUAL) 계좌의 모든 주문
- `sync_executions.py` - 체결 동기화
- `snapshot_account.py` - 계좌 스냅샷
- 조회 명령어

## Supabase MCP 설정

**Project ID: `qbzuqtyvuocpqfmolfcl`** (invest-ai)

Supabase MCP 사용 시 반드시 위 project_id를 사용할 것.
- ❌ project_id를 추측하거나 생성하지 말 것
- ✅ 항상 `list_projects`로 확인하거나 위 ID 사용

## KIS API 규칙

### 총자산/잔고 조회 API

#### 국내주식
| 항목 | 값 |
|------|-----|
| 엔드포인트 | `/uapi/domestic-stock/v1/trading/inquire-balance` |
| TR_ID (실전) | `TTTC8434R` |
| TR_ID (모의) | `VTTC8434R` |
| 함수 | `api/kis.py` → `get_balance()` |

#### 해외주식 - 잔고조회
| 항목 | 값 |
|------|-----|
| 엔드포인트 | `/uapi/overseas-stock/v1/trading/inquire-balance` |
| TR_ID (실전) | `TTTS3012R` |
| TR_ID (모의) | `VTTS3012R` |
| 함수 | `api/kis.py` → `get_overseas_balance()` |

#### 해외주식 - 정확한 잔고 (환율 포함)
| 항목 | 값 |
|------|-----|
| 엔드포인트 | `/uapi/overseas-stock/v1/trading/inquire-present-balance` |
| TR_ID (실전) | `CTRP6504R` |
| TR_ID (모의) | `VTRP6504R` |
| 함수 | `api/kis.py` → `_get_actual_overseas_cash()` |

#### 해외주식 - 결제기준잔고 (실전 전용)
| 항목 | 값 |
|------|-----|
| 엔드포인트 | `/uapi/overseas-stock/v1/trading/inquire-paymt-stdr-balance` |
| TR_ID (실전) | `CTRP6010R` |
| 함수 | `api/kis.py` → `get_paymt_stdr_balance()` |

### API 사용 원칙
- 새 API 호출 전 반드시 `api/kis.py` 기존 구현 확인
- TR_ID 추측 금지 - 위 테이블 또는 기존 코드 참조
- 실전/모의 TR_ID 구분 필수

### 국내주식 수수료 (2026-01-16 측정, 모의투자)

| 구분 | 측정값 | 계산식 |
|------|--------|--------|
| 매수 수수료 | **0.0135%** | `체결가 × 0.000135` |
| 매도 수수료+세금 | **0.2138%** | `체결가 × 0.002138` |

**측정 결과:**
- 매수 148,300원 → 차감 148,320원 (수수료 20원, 오차 0원)
- 매도 148,300원 → 입금 147,983원 (수수료+세금 317원)

**수수료 계산 공식:**
```python
from decimal import Decimal

BUY_FEE_RATE = Decimal('0.000135')   # 0.0135%
SELL_FEE_RATE = Decimal('0.002138')  # 0.2138%

# 매수 비용
buy_cost = buy_price + int(Decimal(buy_price) * BUY_FEE_RATE)

# 매도 수령액
sell_received = sell_price - int(Decimal(sell_price) * SELL_FEE_RATE)
```

**거래 내역 기반 자산 역산:**
```
현재자산 = 초기자산 - Σ(매수가 × 1.000135) + Σ(매도가 × 0.997862)
```

### 총자산 조회 코드 (로컬에서 실행 가능)

```python
# 국내주식 모의계좌 총자산 조회
from db.database import Database
from api.kis import KISClient

db = Database()
account = db.supabase.table('accounts').select('*').eq('account_number', '{계좌번호}').single().execute().data

# mode에 따라 url_base 설정
if account['mode'] == 'VIRTUAL':
    account['url_base'] = 'https://openapivts.koreainvestment.com:29443'
else:
    account['url_base'] = 'https://openapi.koreainvestment.com:9443'

api = KISClient(account)
balance = api.get_balance()

# 결과: balance['holdings'] = 보유종목 리스트, balance['cash_balance'] = 예수금, balance['total_eval'] = 총평가
print(balance)
```

**주요 필드:**
- `holdings`: 보유종목 리스트 (symbol, name, qty, avg_price, current_price, eval_amt)
- `cash_balance`: 현금 (`prvs_rcdl_excc_amt`)
- `total_eval`: 총평가금액 (`tot_evlu_amt`)

### 국내주식 잔고 응답 필드 상세 (output2)

| 필드 | 설명 |
|------|------|
| `prvs_rcdl_excc_amt` | **현금** (실시간 반영, 매수/매도 즉시 차감/증가) |
| `nass_amt` | 순자산 (현금 + 주식평가액) |
| `tot_evlu_amt` | 총자산 (현금 + 주식평가액) |
| `scts_evlu_amt` | 주식평가금액 |
| `dnca_tot_amt` | 결제 완료 예수금 (T+2 기준, 당일 매수 미반영) |

**모의투자 국내주식 현금 조회:**
- 현금 → `prvs_rcdl_excc_amt` (실시간)
- 총자산 → `tot_evlu_amt`
- 주식평가 → `scts_evlu_amt`

### 가상계좌 잔고 동기화 프로세스

KIS API 잔고와 DB 가상계좌 잔고를 일치시키는 절차:

**1단계: KIS API 잔고 조회**
- 국내주식: `prvs_rcdl_excc_amt` (현금), `tot_evlu_amt` (총자산)
- 해외주식: `ovrs_ord_psbl_amt` (현금)

**2단계: DB 가상계좌 합계 조회**
```sql
SELECT SUM(cash_balance) FROM virtual_accounts 
WHERE account_id = {account_id} AND currency = '{KRW|USD}'
```

**3단계: 차이 계산**
```
차이 = KIS 잔고 - VA 합계
```

**4단계: 잔고 조정 (KIS 기준으로 맞춤)**
1. 각 가상계좌의 `cash_balance`를 `initial_balance`로 리셋
2. 리셋 후 합계와 KIS 잔고의 차이 계산
3. **테스트 계좌**에서 오차 금액 가감하여 조정
   - KRW: `KR테스트계좌` 또는 `KR 모의투자`
   - USD: `테스트용 가상계좌` 또는 `워렌버핏 추종자`

**주의사항:**
- 동기화 전 보유주식 전량 매도 권장 (포지션 있으면 계산 복잡)
- `virtual_positions` 테이블도 함께 정리 필요
- 동기화 후 KIS vs VA 합계 재확인

## GCP 실행 규칙

### VM 정보
- **VM 이름**: `invest-ai`
- **Zone**: `asia-northeast3-a`
- **프로젝트 경로**: `~/investai`

### SSH 접속
```bash
gcloud compute ssh invest-ai --zone=asia-northeast3-a
```

### VM에서 스크립트 실행
```bash
# 1. SSH 접속
gcloud compute ssh invest-ai --zone=asia-northeast3-a

# 2. 프로젝트 이동 + 가상환경 활성화
cd ~/investai && source venv/bin/activate

# 3. 스크립트 실행
python traders/high_reliability_trader.py ai-buy --account {계좌번호}
```

### 또는 한 줄로 실행
```bash
gcloud compute ssh invest-ai --zone=asia-northeast3-a --command="cd ~/investai && source venv/bin/activate && python {스크립트} {인자}"
```

### 배포 (로컬에서)
```bash
./deploy.sh        # API만
./deploy.sh --ws   # API + WebSocket
```

### 서비스 관리 (VM에서)
```bash
sudo systemctl status investai          # 상태 확인
sudo systemctl restart investai         # 재시작
sudo journalctl -u investai -f          # 로그
```

### 주의사항
- GCP 실행 요청 시 반드시 VM SSH 접속 후 실행
- 로컬에서 직접 trader 스크립트 실행 금지
- `deploy.config` 설정 참조
