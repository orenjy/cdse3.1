"""
[시계열 데이터 분석 프로젝트] 삼성전자 vs 애플 주가 트렌드 및 변동성 분석 (2023~2024)
- 종목: 삼성전자(005930.KS), 애플(AAPL)
- 기간: 2023-01-01 ~ 2024-12-31
- 작성: 데이터 분석가 & 파이썬 강사
"""

import os
import sys

# Windows 콘솔 인코딩 UTF-8 호환성 보장
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates
import warnings

warnings.filterwarnings('ignore')

# -------------------------------------------------------------
# 1. 환경 설정 및 폰트 세팅
# -------------------------------------------------------------
def setup_environment():
    os.makedirs('data', exist_ok=True)
    os.makedirs('images', exist_ok=True)
    
    # Windows 한글 폰트 설정
    plt.rc('font', family='Malgun Gothic')
    plt.rcParams['axes.unicode_minus'] = False
    sns.set_theme(style="whitegrid", font="Malgun Gothic")
    plt.rcParams['axes.unicode_minus'] = False
    print("✅ [Step 1] 환경 설정 및 디렉터리 준비 완료")

# -------------------------------------------------------------
# 2. 데이터 다운로드 및 저장
# -------------------------------------------------------------
def download_data():
    print("⏳ [Step 2] 데이터 다운로드 중 (2023-01-01 ~ 2024-12-31)...")
    sec = yf.download('005930.KS', start='2023-01-01', end='2025-01-01', auto_adjust=False)
    aapl = yf.download('AAPL', start='2023-01-01', end='2025-01-01', auto_adjust=False)
    
    if isinstance(sec.columns, pd.MultiIndex):
        sec.columns = sec.columns.get_level_values(0)
    if isinstance(aapl.columns, pd.MultiIndex):
        aapl.columns = aapl.columns.get_level_values(0)
        
    sec.to_csv('data/samsung_data.csv')
    aapl.to_csv('data/apple_data.csv')
    print(f"✅ 삼성전자 데이터 저장 완료: {len(sec)} 거래일")
    print(f"✅ 애플 데이터 저장 완료: {len(aapl)} 거래일")
    return sec, aapl

# -------------------------------------------------------------
# 3. 데이터 정제 및 시계열 지표 산출
# -------------------------------------------------------------
def process_data(sec, aapl):
    print("⏳ [Step 3] 결측치 검증 및 시계열 파생변수 계산 중...")
    
    # 개별 종목 지표 산출
    sec['Daily_Return'] = sec['Close'].pct_change() * 100
    sec['SMA20'] = sec['Close'].rolling(window=20).mean()
    sec['Disparity'] = ((sec['Close'] - sec['SMA20']) / sec['SMA20']) * 100
    sec['Vol20'] = sec['Daily_Return'].rolling(window=20).std() * np.sqrt(250)
    
    aapl['Daily_Return'] = aapl['Close'].pct_change() * 100
    aapl['SMA20'] = aapl['Close'].rolling(window=20).mean()
    aapl['Disparity'] = ((aapl['Close'] - aapl['SMA20']) / aapl['SMA20']) * 100
    aapl['Vol20'] = aapl['Daily_Return'].rolling(window=20).std() * np.sqrt(252)
    
    # 통합 달력 결측치 보정 (휴장일 ffill)
    combined = pd.DataFrame({
        'Samsung_Close': sec['Close'],
        'Samsung_Return': sec['Daily_Return'],
        'Apple_Close': aapl['Close'],
        'Apple_Return': aapl['Daily_Return']
    }).ffill().bfill()
    
    # 정규화 누적 수익률 (2023년 시초=100)
    combined['Samsung_Norm'] = (combined['Samsung_Close'] / combined['Samsung_Close'].iloc[0]) * 100
    combined['Apple_Norm'] = (combined['Apple_Close'] / combined['Apple_Close'].iloc[0]) * 100
    combined.to_csv('data/samsung_apple_combined.csv')
    
    print("✅ 데이터 정제 및 파생변수 계산 완료")
    return sec, aapl, combined

# -------------------------------------------------------------
# 4. 시각화 생성 및 화면 표시
# -------------------------------------------------------------
def generate_visualizations(sec, aapl, combined):
    print("\n⏳ [Step 4] 시각화 이미지 생성 및 화면 표시 중...")
    print("💡 팁: 그래프 창(GUI 창)이 화면에 뜨면 확인 후 창을 닫아주세요. 다음 차트가 차례대로 표시됩니다.\n")
    
    # 차트 1: 두 종목 종가 비교
    print("📈 [차트 1/4] 두 종목 종가 비교 (정규화 누적 수익률 & 이중축) 창을 표시합니다...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [1.2, 1]})
    ax1.plot(combined.index, combined['Samsung_Norm'], label='삼성전자 (005930.KS)', color='#0047AB', linewidth=2)
    ax1.plot(combined.index, combined['Apple_Norm'], label='애플 (AAPL)', color='#E056FD', linewidth=2)
    ax1.axhline(100, color='gray', linestyle='--', alpha=0.7, label='기준선 (100)')
    ax1.set_title('[차트 1-1] 삼성전자 vs 애플 누적 수익률 비교 (기준일 2023-01-02/03 = 100)', fontsize=14, fontweight='bold', pad=12)
    ax1.set_ylabel('정규화 지수 (기준=100)', fontsize=12)
    ax1.legend(loc='upper left', frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    ax2_twin = ax2.twinx()
    p1 = ax2.plot(combined.index, combined['Samsung_Close'], color='#0047AB', label='삼성전자 종가 (KRW)', linewidth=1.8)
    p2 = ax2_twin.plot(combined.index, combined['Apple_Close'], color='#FF7675', label='애플 종가 (USD)', linewidth=1.8)
    ax2.set_title('[차트 1-2] 종목별 실제 종가 추이 (이중 Y축: KRW vs USD)', fontsize=13, fontweight='bold', pad=10)
    ax2.set_ylabel('삼성전자 주가 (원)', color='#0047AB', fontsize=12)
    ax2_twin.set_ylabel('애플 주가 (달러)', color='#FF7675', fontsize=12)
    ax2.yaxis.set_major_formatter('{x:,.0f}원')
    ax2_twin.yaxis.set_major_formatter('${x:,.0f}')
    lines = p1 + p2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='upper left', frameon=True)
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig('images/01_price_trend_comparison.png', dpi=300)
    plt.show()  # 화면에 그래프 창 팝업!
    
    # 차트 2: 삼성전자 종가 vs 20일 이동평균선
    print("📈 [차트 2/4] 삼성전자 종가 vs 20일 이동평균선(SMA 20) 창을 표시합니다...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True, gridspec_kw={'height_ratios': [2, 1]})
    ax1.plot(sec.index, sec['Close'], label='삼성전자 종가 (Close)', color='#1E3799', linewidth=2)
    ax1.plot(sec.index, sec['SMA20'], label='20일 이동평균선 (SMA 20)', color='#FA983A', linewidth=2, linestyle='--')
    ax1.fill_between(sec.index, sec['Close'], sec['SMA20'], where=(sec['Close'] >= sec['SMA20']),
                     color='#4CD137', alpha=0.2, label='주가 > SMA 20 (상승 국면)')
    ax1.fill_between(sec.index, sec['Close'], sec['SMA20'], where=(sec['Close'] < sec['SMA20']),
                     color='#E84118', alpha=0.2, label='주가 < SMA 20 (하락/조정 국면)')
    ax1.set_title('[차트 2] 삼성전자 종가 vs 20일 이동평균선(SMA 20) 추이 및 변곡점', fontsize=14, fontweight='bold', pad=12)
    ax1.set_ylabel('주가 (KRW)', fontsize=12)
    ax1.yaxis.set_major_formatter('{x:,.0f}원')
    ax1.legend(loc='upper left', frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    ax2.plot(sec.index, sec['Disparity'], color='#2F3542', linewidth=1.5, label='20일 이격도 (Disparity, %)')
    ax2.axhline(0, color='red', linestyle='--', linewidth=1.2, alpha=0.8, label='SMA 20 기준선 (0%)')
    ax2.fill_between(sec.index, sec['Disparity'], 0, where=(sec['Disparity'] >= 0), color='#4CD137', alpha=0.3)
    ax2.fill_between(sec.index, sec['Disparity'], 0, where=(sec['Disparity'] < 0), color='#E84118', alpha=0.3)
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
    plt.show()  # 화면에 그래프 창 팝업!
    
    # 차트 3: 변동성 추이
    print("📈 [차트 3/4] 일일 수익률 변동성 및 20일 롤링 변동성 창을 표시합니다...")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)
    ax1.plot(sec.index, sec['Daily_Return'], label='삼성전자 일일 수익률(%)', color='#0984E3', alpha=0.7, linewidth=1.2)
    ax1.plot(aapl.index, aapl['Daily_Return'], label='애플 일일 수익률(%)', color='#E84393', alpha=0.7, linewidth=1.2)
    ax1.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.7)
    ax1.set_title('[차트 3-1] 삼성전자 vs 애플 일일 수익률(Daily Return) 변동성 추이', fontsize=14, fontweight='bold', pad=12)
    ax1.set_ylabel('일일 수익률 (%)', fontsize=12)
    ax1.yaxis.set_major_formatter('{x:+.1f}%')
    ax1.legend(loc='upper left', frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
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
    plt.show()  # 화면에 그래프 창 팝업!
    
    # 차트 4: 분포 비교
    print("📈 [차트 4/4] 일일 수익률 히스토그램 및 박스플롯 분포 창을 표시합니다...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    sns.histplot(sec['Daily_Return'].dropna(), kde=True, color='#0984E3', label=f"삼성전자 (표준편차: {sec['Daily_Return'].std():.2f}%)",
                 stat="density", bins=40, alpha=0.4, ax=ax1)
    sns.histplot(aapl['Daily_Return'].dropna(), kde=True, color='#E84393', label=f"애플 (표준편차: {aapl['Daily_Return'].std():.2f}%)",
                 stat="density", bins=40, alpha=0.4, ax=ax1)
    ax1.axvline(0, color='gray', linestyle='--', linewidth=1)
    ax1.set_title('[차트 4-1] 일일 수익률 분포 히스토그램 & 밀도(KDE)', fontsize=13, fontweight='bold')
    ax1.set_xlabel('일일 수익률 (%)', fontsize=11)
    ax1.set_ylabel('밀도 (Density)', fontsize=11)
    ax1.legend(frameon=True)
    ax1.grid(True, linestyle=':', alpha=0.6)
    
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
    plt.show()  # 화면에 그래프 창 팝업!
    
    print("✅ 모든 시각화 차트가 images/ 폴더에 고화질로 저장되었으며, 화면 출력이 완료되었습니다.")

# -------------------------------------------------------------
# 5. 핵심 통계 출력
# -------------------------------------------------------------
def print_summary(sec, aapl):
    print("\n================== [핵심 분석 요약] ==================")
    print(f"▶ 삼성전자 (2023-01-02 ~ 2024-12-30)")
    print(f"  - 시작가: {sec['Close'].iloc[0]:,.0f}원 | 최종가: {sec['Close'].iloc[-1]:,.0f}원 | 수익률: {((sec['Close'].iloc[-1]-sec['Close'].iloc[0])/sec['Close'].iloc[0]*100):+.2f}%")
    print(f"  - 최고가: {sec['Close'].max():,.0f}원 ({sec['Close'].idxmax().strftime('%Y-%m-%d')}) | 최저가: {sec['Close'].min():,.0f}원 ({sec['Close'].idxmin().strftime('%Y-%m-%d')})")
    print(f"  - 최종 20일 SMA: {sec['SMA20'].iloc[-1]:,.1f}원 | 이격도: {sec['Disparity'].iloc[-1]:+.2f}% (20일선 하회)")
    print(f"  - 연율화 변동성: {sec['Daily_Return'].std()*np.sqrt(250):.2f}%")
    
    print(f"\n▶ 애플 (2023-01-03 ~ 2024-12-31)")
    print(f"  - 시작가: ${aapl['Close'].iloc[0]:.2f} | 최종가: ${aapl['Close'].iloc[-1]:.2f} | 수익률: {((aapl['Close'].iloc[-1]-aapl['Close'].iloc[0])/aapl['Close'].iloc[0]*100):+.2f}%")
    print(f"  - 최고가: ${aapl['Close'].max():.2f} ({aapl['Close'].idxmax().strftime('%Y-%m-%d')}) | 최저가: ${aapl['Close'].min():.2f} ({aapl['Close'].idxmin().strftime('%Y-%m-%d')})")
    print(f"  - 최종 20일 SMA: ${aapl['SMA20'].iloc[-1]:.2f} | 이격도: {aapl['Disparity'].iloc[-1]:+.2f}% (20일선 상회)")
    print(f"  - 연율화 변동성: {aapl['Daily_Return'].std()*np.sqrt(252):.2f}%")
    print("======================================================\n")

if __name__ == '__main__':
    setup_environment()
    sec, aapl = download_data()
    sec, aapl, combined = process_data(sec, aapl)
    generate_visualizations(sec, aapl, combined)
    print_summary(sec, aapl)
