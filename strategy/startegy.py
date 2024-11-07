def volatility_breakout_strategy(df, k=0.5):
    """변동성 돌파 전략을 구현합니다."""
    df['range'] = df['고가'] - df['저가']
    df['target'] = df['시가'] + (df['range'].shift(1) * k)
    df['buy_signal'] = df['고가'] > df['target']
    df['sell_price'] = df['종가']
    df['returns'] = 0
    df.loc[df['buy_signal'], 'returns'] = df['sell_price'] / df['target'] - 1
    df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1
    return df
