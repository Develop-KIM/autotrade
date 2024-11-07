import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_returns(result):
    """일별 수익률을 시각화합니다."""
    plt.figure(figsize=(14, 7))
    buy_signals = result[result['buy_signal']]
    plt.bar(buy_signals.index, buy_signals['returns'] * 100, color='green')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xlabel('날짜')
    plt.ylabel('일별 수익률 (%)')
    plt.title('일별 수익률')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    plt.show()