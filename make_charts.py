import os
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.dates as mdates

# Set Korean Font & Style
plt.rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False
sns.set_theme(style="whitegrid", font="Malgun Gothic")
plt.rcParams['axes.unicode_minus'] = False

# 1. Download Data
print("1. Downloading stock data...")
sec = yf.download('005930.KS', start='2023-01-01', end='2025-01-01', auto_adjust=False)
aapl = yf.download('AAPL', start='2023-01-01', end='2025-01-01', auto_adjust=False)

if isinstance(sec.columns, pd.MultiIndex):
    sec.columns = sec.columns.get_level_values(0)
if isinstance(aapl.columns, pd.MultiIndex):
    aapl.columns = aapl.columns.get_level_values(0)

# Save individual clean csv
sec.to_csv('data/samsung_data.csv')
aapl.to_csv('data/apple_data.csv')

# Calculate SMA 20 and Daily Return
sec['SMA20'] = sec['Close'].rolling(window=20).mean()
sec['Daily_Return'] = sec['Close'].pct_change() * 100
sec['Disparity'] = ((sec['Close'] - sec['SMA20']) / sec['SMA20']) * 100

aapl['SMA20'] = aapl['Close'].rolling(window=20).mean()
aapl['Daily_Return'] = aapl['Close'].pct_change() * 100
aapl['Disparity'] = ((aapl['Close'] - aapl['SMA20']) / aapl['SMA20']) * 100

# 2. Merged Data for Direct Comparison
# Forward-fill missing dates caused by differing KRX / US market holidays
combined = pd.DataFrame({
    'Samsung_Close': sec['Close'],
    'Samsung_Return': sec['Daily_Return'],
    'Apple_Close': aapl['Close'],
    'Apple_Return': aapl['Daily_Return']
})
combined_filled = combined.ffill().bfill()
combined_filled['Samsung_Norm'] = (combined_filled['Samsung_Close'] / combined_filled['Samsung_Close'].iloc[0]) * 100
combined_filled['Apple_Norm'] = (combined_filled['Apple_Close'] / combined_filled['Apple_Close'].iloc[0]) * 100
combined_filled.to_csv('data/samsung_apple_combined.csv')

print("2. Generating Visualizations...")

# -------------------------------------------------------------
# Chart 1: Two Stocks Price Comparison (Normalized & Dual-Axis)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True, gridspec_kw={'height_ratios': [1.2, 1]})

# Subplot 1: Normalized Return (2023-01 = 100)
ax1.plot(combined_filled.index, combined_filled['Samsung_Norm'], label='삼성전자 (005930.KS)', color='#0047AB', linewidth=2)
ax1.plot(combined_filled.index, combined_filled['Apple_Norm'], label='애플 (AAPL)', color='#E056FD', linewidth=2)
ax1.axhline(100, color='gray', linestyle='--', alpha=0.7, label='기준선 (100)')
ax1.set_title('[차트 1-1] 삼성전자 vs 애플 누적 수익률 비교 (기준일 2023-01-02/03 = 100)', fontsize=14, fontweight='bold', pad=12)
ax1.set_ylabel('정규화 지수 (기준=100)', fontsize=12)
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# Annotations on Subplot 1
ax1.annotate(f"애플 최종: {combined_filled['Apple_Norm'].iloc[-1]:.1f} (+{combined_filled['Apple_Norm'].iloc[-1]-100:.1f}%)",
             xy=(combined_filled.index[-1], combined_filled['Apple_Norm'].iloc[-1]),
             xytext=(combined_filled.index[-1] - pd.Timedelta(days=70), combined_filled['Apple_Norm'].iloc[-1] + 10),
             arrowprops=dict(facecolor='#E056FD', shrink=0.05, width=1.5, headwidth=6),
             fontweight='bold', color='#68007D', bbox=dict(boxstyle="round,pad=0.3", fc="#fbeaff", ec="#E056FD"))

ax1.annotate(f"삼성전자 최종: {combined_filled['Samsung_Norm'].iloc[-1]:.1f} ({combined_filled['Samsung_Norm'].iloc[-1]-100:+.1f}%)",
             xy=(combined_filled.index[-1], combined_filled['Samsung_Norm'].iloc[-1]),
             xytext=(combined_filled.index[-1] - pd.Timedelta(days=80), combined_filled['Samsung_Norm'].iloc[-1] - 25),
             arrowprops=dict(facecolor='#0047AB', shrink=0.05, width=1.5, headwidth=6),
             fontweight='bold', color='#002766', bbox=dict(boxstyle="round,pad=0.3", fc="#e6f4ff", ec="#0047AB"))

# Subplot 2: Dual Axis Actual Prices
ax2_twin = ax2.twinx()
p1 = ax2.plot(combined_filled.index, combined_filled['Samsung_Close'], color='#0047AB', label='삼성전자 종가 (KRW)', linewidth=1.8)
p2 = ax2_twin.plot(combined_filled.index, combined_filled['Apple_Close'], color='#FF7675', label='애플 종가 (USD)', linewidth=1.8)

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
plt.savefig('images/01_price_trend_comparison.png', dpi=300)
plt.close()
print("Saved images/01_price_trend_comparison.png")

# -------------------------------------------------------------
# Chart 2: Samsung Close vs 20-Day SMA
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# Top: Close and SMA20
ax1.plot(sec.index, sec['Close'], label='삼성전자 종가 (Close)', color='#1E3799', linewidth=2)
ax1.plot(sec.index, sec['SMA20'], label='20일 이동평균선 (SMA 20)', color='#FA983A', linewidth=2, linestyle='--')

# Fill between
ax1.fill_between(sec.index, sec['Close'], sec['SMA20'], where=(sec['Close'] >= sec['SMA20']),
                 color='#4CD137', alpha=0.2, label='주가 > SMA 20 (상승 국면)')
ax1.fill_between(sec.index, sec['Close'], sec['SMA20'], where=(sec['Close'] < sec['SMA20']),
                 color='#E84118', alpha=0.2, label='주가 < SMA 20 (하락/조정 국면)')

# Annotate key milestones
# 2024-03-20 Jensen Huang GTC
ax1.annotate('2024-03-20\n엔비디아 GTC\n(HBM 승인 기대)',
             xy=(pd.Timestamp('2024-03-20'), 76900),
             xytext=(pd.Timestamp('2024-01-15'), 83000),
             arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=5),
             fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="#f1f2f6", ec="#ced6e0"))

# 2024-07-09 Peak
ax1.annotate('2024-07-09\n최고가 87,800원',
             xy=(pd.Timestamp('2024-07-09'), 87800),
             xytext=(pd.Timestamp('2024-05-15'), 92000),
             arrowprops=dict(facecolor='#E84118', shrink=0.05, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', color='#c0392b', bbox=dict(boxstyle="round,pad=0.3", fc="#ffeaa7", ec="#fdcb6e"))

# 2024-08-05 Black Monday
ax1.annotate('2024-08-05\n검은 월요일 (-10.3%)',
             xy=(pd.Timestamp('2024-08-05'), 71400),
             xytext=(pd.Timestamp('2024-08-15'), 60000),
             arrowprops=dict(facecolor='#c0392b', shrink=0.05, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', color='#c0392b', bbox=dict(boxstyle="round,pad=0.3", fc="#ffdd59", ec="#e67e22"))

# 2024-11-14 Trough & Buyback
ax1.annotate('2024-11-14 최저 49,900원\n11-15 자사주 10조 매입',
             xy=(pd.Timestamp('2024-11-15'), 53500),
             xytext=(pd.Timestamp('2024-09-15'), 46000),
             arrowprops=dict(facecolor='#0984e3', shrink=0.05, width=1.5, headwidth=6),
             fontsize=9, fontweight='bold', color='#0984e3', bbox=dict(boxstyle="round,pad=0.3", fc="#dff9fb", ec="#22a6b3"))

ax1.set_title('[차트 2] 삼성전자 종가 vs 20일 이동평균선(SMA 20) 추이 및 주요 이벤트', fontsize=14, fontweight='bold', pad=12)
ax1.set_ylabel('주가 (KRW)', fontsize=12)
ax1.yaxis.set_major_formatter('{x:,.0f}원')
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# Bottom: Disparity (%)
ax2.plot(sec.index, sec['Disparity'], color='#2F3542', linewidth=1.5, label='20일 이격도 (Disparity, %)')
ax2.axhline(0, color='red', linestyle='--', linewidth=1.2, alpha=0.8, label='SMA 20 기준선 (0%)')
ax2.axhline(5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax2.axhline(-5, color='gray', linestyle=':', linewidth=1, alpha=0.5)
ax2.fill_between(sec.index, sec['Disparity'], 0, where=(sec['Disparity'] >= 0), color='#4CD137', alpha=0.3)
ax2.fill_between(sec.index, sec['Disparity'], 0, where=(sec['Disparity'] < 0), color='#E84118', alpha=0.3)

# Mark the last day
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
plt.close()
print("Saved images/02_samsung_sma20.png")

# -------------------------------------------------------------
# Chart 3: Daily Return Volatility (Time-series & Rolling Std)
# -------------------------------------------------------------
# 20-day rolling annualized volatility: std * sqrt(250) * 100
sec['Vol20'] = sec['Daily_Return'].rolling(window=20).std() * np.sqrt(250)
aapl['Vol20'] = aapl['Daily_Return'].rolling(window=20).std() * np.sqrt(252)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), sharex=True)

# Top: Daily Return Line Chart
ax1.plot(sec.index, sec['Daily_Return'], label='삼성전자 일일 수익률(%)', color='#0984E3', alpha=0.7, linewidth=1.2)
ax1.plot(aapl.index, aapl['Daily_Return'], label='애플 일일 수익률(%)', color='#E84393', alpha=0.7, linewidth=1.2)
ax1.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.7)
ax1.axhline(5, color='orange', linestyle=':', alpha=0.5)
ax1.axhline(-5, color='orange', linestyle=':', alpha=0.5)

# Annotate Black Monday 2024-08-05
ax1.annotate('2024-08-05\n삼성: -10.30%\n애플: -4.82%',
             xy=(pd.Timestamp('2024-08-05'), -10.30),
             xytext=(pd.Timestamp('2024-06-01'), -9.5),
             arrowprops=dict(facecolor='red', shrink=0.05, width=1.2, headwidth=5),
             fontweight='bold', color='#c0392b', bbox=dict(boxstyle="round,pad=0.3", fc="#ffeaa7", ec="#e67e22"))

ax1.set_title('[차트 3-1] 삼성전자 vs 애플 일일 수익률(Daily Return) 변동성 추이', fontsize=14, fontweight='bold', pad=12)
ax1.set_ylabel('일일 수익률 (%)', fontsize=12)
ax1.yaxis.set_major_formatter('{x:+.1f}%')
ax1.legend(loc='upper left', frameon=True)
ax1.grid(True, linestyle=':', alpha=0.6)

# Bottom: 20-day Rolling Volatility (Annualized)
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
plt.close()
print("Saved images/03_daily_return_volatility.png")

# -------------------------------------------------------------
# Chart 4: Daily Return Distribution Histogram & Boxplot
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# Histogram with KDE
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

# Boxplot
df_returns = pd.DataFrame({
    '종목': ['삼성전자'] * len(sec['Daily_Return'].dropna()) + ['애플'] * len(aapl['Daily_Return'].dropna()),
    '일일수익률': list(sec['Daily_Return'].dropna()) + list(aapl['Daily_Return'].dropna())
})
sns.boxplot(x='종목', y='일일수익률', data=df_returns, palette=['#74b9ff', '#ff7675'], ax=ax2, width=0.4)
ax2.axhline(0, color='gray', linestyle='--', linewidth=1)
ax2.set_title('[차트 4-2] 일일 수익률 이상치(Outlier) 및 분포 박스플롯', fontsize=13, fontweight='bold')
ax2.set_ylabel('일일 수익률 (%)', fontsize=11)
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.savefig('images/04_return_distribution.png', dpi=300)
plt.close()
print("Saved images/04_return_distribution.png")

print("All charts generated successfully!")
