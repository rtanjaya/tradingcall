"""Stock universe definitions for each market."""

US_STOCKS = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "META", "NVDA", "AMD", "INTC", "CRM", "ORCL", "IBM",
    "CSCO", "QCOM", "TXN", "AVGO", "MU", "HPE", "AMAT", "LRCX", "KLAC", "ADI",
    "DELL", "HPQ", "WDC", "STX", "NTAP", "CDNS", "SNPS", "ANSS", "PTC", "CTSH",
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "AXP", "V", "MA",
    "USB", "TFC", "COF", "ALL", "MET", "PRU", "AFL", "CB", "TRV", "MMC",
    "PNC", "FITB", "KEY", "RF", "CFG", "HBAN", "MTB", "ZION",
    # Healthcare
    "JNJ", "UNH", "PFE", "MRK", "ABBV", "LLY", "BMY", "AMGN", "GILD", "CVS",
    "MCK", "ABT", "MDT", "ELV", "HUM", "CI", "CNC", "MOH", "ISRG", "BSX",
    "SYK", "ZBH", "BDX", "BAX", "CAH", "AMP",
    # Consumer Discretionary
    "AMZN", "HD", "LOW", "MCD", "SBUX", "NKE", "TGT", "COST", "TJX", "ROST",
    "BBY", "KSS", "M", "GPS", "PVH", "RL", "VFC", "HBI",
    # Consumer Staples
    "WMT", "PG", "KO", "PEP", "PM", "MO", "CL", "GIS", "K", "CPB",
    "SJM", "CAG", "MKC", "HRL", "TSN", "KHC", "HSY",
    # Energy
    "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "KMI", "WMB",
    "OKE", "HAL", "BKR", "DVN", "PXD",
    # Industrials
    "GE", "HON", "MMM", "CAT", "DE", "BA", "RTX", "LMT", "NOC", "GD",
    "EMR", "ETN", "ITW", "PH", "ROK", "XYL", "IR", "FTV", "AME", "ROP",
    "CARR", "OTIS", "FDX", "UPS", "CSX", "NSC", "UNP",
    # Materials
    "LIN", "APD", "ECL", "NEM", "FCX", "NUE", "ALB", "CF", "MOS", "FMC",
    # Utilities
    "NEE", "DUK", "SO", "AEP", "D", "EXC", "XEL", "WEC", "ES", "ETR",
    # REITs
    "PLD", "AMT", "CCI", "EQIX", "SPG", "O", "VICI", "WELL", "DLR", "PSA",
    # Telecom
    "T", "VZ", "TMUS",
]

HK_STOCKS = [
    # Hang Seng Index + major HKEX
    "0700.HK",   # Tencent
    "9988.HK",   # Alibaba
    "0005.HK",   # HSBC
    "0941.HK",   # China Mobile
    "1299.HK",   # AIA Group
    "2318.HK",   # Ping An Insurance
    "0388.HK",   # HKEx
    "3988.HK",   # Bank of China
    "0939.HK",   # CCB
    "1398.HK",   # ICBC
    "0857.HK",   # PetroChina
    "0386.HK",   # Sinopec
    "2628.HK",   # China Life
    "0883.HK",   # CNOOC
    "0003.HK",   # HK & China Gas
    "0001.HK",   # CK Hutchison
    "0002.HK",   # CLP Holdings
    "0016.HK",   # Sun Hung Kai Properties
    "0011.HK",   # Hang Seng Bank
    "1109.HK",   # China Resources Land
    "1038.HK",   # CK Infrastructure
    "0066.HK",   # MTR Corp
    "0823.HK",   # Link REIT
    "2331.HK",   # Li Ning
    "9618.HK",   # JD.com
    "0762.HK",   # China Unicom
    "1044.HK",   # Hengan International
    "1113.HK",   # CK Asset Holdings
    "0267.HK",   # CITIC
    "2020.HK",   # ANTA Sports
    "0175.HK",   # Geely Auto
    "0027.HK",   # Galaxy Entertainment
    "1211.HK",   # BYD
    "3690.HK",   # Meituan
    "0688.HK",   # China Overseas Land
    "0012.HK",   # Henderson Land
    "0017.HK",   # New World Dev
    "0288.HK",   # WH Group
    "6098.HK",   # CG Services
    "9999.HK",   # NetEase
    "1024.HK",   # Kuaishou
    "0960.HK",   # Longfor
    "1810.HK",   # Xiaomi
    "2382.HK",   # Sunny Optical
    "9888.HK",   # Baidu
]

SG_STOCKS = [
    # STI Components + broader SGX
    "D05.SI",    # DBS Group
    "O39.SI",    # OCBC Bank
    "U11.SI",    # UOB
    "Z74.SI",    # Singtel
    "C6L.SI",    # Singapore Airlines
    "S68.SI",    # SGX
    "U96.SI",    # Sembcorp Industries
    "C38U.SI",   # CapitaLand Ascendas REIT (replaces C31)
    "A17U.SI",   # Ascendas REIT
    "ME8U.SI",   # Mapletree Industrial Trust
    "N2IU.SI",   # Mapletree Pan Asia Commercial
    "C38U.SI",   # CapitaLand Ascendas REIT
    "H78.SI",    # Hongkong Land
    "BS6.SI",    # Yangzijiang Shipbuilding
    "BN4.SI",    # Keppel
    "U14.SI",    # UOL Group
    "V03.SI",    # Venture Corp
    "S58.SI",    # SATS
    "G13.SI",    # Genting Singapore
    "C09.SI",    # City Developments
    "9CI.SI",    # CapitaLand Investment
    "F34.SI",    # Wilmar International
    "J36.SI",    # Jardine Matheson
    "S07.SI",    # Jardine Cycle & Carriage
    "Y92.SI",    # Thai Beverage
    "OV8.SI",    # Sheng Siong Group
    "5E2.SI",    # Olam Group
    "M44U.SI",   # Mapletree Logistics Trust
    "BUOU.SI",   # Frasers Logistics Trust
    "K71U.SI",   # Keppel REIT
]

MARKET_CONFIG = {
    "US": {
        "name": "United States",
        "tickers": US_STOCKS,
        "currency": "USD",
        "timezone": "America/New_York",
        "open": "09:30",
        "close": "16:00",
        "flag": "🇺🇸",
    },
    "HK": {
        "name": "Hong Kong",
        "tickers": HK_STOCKS,
        "currency": "HKD",
        "timezone": "Asia/Hong_Kong",
        "open": "09:30",
        "close": "16:00",
        "flag": "🇭🇰",
    },
    "SG": {
        "name": "Singapore",
        "tickers": SG_STOCKS,
        "currency": "SGD",
        "timezone": "Asia/Singapore",
        "open": "09:00",
        "close": "17:00",
        "flag": "🇸🇬",
    },
}
