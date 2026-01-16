# Phase 8: KIS API 완전 대응

## 목표
KIS Open API의 모든 기능을 kis-wrapper에서 사용 가능하도록 완전 대응

## 현재 상태 (v0.3.0)

### 구현 완료
| 모듈 | 기능 |
|------|------|
| auth | 토큰 발급/폐기, WebSocket 키 |
| domestic | price, orderbook, daily, buy, sell, cancel, modify, balance, positions, orders, pending_orders, position, sell_all, cancel_remaining |
| overseas | price, orderbook, daily, buy, sell, cancel, modify, balance, positions, orders, pending_orders, position, sell_all, exchange_rate |
| ws | 실시간 체결/호가 (국내/해외) |

---

## Phase 8.1: 국내주식 확장

### 8.1.1 시세 확장
| API | 함수명 | 설명 |
|-----|--------|------|
| 주식현재가 시세2 | `price_detail` | 상세 시세 (52주 고가/저가 등) |
| 주식현재가 체결 | `ticks` | 체결 틱 데이터 |
| 주식현재가 투자자 | `investor` | 투자자별 매매동향 |
| 주식현재가 회원사 | `broker` | 회원사별 매매동향 |
| 주식당일분봉조회 | `minute` | 당일 분봉 |
| 주식일별분봉조회 | `minute_daily` | 일별 분봉 |
| 주식현재가 당일시간대별체결 | `time_ticks` | 시간대별 체결 |
| 주식현재가 시간외일자별주가 | `after_daily` | 시간외 일별 시세 |
| 주식현재가 시간외시간별체결 | `after_ticks` | 시간외 체결 |
| 국내주식 시간외현재가 | `after_price` | 시간외 현재가 |
| 국내주식 시간외호가 | `after_orderbook` | 시간외 호가 |
| 국내주식 장마감 예상체결가 | `expected_price` | 장마감 예상체결 |
| ETF/ETN 현재가 | `etf_price` | ETF/ETN 시세 |
| ETF 구성종목시세 | `etf_components` | ETF 구성종목 |
| NAV 비교추이 | `etf_nav` | ETF NAV 추이 |

### 8.1.2 주문 확장
| API | 함수명 | 설명 |
|-----|--------|------|
| 주식예약주문 | `reserve_buy`, `reserve_sell` | 예약주문 |
| 주식예약주문정정취소 | `reserve_modify`, `reserve_cancel` | 예약주문 정정/취소 |
| 주식예약주문조회 | `reserve_orders` | 예약주문 조회 |
| 매수가능조회 | `buyable` | 매수가능금액/수량 |
| 매도가능수량조회 | `sellable` | 매도가능수량 |
| 주식주문(신용) | `buy_credit`, `sell_credit` | 신용주문 |
| 신용매수가능조회 | `buyable_credit` | 신용매수가능 |

### 8.1.3 계좌 확장
| API | 함수명 | 설명 |
|-----|--------|------|
| 주식잔고조회_실현손익 | `realized_profit` | 실현손익 |
| 투자계좌자산현황조회 | `asset_summary` | 자산현황 |
| 기간별손익일별합산조회 | `daily_profit` | 일별손익 |
| 기간별매매손익현황조회 | `period_profit` | 기간손익 |
| 기간별계좌권리현황조회 | `rights` | 권리현황 (배당 등) |

---

## Phase 8.2: 국내주식 분석/정보

### 8.2.1 업종/지수
| API | 함수명 | 설명 |
|-----|--------|------|
| 국내업종 현재지수 | `index_price` | 업종지수 현재가 |
| 국내업종 일자별지수 | `index_daily` | 업종지수 일봉 |
| 국내업종 시간별지수 | `index_minute` | 업종지수 분봉 |
| 업종 분봉조회 | `index_minute_detail` | 업종 분봉 상세 |
| 국내업종 구분별전체시세 | `index_all` | 전체 업종지수 |
| 국내주식 예상체결지수 추이 | `expected_index` | 예상체결지수 |
| 변동성완화장치(VI) 현황 | `vi_status` | VI 발동 현황 |
| 국내휴장일조회 | `holidays` | 휴장일 |

### 8.2.2 종목정보
| API | 함수명 | 설명 |
|-----|--------|------|
| 상품기본조회 | `info` | 종목 기본정보 |
| 주식기본조회 | `stock_info` | 주식 상세정보 |
| 국내주식 재무비율 | `financial_ratio` | 재무비율 |
| 국내주식 대차대조표 | `balance_sheet` | 대차대조표 |
| 국내주식 손익계산서 | `income_statement` | 손익계산서 |
| 예탁원정보(배당일정) | `dividend_schedule` | 배당일정 |
| 예탁원정보(공모주청약일정) | `ipo_schedule` | IPO 일정 |
| 국내주식 종목투자의견 | `analyst_opinion` | 애널리스트 의견 |

### 8.2.3 시세분석
| API | 함수명 | 설명 |
|-----|--------|------|
| 종목조건검색 목록조회 | `search_conditions` | 조건검색 목록 |
| 종목조건검색조회 | `search` | 조건검색 실행 |
| 관심종목 그룹조회 | `watchlist_groups` | 관심종목 그룹 |
| 관심종목 시세조회 | `watchlist_prices` | 관심종목 시세 |
| 국내기관_외국인 매매종목가집계 | `institution_foreign` | 기관/외국인 매매 |
| 종목별 투자자매매동향 | `investor_trend` | 투자자 매매동향 |
| 종목별 프로그램매매추이 | `program_trade` | 프로그램매매 |
| 국내주식 신용잔고 일별추이 | `credit_balance` | 신용잔고 |
| 국내주식 공매도 일별추이 | `short_selling` | 공매도 |

### 8.2.4 순위분석
| API | 함수명 | 설명 |
|-----|--------|------|
| 거래량순위 | `rank_volume` | 거래량 순위 |
| 국내주식 등락률 순위 | `rank_change` | 등락률 순위 |
| 국내주식 시가총액 상위 | `rank_market_cap` | 시총 순위 |
| 국내주식 배당률 상위 | `rank_dividend` | 배당률 순위 |
| 국내주식 호가잔량 순위 | `rank_orderbook` | 호가잔량 순위 |

---

## Phase 8.3: 해외주식 확장

### 8.3.1 시세 확장
| API | 함수명 | 설명 |
|-----|--------|------|
| 해외주식 현재가상세 | `price_detail` | 상세 시세 |
| 해외주식 현재체결가 | `ticks` | 체결 틱 |
| 해외주식 체결추이 | `tick_trend` | 체결추이 |
| 해외주식분봉조회 | `minute` | 분봉 |
| 해외지수분봉조회 | `index_minute` | 지수 분봉 |
| 해외주식 종목/지수/환율기간별시세 | `period_price` | 기간별 시세 |
| 해외주식 상품기본정보 | `info` | 종목정보 |
| 해외결제일자조회 | `settlement_dates` | 결제일자 |

### 8.3.2 주문 확장
| API | 함수명 | 설명 |
|-----|--------|------|
| 해외주식 예약주문접수 | `reserve_buy`, `reserve_sell` | 예약주문 |
| 해외주식 예약주문접수취소 | `reserve_cancel` | 예약주문 취소 |
| 해외주식 예약주문조회 | `reserve_orders` | 예약주문 조회 |
| 해외주식 미국주간주문 | `extended_buy`, `extended_sell` | 주간거래 (프리/애프터) |
| 해외주식 미국주간정정취소 | `extended_modify`, `extended_cancel` | 주간거래 정정/취소 |
| 해외주식 매수가능금액조회 | `buyable` | 매수가능금액 |

### 8.3.3 계좌 확장
| API | 함수명 | 설명 |
|-----|--------|------|
| 해외주식 체결기준현재잔고 | `trade_balance` | 체결기준잔고 |
| 해외주식 결제기준잔고 | `settled_balance` | 결제기준잔고 |
| 해외주식 일별거래내역 | `daily_trades` | 일별거래 |
| 해외주식 기간손익 | `period_profit` | 기간손익 |
| 해외증거금 통화별조회 | `margin_by_currency` | 통화별 증거금 |

### 8.3.4 시세분석
| API | 함수명 | 설명 |
|-----|--------|------|
| 해외주식조건검색 | `search` | 조건검색 |
| 해외주식 가격급등락 | `rank_surge` | 급등락 |
| 해외주식 거래량급증 | `rank_volume_surge` | 거래량급증 |
| 해외주식 상승율/하락율 | `rank_change` | 등락률 |
| 해외주식 거래량순위 | `rank_volume` | 거래량순위 |
| 해외주식 시가총액순위 | `rank_market_cap` | 시총순위 |
| 해외주식 기간별권리조회 | `rights` | 권리현황 |
| 해외주식 업종별시세 | `sector_prices` | 업종시세 |

---

## Phase 8.4: 국내선물옵션

### 8.4.1 주문/계좌
| API | 함수명 | 설명 |
|-----|--------|------|
| 선물옵션 주문 | `buy`, `sell` | 선물옵션 주문 |
| 선물옵션 정정취소주문 | `modify`, `cancel` | 정정/취소 |
| 선물옵션 주문체결내역조회 | `orders` | 주문내역 |
| 선물옵션 잔고현황 | `balance` | 잔고 |
| 선물옵션 주문가능 | `buyable` | 주문가능 |
| (야간)선물옵션 * | `night_*` | 야간거래 |

### 8.4.2 시세
| API | 함수명 | 설명 |
|-----|--------|------|
| 선물옵션 시세 | `price` | 현재가 |
| 선물옵션 시세호가 | `orderbook` | 호가 |
| 선물옵션기간별시세 | `daily` | 일봉 |
| 선물옵션 분봉조회 | `minute` | 분봉 |
| 국내옵션전광판 | `option_board` | 옵션전광판 |

---

## Phase 8.5: 해외선물옵션

### 8.5.1 주문/계좌
| API | 함수명 | 설명 |
|-----|--------|------|
| 해외선물옵션 주문 | `buy`, `sell` | 주문 |
| 해외선물옵션 정정취소주문 | `modify`, `cancel` | 정정/취소 |
| 해외선물옵션 당일주문내역조회 | `orders` | 주문내역 |
| 해외선물옵션 미결제내역조회 | `positions` | 포지션 |
| 해외선물옵션 주문가능조회 | `buyable` | 주문가능 |
| 해외선물옵션 예수금현황 | `deposit` | 예수금 |

### 8.5.2 시세
| API | 함수명 | 설명 |
|-----|--------|------|
| 해외선물종목현재가 | `futures_price` | 선물 현재가 |
| 해외선물 호가 | `futures_orderbook` | 선물 호가 |
| 해외선물 분봉조회 | `futures_minute` | 선물 분봉 |
| 해외옵션종목현재가 | `options_price` | 옵션 현재가 |
| 해외옵션 호가 | `options_orderbook` | 옵션 호가 |

---

## Phase 8.6: 장내채권

### 8.6.1 주문/계좌
| API | 함수명 | 설명 |
|-----|--------|------|
| 장내채권 매수주문 | `buy` | 매수 |
| 장내채권 매도주문 | `sell` | 매도 |
| 장내채권 정정취소주문 | `modify`, `cancel` | 정정/취소 |
| 장내채권 주문체결내역 | `orders` | 주문내역 |
| 장내채권 잔고조회 | `balance` | 잔고 |
| 장내채권 매수가능조회 | `buyable` | 매수가능 |

### 8.6.2 시세
| API | 함수명 | 설명 |
|-----|--------|------|
| 장내채권현재가(시세) | `price` | 현재가 |
| 장내채권현재가(호가) | `orderbook` | 호가 |
| 장내채권현재가(체결) | `ticks` | 체결 |
| 장내채권 기간별시세 | `daily` | 일봉 |
| 장내채권 발행정보 | `info` | 채권정보 |

---

## Phase 8.7: ELW

### 8.7.1 시세
| API | 함수명 | 설명 |
|-----|--------|------|
| ELW 현재가 시세 | `price` | 현재가 |
| ELW 민감도 순위 | `rank_sensitivity` | 민감도순위 |
| ELW 종목검색 | `search` | 종목검색 |
| ELW 투자지표추이 | `indicators` | 투자지표 |

---

## Phase 8.8: WebSocket 확장

### 8.8.1 국내 실시간
| TR ID | 설명 | 상태 |
|-------|------|------|
| H0STCNT0 | 국내주식 실시간체결가 | ✅ 완료 |
| H0STASP0 | 국내주식 실시간호가 | ✅ 완료 |
| H0STCNI0 | 실시간체결통보 | ✅ 완료 |
| H0STCNI9 | 실시간체결통보(모의) | 추가 |
| H0STMCO0 | 장운영정보 | 추가 |
| H0STPGM0 | 프로그램매매 | 추가 |
| H0STMBI0 | 회원사 | 추가 |
| H0STIMC0 | 예상체결 | 추가 |

### 8.8.2 해외 실시간
| TR ID | 설명 | 상태 |
|-------|------|------|
| HDFSCNT0 | 해외주식 실시간체결가 | ✅ 완료 |
| HDFSASP0 | 해외주식 실시간호가 | 추가 |
| H0GSCNI0 | 해외주식 체결통보 | 추가 |
| HDFSCNI0 | 해외주식 체결통보(모의) | 추가 |

### 8.8.3 선물옵션 실시간
| TR ID | 설명 |
|-------|------|
| H0IFASP0 | 지수선물 호가 |
| H0IFCNT0 | 지수선물 체결 |
| H0IOACP0 | 지수옵션 호가 |
| H0IOCNT0 | 지수옵션 체결 |
| H0SFCNI0 | 선물옵션 체결통보 |

---

## 모듈 구조

```
kis/
├── __init__.py
├── auth.py              # 기존
├── client.py            # 기존
├── async_client.py      # 기존
├── errors.py            # 기존
├── types.py             # 기존 (확장)
├── ws.py                # 기존 (확장)
│
├── domestic/            # 국내주식 (분리)
│   ├── __init__.py
│   ├── quote.py         # 시세
│   ├── order.py         # 주문
│   ├── account.py       # 계좌
│   ├── index.py         # 업종/지수
│   ├── info.py          # 종목정보
│   └── analysis.py      # 분석/순위
│
├── overseas/            # 해외주식 (분리)
│   ├── __init__.py
│   ├── quote.py
│   ├── order.py
│   ├── account.py
│   └── analysis.py
│
├── futures/             # 국내선물옵션 (신규)
│   ├── __init__.py
│   ├── quote.py
│   ├── order.py
│   └── account.py
│
├── global_futures/      # 해외선물옵션 (신규)
│   ├── __init__.py
│   ├── quote.py
│   ├── order.py
│   └── account.py
│
├── bond/                # 장내채권 (신규)
│   ├── __init__.py
│   ├── quote.py
│   ├── order.py
│   └── account.py
│
├── elw/                 # ELW (신규)
│   ├── __init__.py
│   └── quote.py
│
├── calc.py              # 기존
├── snapshot.py          # 기존
└── utils.py             # 기존
```

---

## 구현 순서

### Sprint 1: 국내주식 완성 (8.1 + 8.2)
- [ ] 분봉 (minute, minute_daily)
- [ ] 예약주문
- [ ] 매수/매도 가능 조회
- [ ] 업종지수
- [ ] 휴장일
- [ ] 종목정보/재무
- [ ] 조건검색
- [ ] 순위분석

### Sprint 2: 해외주식 완성 (8.3)
- [ ] 분봉
- [ ] 예약주문
- [ ] 미국 주간거래
- [ ] 체결/결제 기준잔고
- [ ] 조건검색
- [ ] 순위분석

### Sprint 3: 선물옵션 (8.4 + 8.5)
- [ ] 국내선물옵션 주문/시세
- [ ] 야간거래
- [ ] 해외선물옵션 주문/시세

### Sprint 4: 채권/ELW (8.6 + 8.7)
- [ ] 장내채권 주문/시세
- [ ] ELW 시세

### Sprint 5: WebSocket 확장 (8.8)
- [ ] 추가 TR ID 지원
- [ ] 선물옵션 실시간

---

## 완료 조건
- [ ] KIS API 문서의 모든 엔드포인트 대응
- [ ] 각 함수 docstring + type hints
- [ ] 테스트 커버리지 유지
- [ ] README 업데이트
