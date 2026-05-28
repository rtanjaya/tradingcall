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

# ── Company name lookup (fallback when yfinance info call fails) ───────────────
COMPANY_NAMES = {
    # ── United States ──
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "GOOGL": "Alphabet Inc.",
    "META": "Meta Platforms", "NVDA": "NVIDIA Corporation", "AMD": "Advanced Micro Devices",
    "INTC": "Intel Corporation", "CRM": "Salesforce Inc.", "ORCL": "Oracle Corporation",
    "IBM": "IBM Corporation", "CSCO": "Cisco Systems", "QCOM": "Qualcomm Inc.",
    "TXN": "Texas Instruments", "AVGO": "Broadcom Inc.", "MU": "Micron Technology",
    "HPE": "Hewlett Packard Enterprise", "AMAT": "Applied Materials", "LRCX": "Lam Research",
    "KLAC": "KLA Corporation", "ADI": "Analog Devices", "DELL": "Dell Technologies",
    "HPQ": "HP Inc.", "WDC": "Western Digital", "STX": "Seagate Technology",
    "NTAP": "NetApp Inc.", "CDNS": "Cadence Design Systems", "SNPS": "Synopsys Inc.",
    "ANSS": "ANSYS Inc.", "PTC": "PTC Inc.", "CTSH": "Cognizant Technology",
    "JPM": "JPMorgan Chase & Co.", "BAC": "Bank of America", "WFC": "Wells Fargo & Company",
    "GS": "Goldman Sachs Group", "MS": "Morgan Stanley", "C": "Citigroup Inc.",
    "BLK": "BlackRock Inc.", "AXP": "American Express", "V": "Visa Inc.", "MA": "Mastercard",
    "USB": "U.S. Bancorp", "TFC": "Truist Financial", "COF": "Capital One Financial",
    "ALL": "Allstate Corporation", "MET": "MetLife Inc.", "PRU": "Prudential Financial",
    "AFL": "Aflac Inc.", "CB": "Chubb Limited", "TRV": "Travelers Companies", "MMC": "Marsh McLennan",
    "PNC": "PNC Financial Services", "FITB": "Fifth Third Bancorp", "KEY": "KeyCorp",
    "RF": "Regions Financial", "CFG": "Citizens Financial", "HBAN": "Huntington Bancshares",
    "MTB": "M&T Bank Corporation", "ZION": "Zions Bancorporation",
    "JNJ": "Johnson & Johnson", "UNH": "UnitedHealth Group", "PFE": "Pfizer Inc.",
    "MRK": "Merck & Co.", "ABBV": "AbbVie Inc.", "LLY": "Eli Lilly and Company",
    "BMY": "Bristol-Myers Squibb", "AMGN": "Amgen Inc.", "GILD": "Gilead Sciences",
    "CVS": "CVS Health Corporation", "MCK": "McKesson Corporation", "ABT": "Abbott Laboratories",
    "MDT": "Medtronic plc", "ELV": "Elevance Health", "HUM": "Humana Inc.",
    "CI": "The Cigna Group", "CNC": "Centene Corporation", "MOH": "Molina Healthcare",
    "ISRG": "Intuitive Surgical", "BSX": "Boston Scientific", "SYK": "Stryker Corporation",
    "ZBH": "Zimmer Biomet Holdings", "BDX": "Becton Dickinson", "BAX": "Baxter International",
    "CAH": "Cardinal Health", "AMP": "Ameriprise Financial",
    "AMZN": "Amazon.com Inc.", "HD": "Home Depot Inc.", "LOW": "Lowe's Companies",
    "MCD": "McDonald's Corporation", "SBUX": "Starbucks Corporation", "NKE": "Nike Inc.",
    "TGT": "Target Corporation", "COST": "Costco Wholesale", "TJX": "TJX Companies",
    "ROST": "Ross Stores Inc.", "BBY": "Best Buy Co.", "KSS": "Kohl's Corporation",
    "M": "Macy's Inc.", "GPS": "Gap Inc.", "PVH": "PVH Corp.", "RL": "Ralph Lauren",
    "VFC": "VF Corporation", "HBI": "Hanesbrands Inc.",
    "WMT": "Walmart Inc.", "PG": "Procter & Gamble", "KO": "Coca-Cola Company",
    "PEP": "PepsiCo Inc.", "PM": "Philip Morris International", "MO": "Altria Group",
    "CL": "Colgate-Palmolive", "GIS": "General Mills", "K": "Kellanova",
    "CPB": "Campbell Soup Company", "SJM": "J.M. Smucker", "CAG": "Conagra Brands",
    "MKC": "McCormick & Company", "HRL": "Hormel Foods", "TSN": "Tyson Foods",
    "KHC": "Kraft Heinz Company", "HSY": "Hershey Company",
    "XOM": "Exxon Mobil Corporation", "CVX": "Chevron Corporation", "COP": "ConocoPhillips",
    "EOG": "EOG Resources", "SLB": "Schlumberger Limited", "MPC": "Marathon Petroleum",
    "PSX": "Phillips 66", "VLO": "Valero Energy", "KMI": "Kinder Morgan", "WMB": "Williams Companies",
    "OKE": "ONEOK Inc.", "HAL": "Halliburton Company", "BKR": "Baker Hughes", "DVN": "Devon Energy",
    "GE": "GE Aerospace", "HON": "Honeywell International", "MMM": "3M Company",
    "CAT": "Caterpillar Inc.", "DE": "Deere & Company", "BA": "Boeing Company",
    "RTX": "RTX Corporation", "LMT": "Lockheed Martin", "NOC": "Northrop Grumman",
    "GD": "General Dynamics", "EMR": "Emerson Electric", "ETN": "Eaton Corporation",
    "ITW": "Illinois Tool Works", "PH": "Parker Hannifin", "ROK": "Rockwell Automation",
    "XYL": "Xylem Inc.", "IR": "Ingersoll Rand", "FTV": "Fortive Corporation",
    "AME": "AMETEK Inc.", "ROP": "Roper Technologies", "CARR": "Carrier Global",
    "OTIS": "Otis Worldwide", "FDX": "FedEx Corporation", "UPS": "United Parcel Service",
    "CSX": "CSX Corporation", "NSC": "Norfolk Southern", "UNP": "Union Pacific",
    "LIN": "Linde plc", "APD": "Air Products & Chemicals", "ECL": "Ecolab Inc.",
    "NEM": "Newmont Corporation", "FCX": "Freeport-McMoRan", "NUE": "Nucor Corporation",
    "ALB": "Albemarle Corporation", "CF": "CF Industries", "MOS": "Mosaic Company", "FMC": "FMC Corporation",
    "NEE": "NextEra Energy", "DUK": "Duke Energy", "SO": "Southern Company",
    "AEP": "American Electric Power", "D": "Dominion Energy", "EXC": "Exelon Corporation",
    "XEL": "Xcel Energy", "WEC": "WEC Energy Group", "ES": "Eversource Energy", "ETR": "Entergy",
    "PLD": "Prologis Inc.", "AMT": "American Tower", "CCI": "Crown Castle",
    "EQIX": "Equinix Inc.", "SPG": "Simon Property Group", "O": "Realty Income",
    "VICI": "VICI Properties", "WELL": "Welltower Inc.", "DLR": "Digital Realty", "PSA": "Public Storage",
    "T": "AT&T Inc.", "VZ": "Verizon Communications", "TMUS": "T-Mobile US",
    # ── Hong Kong ──
    "0700.HK": "Tencent Holdings",
    "9988.HK": "Alibaba Group",
    "0005.HK": "HSBC Holdings",
    "0941.HK": "China Mobile",
    "1299.HK": "AIA Group",
    "2318.HK": "Ping An Insurance",
    "0388.HK": "Hong Kong Exchanges",
    "3988.HK": "Bank of China",
    "0939.HK": "China Construction Bank",
    "1398.HK": "Industrial & Commercial Bank of China",
    "0857.HK": "PetroChina",
    "0386.HK": "Sinopec Corp",
    "2628.HK": "China Life Insurance",
    "0883.HK": "CNOOC",
    "0003.HK": "Hong Kong & China Gas",
    "0001.HK": "CK Hutchison Holdings",
    "0002.HK": "CLP Holdings",
    "0016.HK": "Sun Hung Kai Properties",
    "0011.HK": "Hang Seng Bank",
    "1109.HK": "China Resources Land",
    "1038.HK": "CK Infrastructure Holdings",
    "0066.HK": "MTR Corporation",
    "0823.HK": "Link REIT",
    "2331.HK": "Li Ning Company",
    "9618.HK": "JD.com",
    "0762.HK": "China Unicom",
    "1044.HK": "Hengan International",
    "1113.HK": "CK Asset Holdings",
    "0267.HK": "CITIC Limited",
    "2020.HK": "ANTA Sports Products",
    "0175.HK": "Geely Automobile",
    "0027.HK": "Galaxy Entertainment",
    "1211.HK": "BYD Company",
    "3690.HK": "Meituan",
    "0688.HK": "China Overseas Land & Inv.",
    "0012.HK": "Henderson Land Development",
    "0017.HK": "New World Development",
    "0288.HK": "WH Group",
    "6098.HK": "Country Garden Services",
    "9999.HK": "NetEase",
    "1024.HK": "Kuaishou Technology",
    "0960.HK": "Longfor Group",
    "1810.HK": "Xiaomi Corporation",
    "2382.HK": "Sunny Optical Technology",
    "9888.HK": "Baidu",
    # ── Singapore ──
    "D05.SI":   "DBS Group Holdings",
    "O39.SI":   "OCBC Bank",
    "U11.SI":   "United Overseas Bank",
    "Z74.SI":   "Singapore Telecommunications",
    "C6L.SI":   "Singapore Airlines",
    "S68.SI":   "Singapore Exchange",
    "U96.SI":   "Sembcorp Industries",
    "C38U.SI":  "CapitaLand Ascendas REIT",
    "A17U.SI":  "Ascendas REIT",
    "ME8U.SI":  "Mapletree Industrial Trust",
    "N2IU.SI":  "Mapletree Pan Asia Commercial Trust",
    "H78.SI":   "Hongkong Land Holdings",
    "BS6.SI":   "Yangzijiang Shipbuilding",
    "BN4.SI":   "Keppel Corporation",
    "U14.SI":   "UOL Group",
    "V03.SI":   "Venture Corporation",
    "S58.SI":   "SATS",
    "G13.SI":   "Genting Singapore",
    "C09.SI":   "City Developments",
    "9CI.SI":   "CapitaLand Investment",
    "F34.SI":   "Wilmar International",
    "J36.SI":   "Jardine Matheson Holdings",
    "S07.SI":   "Jardine Cycle & Carriage",
    "Y92.SI":   "Thai Beverage",
    "OV8.SI":   "Sheng Siong Group",
    "5E2.SI":   "Olam Group",
    "M44U.SI":  "Mapletree Logistics Trust",
    "BUOU.SI":  "Frasers Logistics & Commercial Trust",
    "K71U.SI":  "Keppel REIT",
}

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
