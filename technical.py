from alpha_vantage.techindicators import TechIndicators

ti = TechIndicators(key='8HY3ZTQRP0WR4QF1')
data, meta_data = ti.get_rsi(symbol='MSFT', interval='1min', time_period=20, series_type='close')

print(data)
print(meta_data)