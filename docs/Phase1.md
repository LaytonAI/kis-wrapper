# Phase 1: 프로젝트 초기화 + 문서 수집

## 목표
- 프로젝트 구조 생성
- KIS 공식 Excel 문서 수집 및 정리
- 개발 환경 설정

## 1.1 pyproject.toml

```toml
[project]
name = "kis"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "httpx",          # HTTP (sync/async)
    "websockets",     # WebSocket
    "pycryptodome",   # AES 복호화
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio", "ruff", "mypy"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## 1.2 디렉토리 생성

```bash
mkdir -p kis tests/fixtures docs examples
touch kis/__init__.py
touch kis/auth.py kis/client.py kis/ws.py
touch kis/domestic.py kis/overseas.py
touch kis/types.py kis/utils.py
```

## 1.3 KIS Excel 문서 수집

### 다운로드 위치
- https://apiportal.koreainvestment.com/apiservice
- "전체 API 문서 (Excel) 다운로드" 클릭

### 정리할 내용 (docs/ 폴더)
- `docs/domestic_stock.md` - 국내주식 API
- `docs/overseas_stock.md` - 해외주식 API
- `docs/realtime.md` - 실시간 TR ID
- `docs/error_codes.md` - 에러 코드

### Excel 파싱 스크립트 (선택)
```python
# scripts/parse_excel.py
import openpyxl

def parse_api_spec(excel_path: str) -> dict:
    """Excel에서 API 스펙 추출"""
    wb = openpyxl.load_workbook(excel_path)
    # ... 파싱 로직
    return specs
```

## 1.4 환경 변수 템플릿

```bash
# .env.example
KIS_APP_KEY=your_app_key
KIS_APP_SECRET=your_app_secret
KIS_ACCOUNT=12345678-01
KIS_HTS_ID=your_hts_id

# 모의투자용 (별도 키 필요시)
KIS_PAPER_APP_KEY=
KIS_PAPER_APP_SECRET=
```

## 1.5 .gitignore

```
__pycache__/
*.pyc
.env
.venv/
*.egg-info/
dist/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

## 완료 조건
- [x] pyproject.toml 생성
- [x] 디렉토리 구조 생성
- [ ] KIS Excel 문서 다운로드 (manual)
- [ ] docs/ 폴더에 API 스펙 정리 (manual)
- [x] .env.example 생성
- [x] uv sync 성공
- [x] .claude/rules 설정
- [x] /lint skill 생성
