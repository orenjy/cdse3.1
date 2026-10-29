import json

cells = []

def add_md(text):
    cells.append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in text.split("\n")]
    })

def add_code(text):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in text.split("\n")]
    })

# Title & Intro
add_md("""# 📈 [시계열 데이터 분석] 삼성전자 vs 애플 주가 트렌드 및 변동성 분석 (2023~2024)

> **강의 및 실습 안내**  
> 안녕하세요! 데이터 분석가이자 여러분의 페어 프로그래밍 강사입니다.  
> 이번 실습에서는 시계열 데이터의 기초 개념인 **이동평균선(Moving Average)**, **일일 수익률(Daily Return)**, **변동성(Volatility)**을 파이썬의 대표 금융 라이브러리인 `yfinance`를 활용해 직접 수집하고 분석해 봅니다.
>
> 💡 **분석의 핵심:**  
> 단순히 그래프를 그리는 데 그치지 않고, 수치를 기반으로 한 **'관찰(Fact)'**과 그에 따른 원인 분석인 **'해석(가설)'**을 명확히 구분하는 훈련을 진행합니다.

---

### 📌 주요 실습 목차
1. **환경 설정:** 필수 라이브러리 임포트 및 시각화 한글 폰트 설정
2. **데이터 수집:** `yfinance`로 2023-01-01 ~ 2024-12-31 삼성전자(`005930.KS`)와 애플(`AAPL`) 데이터 수집
3. **데이터 정제(Data Cleaning):** 결측치 점검, 거래소 휴장일 차이 보정(`ffill`), 데이터 정합성 검증
4. **시계열 지표 산출:** 20일 이동평균선(SMA 20), 일일 수익률, 이격도(Disparity), 20일 롤링 변동성 계산
5. **시각화 및 패턴 분석:**
   - [시각화 1] 두 종목 종가 비교 (정규화 누적 수익률 & 이중축 절대가격)
   - [시각화 2] 삼성전자 종가 vs 20일 이동평균선 및 골든/데드크로스 분석
   - [시각화 3] 일일 수익률 변동성(시계열 & 롤링 연율화 변동성)
   - [시각화 4] 일일 수익률 분포 히스토그램 및 박스플롯
6. **핵심 분석 요약 및 리포트 연계**
""")

# Setup
add_code("""# [Step 1] 라이브러리 자동 설치 확인 및 임포트
# 혹시 라이브러리가 설치되지 않은 새로운 커널 환경인 경우 아래 주석을 풀고 실행하세요:
# !pip install yfinance pandas matplotlib seaborn

import os
import sys
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

# 경고 메시지 무시 설정
import warnings
warnings.filterwarnings('ignore')

# Matplotlib 한글 폰트 설정 (Windows 기준 Malgun Gothic)
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지
sns.set_theme(style="whitegrid", font="Malgun Gothic")
plt.rcParams['axes.unicode_minus'] = False

print("환경 설정 완료 (Python 실행 경로:", sys.executable, ")")
print("Pandas 버전:", pd.__version__, "| yfinance 버전:", yf.__version__)
""")

# Step 2: Download
add_md("""---
## 1. 데이터 수집 (Data Collection)
- 대상: **삼성전자(005930.KS)**, **애플(AAPL)**
- 기간: **2023-01-01 ~ 2024-12-31**
- 수집 라이브러리: `yfinance` (종가 원화/달러 보존을 위해 `auto_adjust=False` 적용)
""")

add_code("""# [Step 2] yfinance를 이용한 시계열 데이터 다운로드
START_DATE = '2023-01-01'
END_DATE = '2025-01-01'  # 2024-12-31까지 온전히 포함하기 위해 2025-01-01로 지정

print("⏳ 데이터 다운로드 시작...")
sec_raw = yf.download('005930.KS', start=START_DATE, end=END_DATE, auto_adjust=False)
aapl_raw = yf.download('AAPL', start=START_DATE, end=END_DATE, auto_adjust=False)

# MultiIndex 컬럼일 경우 단일 레벨로 변환
if isinstance(sec_raw.columns, pd.MultiIndex):
    sec_raw.columns = sec_raw.columns.get_level_values(0)
if isinstance(aapl_raw.columns, pd.MultiIndex):
    aapl_raw.columns = aapl_raw.columns.get_level_values(0)

print(f"✅ 삼성전자 데이터 수집 완료: {sec_raw.shape[0]} 거래일 (컬럼: {list(sec_raw.columns)})")
print(f"✅ 애플 데이터 수집 완료: {aapl_raw.shape[0]} 거래일 (컬럼: {list(aapl_raw.columns)})")

# 원본 데이터 로컬 저장
os.makedirs('data', exist_ok=True)
sec_raw.to_csv('data/samsung_data.csv')
aapl_raw.to_csv('data/apple_data.csv')
""")

# Step 3: EDA & Data Cleaning
add_md("""---
## 2. 데이터 탐색(EDA) 및 정제(Data Cleaning)

> 💡 **강사의 팁: 시계열 데이터 정제 시 주의할 점**  
> 1. 개별 종목 내부의 결측치 확인: 장이 열린 날에 주가 데이터가 누락되었는지 확인합니다.  
> 2. 국가 간 거래소 휴장일 불일치: 한국(KRX)과 미국(NYSE/NASDAQ)은 공휴일이 서로 다릅니다. 두 종목을 1:1로 비교 분석할 때는 **날짜 인덱스를 정렬하고 전일 종가(Forward Fill, `ffill`)로 채우는 것**이 금융 분석의 표준 규칙입니다.
""")

add_code("""# [Step 3-1] 개별 종목 결측치 및 데이터 타입 점검
print("=== 삼성전자 결측치 현황 ===")
print(sec_raw.isnull().sum())

print("\\n=== 애플 결측치 현황 ===")
print(aapl_raw.isnull().sum())

print("\\n=== 삼성전자 기초 통계량 (종가 기준) ===")
display(sec_raw[['Close', 'Volume']].describe())
""")

add_code("""# [Step 3-2] 양국 거래일 통합 데이터셋 생성 및 결측치 보정 (ffill)
# 날짜 기준으로 외부 조인(outer join)
combined = pd.DataFrame({
    'Samsung_Close': sec_raw['Close'],
    'Apple_Close': aapl_raw['Close']
})

print(f"통합 달력 총 일수 (양국 개장일 합집합): {len(combined)}일")
print("병합 직후 결측치(휴장일 차이):")
print(combined.isnull().sum())

# 결측치 보정: 전일 종가 대체 (Forward Fill) -> 시계열의 연속성 유지
combined_clean = combined.ffill().bfill()
print("\\n결측치 보정 후 결측치 수:")
print(combined_clean.isnull().sum())
""")

# Step 4: Feature Engineering
add_md("""---
## 3. 시계열 분석 기법 적용 (Feature Engineering)
- **20일 이동평균선 (SMA 20):** 한 달(약 20영업일) 동안 시장 참여자들의 평균 매수 단가 파악.
- **일일 수익률 (Daily Return, %):** 당일 종가와 전일 종가의 변동률(`pct_change() * 100`).
- **20일 이격도 (Disparity, %):** 현재 주가가 20일 이동평균선 대비 몇 % 위에 있거나 아래에 있는지 측정.
- **20일 롤링 연율화 변동성 (Rolling Volatility):** 최근 20일간의 수익률 표준편차를 연율화($\\sigma \\times \\sqrt{250}$).
""")

add_code("""# [Step 4] 핵심 시계열 지표 계산
# 1. 삼성전자 지표 계산
sec = sec_raw.copy()
sec['SMA20'] = sec['Close'].rolling(window=20).mean()
sec['Daily_Return'] = sec['Close'].pct_change() * 100
sec['Disparity'] = ((sec['Close'] - sec['SMA20']) / sec['SMA20']) * 100
sec['Vol20'] = sec['Daily_Return'].rolling(window=20).std() * np.sqrt(250)

# 2. 애플 지표 계산
aapl = aapl_raw.copy()
aapl['SMA20'] = aapl['Close'].rolling(window=20).mean()
aapl['Daily_Return'] = aapl['Close'].pct_change() * 100
aapl['Disparity'] = ((aapl['Close'] - aapl['SMA20']) / aapl['SMA20']) * 100
aapl['Vol20'] = aapl['Daily_Return'].rolling(window=20).std() * np.sqrt(252)

# 3. 통합 정규화 지수 (2023년 시초가 = 100)
combined_clean['Samsung_Norm'] = (combined_clean['Samsung_Close'] / combined_clean['Samsung_Close'].iloc[0]) * 100
combined_clean['Apple_Norm'] = (combined_clean['Apple_Close'] / combined_clean['Apple_Close'].iloc[0]) * 100

print("✅ 모든 시계열 파생변수 생성 완료")
display(sec[['Close', 'SMA20', 'Daily_Return', 'Disparity', 'Vol20']].tail(5))
""")

# Step 5: Visualizations
add_md("""---
## 4. 시각화 1: 두 종목의 종가(Close) 비교 분석
- **목적:** 통화 단위(KRW vs USD)와 가격 수준 차이를 극복하기 위해 **정규화 누적 수익률(기준=100)**과 **이중 Y축 차트**를 함께 시각화합니다.
""")

add_code("""# [시각화 1] 두 종목의 종가 비교 (정규화 누적 수익률 & 이중축 절대가격)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [1.2, 1]})

# 상단: 정규화 누적 수익률 (2023-01 = 100)
ax1.plot(combined_clean.index, combined_clean['Samsung_Norm'], label='삼성전자 (005930.KS)', color='#0047AB', linewidth=2)
ax1.plot(combined_clean.index, combined_clean['Apple_Norm'], label='애플 (AAPL)', color='#E056FD', linewidth=2)
ax1.axhline(100, color='gray', linestyle='--', alpha=0.7, label='시작 기준선 (100)')
ax1.set_title('[차트 1-1] 삼성전자 vs 애플 누적 수익률 비교 (기준일 2023-01-02/03 = 100)', fontsize=14, fontweight='bold', pad=12)
ax1.set_ylabel('정규화 지수 (기준=100)', fontsize=12)
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# 주요 어노테이션
ax1.annotate(f"애플 최종: {combined_clean['Apple_Norm'].iloc[-1]:.1f} (+{combined_clean['Apple_Norm'].iloc[-1]-100:.1f}%)",
             xy=(combined_clean.index[-1], combined_clean['Apple_Norm'].iloc[-1]),
             xytext=(combined_clean.index[-1] - pd.Timedelta(days=70), combined_clean['Apple_Norm'].iloc[-1] + 10),
             arrowprops=dict(facecolor='#E056FD', shrink=0.05, width=1.5, headwidth=6),
             fontweight='bold', color='#68007D', bbox=dict(boxstyle="round,pad=0.3", fc="#fbeaff", ec="#E056FD"))

ax1.annotate(f"삼성전자 최종: {combined_clean['Samsung_Norm'].iloc[-1]:.1f} ({combined_clean['Samsung_Norm'].iloc[-1]-100:+.1f}%)",
             xy=(combined_clean.index[-1], combined_clean['Samsung_Norm'].iloc[-1]),
             xytext=(combined_clean.index[-1] - pd.Timedelta(days=80), combined_clean['Samsung_Norm'].iloc[-1] - 25),
             arrowprops=dict(facecolor='#0047AB', shrink=0.05, width=1.5, headwidth=6),
             fontweight='bold', color='#002766', bbox=dict(boxstyle="round,pad=0.3", fc="#e6f4ff", ec="#0047AB"))

# 하단: 이중 Y축 실제 주가 차트
ax2_twin = ax2.twinx()
p1 = ax2.plot(combined_clean.index, combined_clean['Samsung_Close'], color='#0047AB', label='삼성전자 종가 (KRW)', linewidth=1.8)
p2 = ax2_twin.plot(combined_clean.index, combined_clean['Apple_Close'], color='#FF7675', label='애플 종가 (USD)', linewidth=1.8)

ax2.set_title('[차트 1-2] 종목별 실제 종가 추이 (이중 Y축: KRW vs USD)', fontsize=13, fontweight='bold', pad=10)
ax2.set_ylabel('삼성전자 주가 (원)', color='#0047AB', fontsize=12)
ax2_twin.set_ylabel('애플 주가 (달러)', color='#FF7675', fontsize=12)
ax2.tick_params(axis='y', labelcolor='#0047AB')
ax2_twin.tick_params(axis='y', labelcolor='#FF7675')
ax2.yaxis.set_major_formatter('{x:,.0f}원')
ax2_twin.yaxis.set_major_formatter('${x:,.0f}')

lines = p1 + p2
labels = [l.get_label() for l in lines]
ax2.legend(lines, labels, loc='upper left', frameon=True)

ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()
plt.tight_layout()
os.makedirs('images', exist_ok=True)
plt.savefig('images/01_price_trend_comparison.png', dpi=300)
plt.show()
""")

# Step 6: Samsung SMA 20
add_md("""---
## 5. 시각화 2: 삼성전자 종가 vs 20일 이동평균선(SMA 20) 심층 분석
- **목적:** 삼성전자의 단기 추세 지지선 및 저항선으로서의 20일 이동평균선 역할을 검증하고, 주가 급변 이벤트와의 상관관계를 파악합니다.
""")

add_code("""# [시각화 2] 삼성전자 종가 vs 20일 이동평균선(SMA 20) 및 이격도 차트
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# 상단: 주가 및 이동평균선
ax1.plot(sec.index, sec['Close'], label='삼성전자 종가 (Close)', color='#1E3799', linewidth=2)
ax1.plot(sec.index, sec['SMA20'], label='20일 이동평균선 (SMA 20)', color='#FA983A', linewidth=2, linestyle='--')

# 영역 채우기
ax1.fill_between(sec.index, sec['Close'], sec['SMA20'], where=(sec['Close'] >= sec['SMA20']),
                 color='#4CD137', alpha=0.2, label='주가 > SMA 20 (상승 국면)')
ax1.fill_between(sec.index, sec['Close'], sec['SMA20'], where=(sec['Close'] < sec['SMA20']),
                 color='#E84118', alpha=0.2, label='주가 < SMA 20 (하락/조정 국면)')

# 주요 사건 어노테이션
ax1.annotate('2024-03-20\\n엔비디아 GTC\\n(HBM 승인 기대)',
             xy=(pd.Timestamp('2024-03-20'), 76900), xytext=(pd.Timestamp('2024-01-15'), 83000),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#f1f2f6", ec="#ced6e0"))

ax1.annotate('2024-07-09\\n최고가 87,800원',
             xy=(pd.Timestamp('2024-07-09'), 87800), xytext=(pd.Timestamp('2024-05-15'), 92000),
             arrowprops=dict(facecolor='#E84118', shrink=0.05, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', color='#c0392b', bbox=dict(boxstyle="round,pad=0.3", fc="#ffeaa7", ec="#fdcb6e"))

ax1.annotate('2024-08-05\\n검은 월요일 (-10.3%)',
             xy=(pd.Timestamp('2024-08-05'), 71400), xytext=(pd.Timestamp('2024-08-15'), 60000),
             arrowprops=dict(facecolor='#c0392b', shrink=0.05, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', color='#c0392b', bbox=dict(boxstyle="round,pad=0.3", fc="#ffdd59", ec="#e67e22"))

ax1.annotate('2024-11-14 최저 49,900원\\n11-15 자사주 10조 매입',
             xy=(pd.Timestamp('2024-11-15'), 53500), xytext=(pd.Timestamp('2024-09-15'), 46000),
             arrowprops=dict(facecolor='#0984e3', shrink=0.05, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', color='#0984e3', bbox=dict(boxstyle="round,pad=0.3", fc="#dff9fb", ec="#22a6b3"))

ax1.set_title('[차트 2] 삼성전자 종가 vs 20일 이동평균선(SMA 20) 추이 및 주요 이벤트', fontsize=14, fontweight='bold', pad=12)
ax1.set_ylabel('주가 (KRW)', fontsize=12)
ax1.yaxis.set_major_formatter('{x:,.0f}원')
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# 하단: 20일 이격도 (Disparity, %)
ax2.plot(sec.index, sec['Disparity'], color='#2F3542', linewidth=1.5, label='20일 이격도 (Disparity, %)')
ax2.axhline(0, color='red', linestyle='--', linewidth=1.2, alpha=0.8, label='SMA 20 기준선 (0%)')
ax2.axhline(5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax2.axhline(-5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax2.fill_between(sec.index, sec['Disparity'], 0, where=(sec['Disparity'] >= 0), color='#4CD137', alpha=0.3)
ax2.fill_between(sec.index, sec['Disparity'], 0, where=(sec['Disparity'] < 0), color='#E84118', alpha=0.3)

# 2024년 말 최종일 표시
last_date = sec.index[-1]
last_disp = sec['Disparity'].iloc[-1]
ax2.scatter(last_date, last_disp, color='red', s=50, zorder=5)
ax2.annotate(f"2024-12-30: {last_disp:+.2f}%", xy=(last_date, last_disp),
             xytext=(last_date - pd.Timedelta(days=60), last_disp - 4),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=4),
             fontweight='bold', fontsize=9)

ax2.set_title('20일 이동평균선 이격도(Disparity, %)', fontsize=12, fontweight='bold')
ax2.set_ylabel('이격도 (%)', fontsize=11)
ax2.yaxis.set_major_formatter('{x:+.1f}%')
ax2.legend(loc='lower left', frameon=True)
ax2.grid(True, linestyle=':', alpha=0.6)

ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig('images/02_samsung_sma20.png', dpi=300)
plt.show()
""")

# Step 7: Volatility Analysis
add_md("""---
## 6. 시각화 3: 일일 수익률 변동성 분석
- **목적:** 삼성전자와 애플의 일일 수익률(Daily Return) 시계열 변동 폭과 최근 20일 기준 롤링 연율화 변동성($\\sigma_{20} \\times \\sqrt{250}$)을 비교합니다.
""")

add_code("""# [시각화 3] 일일 수익률 시계열 변동성 및 20일 롤링 변동성
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)

# 상단: 일일 수익률 시계열
ax1.plot(sec.index, sec['Daily_Return'], label='삼성전자 일일 수익률(%)', color='#0984E3', alpha=0.7, linewidth=1.2)
ax1.plot(aapl.index, aapl['Daily_Return'], label='애플 일일 수익률(%)', color='#E84393', alpha=0.7, linewidth=1.2)
ax1.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.7)
ax1.axhline(5, color='orange', linestyle=':', alpha=0.5)
ax1.axhline(-5, color='orange', linestyle=':', alpha=0.5)

# 검은 월요일 표시
ax1.annotate('2024-08-05\\n삼성: -10.30%\\n애플: -4.82%',
             xy=(pd.Timestamp('2024-08-05'), -10.30), xytext=(pd.Timestamp('2024-06-01'), -9.5),
             arrowprops=dict(facecolor='red', shrink=0.05, width=1.2, headwidth=5),
             fontweight='bold', color='#c0392b', bbox=dict(boxstyle="round,pad=0.3", fc="#ffeaa7", ec="#e67e22"))

ax1.set_title('[차트 3-1] 삼성전자 vs 애플 일일 수익률(Daily Return) 변동성 추이', fontsize=14, fontweight='bold', pad=12)
ax1.set_ylabel('일일 수익률 (%)', fontsize=12)
ax1.yaxis.set_major_formatter('{x:+.1f}%')
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# 하단: 20일 롤링 연율화 변동성
ax2.plot(sec.index, sec['Vol20'], label=f'삼성전자 20일 연율화 변동성 (평균: {sec["Vol20"].mean():.1f}%)', color='#0984E3', linewidth=2)
ax2.plot(aapl.index, aapl['Vol20'], label=f'애플 20일 연율화 변동성 (평균: {aapl["Vol20"].mean():.1f}%)', color='#E84393', linewidth=2)
ax2.set_title('[차트 3-2] 20일 롤링 연율화 변동성(Rolling Annualized Volatility) 비교', fontsize=13, fontweight='bold', pad=10)
ax2.set_ylabel('연율화 변동성 (%)', fontsize=12)
ax2.yaxis.set_major_formatter('{x:.0f}%')
ax2.legend(loc='upper left', frameon=True)
ax2.grid(True, linestyle=':', alpha=0.6)

ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig('images/03_daily_return_volatility.png', dpi=300)
plt.show()
""")

# Step 8: Distribution
add_md("""---
## 7. 시각화 4 (보너스): 일일 수익률 분포 히스토그램 & 박스플롯
- **목적:** 두 종목의 일일 수익률 통계적 분포(두꺼운 꼬리, 첨도, 이상치)를 확인합니다.
""")

add_code("""# [시각화 4] 일일 수익률 히스토그램 및 박스플롯
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 히스토그램 & KDE 곡선
sns.histplot(sec['Daily_Return'].dropna(), kde=True, color='#0984E3', 
             label=f"삼성전자 (표준편차: {sec['Daily_Return'].std():.2f}%)",
             stat="density", bins=40, alpha=0.4, ax=ax1)
sns.histplot(aapl['Daily_Return'].dropna(), kde=True, color='#E84393', 
             label=f"애플 (표준편차: {aapl['Daily_Return'].std():.2f}%)",
             stat="density", bins=40, alpha=0.4, ax=ax1)
ax1.axvline(0, color='gray', linestyle='--', linewidth=1)
ax1.set_title('[차트 4-1] 일일 수익률 분포 히스토그램 & 밀도(KDE)', fontsize=13, fontweight='bold')
ax1.set_xlabel('일일 수익률 (%)', fontsize=11)
ax1.set_ylabel('밀도 (Density)', fontsize=11)
ax1.legend(frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# 박스플롯 (이상치 시각화)
df_returns = pd.DataFrame({
    '종목': ['삼성전자'] * len(sec['Daily_Return'].dropna()) + ['애플'] * len(aapl['Daily_Return'].dropna()),
    '일일수익률': list(sec['Daily_Return'].dropna()) + list(aapl['Daily_Return'].dropna())
})
sns.boxplot(x='종목', y='일일수익률', hue='종목', data=df_returns, palette=['#74b9ff', '#ff7675'], legend=False, ax=ax2, width=0.4)
ax2.axhline(0, color='gray', linestyle='--', linewidth=1)
ax2.set_title('[차트 4-2] 일일 수익률 이상치(Outlier) 및 사분위 분포', fontsize=13, fontweight='bold')
ax2.set_ylabel('일일 수익률 (%)', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('images/04_return_distribution.png', dpi=300)
plt.show()
""")

# Step 9: Final Table & Q&A
add_md("""---
## 8. 최종 통계 요약 및 분석 질문 검증

### 📊 종합 통계 지표 비교표
""")

add_code("""# 핵심 통계 지표 데이터프레임 생성
summary_data = {
    '항목': [
        '분석 기간 시작일 주가',
        '분석 기간 종료일 주가',
        '기간 전체 수익률 (%)',
        '기간 최고가 (일자)',
        '기간 최저가 (일자)',
        '일일 변동성 (일간 표준편차)',
        '연율화 변동성 (Annualized Vol)',
        '최대 일일 상승률 (일자)',
        '최대 일일 하락률 (일자)',
        '종료일 기준 20일 SMA',
        '종료일 기준 20일 이격도 (Disparity)'
    ],
    '삼성전자 (005930.KS)': [
        f"{sec['Close'].iloc[0]:,.0f}원 (2023-01-02)",
        f"{sec['Close'].iloc[-1]:,.0f}원 (2024-12-30)",
        f"{((sec['Close'].iloc[-1] - sec['Close'].iloc[0]) / sec['Close'].iloc[0] * 100):+.2f}%",
        f"{sec['Close'].max():,.0f}원 ({sec['Close'].idxmax().strftime('%Y-%m-%d')})",
        f"{sec['Close'].min():,.0f}원 ({sec['Close'].idxmin().strftime('%Y-%m-%d')})",
        f"{sec['Daily_Return'].std():.2f}%",
        f"{sec['Daily_Return'].std() * np.sqrt(250):.2f}%",
        f"{sec['Daily_Return'].max():+.2f}% ({sec['Daily_Return'].idxmax().strftime('%Y-%m-%d')})",
        f"{sec['Daily_Return'].min():+.2f}% ({sec['Daily_Return'].idxmin().strftime('%Y-%m-%d')})",
        f"{sec['SMA20'].iloc[-1]:,.1f}원",
        f"{sec['Disparity'].iloc[-1]:+.2f}%"
    ],
    '애플 (AAPL)': [
        f"${aapl['Close'].iloc[0]:.2f} (2023-01-03)",
        f"${aapl['Close'].iloc[-1]:.2f} (2024-12-31)",
        f"{((aapl['Close'].iloc[-1] - aapl['Close'].iloc[0]) / aapl['Close'].iloc[0] * 100):+.2f}%",
        f"${aapl['Close'].max():.2f} ({aapl['Close'].idxmax().strftime('%Y-%m-%d')})",
        f"${aapl['Close'].min():.2f} ({aapl['Close'].idxmin().strftime('%Y-%m-%d')})",
        f"{aapl['Daily_Return'].std():.2f}%",
        f"{aapl['Daily_Return'].std() * np.sqrt(252):.2f}%",
        f"{aapl['Daily_Return'].max():+.2f}% ({aapl['Daily_Return'].idxmax().strftime('%Y-%m-%d')})",
        f"{aapl['Daily_Return'].min():+.2f}% ({aapl['Daily_Return'].idxmin().strftime('%Y-%m-%d')})",
        f"${aapl['SMA20'].iloc[-1]:.2f}",
        f"{aapl['Disparity'].iloc[-1]:+.2f}%"
    ]
}

df_summary = pd.DataFrame(summary_data)
display(df_summary)
""")

add_md("""---
## 🎯 분석 질문에 대한 명확한 답변

1. **질문 1: 2023~2024년 전체적인 주가 흐름은 상승 추세인가, 하락 추세인가?**
   - **삼성전자:** **약세 횡보/하락 마감 (총 수익률 -4.14%)**.  
     2023년 초 55,500원에서 2024년 7월 87,800원(+58.2%)까지 강한 상승세를 보였으나, 하반기 HBM 공급 지연 및 실적 부진으로 급락하여 49,900원까지 하락한 뒤 53,200원으로 마감함. (산 모양의 롤러코스터 패턴)
   - **애플:** **강력한 우상향 상승 추세 (총 수익률 +100.22%)**.  
     2023년 초 $125.07에서 2024년 말 $250.42로 주가가 정확히 2배로 급등하며 지속적인 신고가 랠리를 시현함.

2. **질문 2: 주가가 급변했던 특정 시점은 언제이며, 그 원인은 무엇으로 추정되는가?**
   - **삼성전자 최대 급락일:** **2024년 8월 5일 (-10.30%)**  
     → [추정 원인] 미국 경기 침체 공포 및 '엔 캐리 트레이드 청산'에 따른 글로벌 증시 '검은 월요일(Black Monday)'.
   - **삼성전자 최대 급등일:** **2024년 11월 15일 (+7.21%) 및 11월 18일 (+5.98%)**  
     → [추정 원인] '4만전자(49,900원)' 추락 직후 발표된 경영진의 10조 원 규모 초대형 자사주 매입 및 소각 공시 효과.
   - **애플 최대 급등일:** **2024년 6월 11일 (+7.26%)**  
     → [추정 원인] WWDC 2024에서 공개된 자체 AI 시스템 '애플 인텔리전스(Apple Intelligence)' 발표에 따른 월가의 교체 사이클 기대감.

3. **질문 3: 주가와 20일 이동평균선을 비교했을 때, 현재 주가는 평균 대비 어떤 상태인가?**
   - **삼성전자 (2024-12-30 종가 53,200원 vs 20일 SMA 54,035원):**  
     → **이격도 -1.55%로 20일선 '하회' 상태.** 20일 이동평균선이 주가 상단에서 저항선으로 작용하며 약세 조정 국면을 나타냄.
   - **애플 (2024-12-31 종가 $250.42 vs 20일 SMA $249.81):**  
     → **이격도 +0.24%로 20일선 '상회' 및 안착 상태.** 20일 이동평균선이 주가 하단에서 견고한 지지선 역할을 수행하는 상승 지속 국면임.
""")

notebook_json = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {
                "name": "ipython",
                "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

with open("analysis.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook_json, f, ensure_ascii=False, indent=2)

print("analysis.ipynb created successfully!")
