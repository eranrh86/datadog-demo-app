import os, sys, time, threading, random, json, ssl, urllib.request as _ureq
import logging

# Allow importing sibling modules from /scripts (ConfigMap mount)
sys.path.insert(0, '/scripts')

from flask import Flask, jsonify, request, g
from flask_cors import CORS

# ── Datadog APM + Structured Logging ────────────────────────────────────────
try:
    from ddtrace import tracer, Pin
    from ddtrace.contrib.logging import patch as dd_patch_logging
    dd_patch_logging()
    _DD_AVAILABLE = True
except ImportError:
    _DD_AVAILABLE = False

# JSON structured logger — DD agent picks this up and injects trace/span IDs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s [%(name)s] [dd.trace_id=%(dd.trace_id)s dd.span_id=%(dd.span_id)s] %(message)s',
)
logger = logging.getLogger("stocklens")

app = Flask(__name__)
CORS(app)

# Migratable state (seeded from env vars on CRIU restore)
request_count = int(os.environ.get("RESTORED_RC", "0"))
trade_count   = int(os.environ.get("RESTORED_TC", "0"))
pnl_total     = float(os.environ.get("RESTORED_PNL", "0.0"))
start_time    = time.time()
state_lock    = threading.Lock()

# Mutable stock list
DEFAULTS    = [
    # ── US Mega-cap ──────────────────────────────────────────────────────
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOG", "META", "TSLA", "AVGO",
    "JPM", "LLY", "V", "MA", "UNH", "XOM", "COST",
    # ── US Tech / Growth ─────────────────────────────────────────────────
    "NFLX", "AMD", "CRM", "ORCL", "ADBE", "NOW", "PANW",
    "DDOG", "CRWD", "PLTR", "ARM", "SMCI", "HOOD",
    # ── Market indices / ETFs (for market bar) ───────────────────────────
    "SPY", "QQQ", "DIA", "^VIX", "IWM",
    # ── Israeli stocks on NASDAQ/NYSE ────────────────────────────────────
    "CHKP", "CYBR", "NICE", "WIX", "MNDY", "GLBE", "INMD",
    "SEDG", "TSEM", "ESLT",
    # ── TASE — TA-35 core ────────────────────────────────────────────────
    "TEVA.TA", "POLI.TA", "LUMI.TA", "MSBI.TA", "DSCT.TA",
    "ICL.TA", "ESLT.TA", "BEZQ.TA", "NICE.TA", "CYBR.TA",
    "AZRG.TA", "ENLT.TA", "HARL.TA", "PHOE.TA", "CLAL.TA",
    "CEL.TA", "PTNR.TA", "MTRX.TA", "ELAL.TA",
]
stocks      = list(DEFAULTS)
stocks_lock = threading.Lock()

# Data caches (refreshed in background)
price_cache = {}   # sym -> {price, change, pct, ma50, ma100, ma200, volume, chart, _ts}
fund_cache  = {}   # sym -> {fundamentals}
data_lock   = threading.Lock()
loading_set = set()

# Recommendations cache
rec_cache = []
rec_lock  = threading.Lock()
REC_ORDER = {"strong_buy": 1, "buy": 2, "hold": 3, "underperform": 4, "sell": 5}

# ── Stock catalog for search autocomplete ──────────────────────
# Each entry: (symbol, full_name, exchange, sector, country_code)
CATALOG = [
    # US — Technology
    ("AAPL","Apple Inc","NASDAQ","Technology","US"),
    ("MSFT","Microsoft Corp","NASDAQ","Technology","US"),
    ("GOOGL","Alphabet Inc (Class A)","NASDAQ","Technology","US"),
    ("GOOG","Alphabet Inc (Class C)","NASDAQ","Technology","US"),
    ("AMZN","Amazon.com Inc","NASDAQ","Consumer Cyclical","US"),
    ("META","Meta Platforms Inc","NASDAQ","Technology","US"),
    ("NVDA","NVIDIA Corporation","NASDAQ","Technology","US"),
    ("TSLA","Tesla Inc","NASDAQ","Consumer Cyclical","US"),
    ("AMD","Advanced Micro Devices","NASDAQ","Technology","US"),
    ("INTC","Intel Corporation","NASDAQ","Technology","US"),
    ("QCOM","Qualcomm Inc","NASDAQ","Technology","US"),
    ("AVGO","Broadcom Inc","NASDAQ","Technology","US"),
    ("TXN","Texas Instruments","NASDAQ","Technology","US"),
    ("MU","Micron Technology","NASDAQ","Technology","US"),
    ("ASML","ASML Holding","NASDAQ","Technology","NL"),
    ("AMAT","Applied Materials","NASDAQ","Technology","US"),
    ("LRCX","Lam Research","NASDAQ","Technology","US"),
    ("KLAC","KLA Corporation","NASDAQ","Technology","US"),
    ("ADBE","Adobe Inc","NASDAQ","Technology","US"),
    ("CRM","Salesforce Inc","NYSE","Technology","US"),
    ("ORCL","Oracle Corporation","NYSE","Technology","US"),
    ("SAP","SAP SE","NYSE","Technology","DE"),
    ("NOW","ServiceNow Inc","NYSE","Technology","US"),
    ("SNOW","Snowflake Inc","NYSE","Technology","US"),
    ("PLTR","Palantir Technologies","NASDAQ","Technology","US"),
    ("NFLX","Netflix Inc","NASDAQ","Communication","US"),
    ("DIS","Walt Disney Co","NYSE","Communication","US"),
    ("SPOT","Spotify Technology","NYSE","Communication","SE"),
    ("SNAP","Snap Inc","NYSE","Communication","US"),
    ("PINS","Pinterest Inc","NYSE","Communication","US"),
    ("UBER","Uber Technologies","NYSE","Technology","US"),
    ("LYFT","Lyft Inc","NASDAQ","Technology","US"),
    ("SHOP","Shopify Inc","NYSE","Technology","CA"),
    ("SQ","Block Inc","NYSE","Technology","US"),
    ("COIN","Coinbase Global","NASDAQ","Financial","US"),
    ("PYPL","PayPal Holdings","NASDAQ","Financial","US"),
    # US — Finance
    ("JPM","JPMorgan Chase","NYSE","Financial","US"),
    ("BAC","Bank of America","NYSE","Financial","US"),
    ("GS","Goldman Sachs","NYSE","Financial","US"),
    ("MS","Morgan Stanley","NYSE","Financial","US"),
    ("WFC","Wells Fargo","NYSE","Financial","US"),
    ("C","Citigroup Inc","NYSE","Financial","US"),
    ("V","Visa Inc","NYSE","Financial","US"),
    ("MA","Mastercard Inc","NYSE","Financial","US"),
    ("AXP","American Express","NYSE","Financial","US"),
    ("BLK","BlackRock Inc","NYSE","Financial","US"),
    ("SCHW","Charles Schwab","NYSE","Financial","US"),
    # US — Healthcare
    ("JNJ","Johnson & Johnson","NYSE","Healthcare","US"),
    ("PFE","Pfizer Inc","NYSE","Healthcare","US"),
    ("MRK","Merck & Co","NYSE","Healthcare","US"),
    ("ABBV","AbbVie Inc","NYSE","Healthcare","US"),
    ("LLY","Eli Lilly and Company","NYSE","Healthcare","US"),
    ("UNH","UnitedHealth Group","NYSE","Healthcare","US"),
    ("BMY","Bristol-Myers Squibb","NYSE","Healthcare","US"),
    ("AMGN","Amgen Inc","NASDAQ","Healthcare","US"),
    ("GILD","Gilead Sciences","NASDAQ","Healthcare","US"),
    ("BIIB","Biogen Inc","NASDAQ","Healthcare","US"),
    ("MRNA","Moderna Inc","NASDAQ","Healthcare","US"),
    ("ISRG","Intuitive Surgical","NASDAQ","Healthcare","US"),
    # US — Energy
    ("XOM","Exxon Mobil Corp","NYSE","Energy","US"),
    ("CVX","Chevron Corporation","NYSE","Energy","US"),
    ("COP","ConocoPhillips","NYSE","Energy","US"),
    ("SLB","SLB (Schlumberger)","NYSE","Energy","US"),
    ("EOG","EOG Resources","NYSE","Energy","US"),
    # US — Consumer
    ("KO","Coca-Cola Company","NYSE","Consumer Defensive","US"),
    ("PEP","PepsiCo Inc","NASDAQ","Consumer Defensive","US"),
    ("WMT","Walmart Inc","NYSE","Consumer Defensive","US"),
    ("COST","Costco Wholesale","NASDAQ","Consumer Defensive","US"),
    ("MCD","McDonald's Corp","NYSE","Consumer Cyclical","US"),
    ("SBUX","Starbucks Corp","NASDAQ","Consumer Cyclical","US"),
    ("NKE","Nike Inc","NYSE","Consumer Cyclical","US"),
    ("HD","Home Depot Inc","NYSE","Consumer Cyclical","US"),
    ("LOW","Lowe's Companies","NYSE","Consumer Cyclical","US"),
    # US — Industrial
    ("BA","Boeing Company","NYSE","Industrials","US"),
    ("CAT","Caterpillar Inc","NYSE","Industrials","US"),
    ("GE","GE Aerospace","NYSE","Industrials","US"),
    ("HON","Honeywell International","NASDAQ","Industrials","US"),
    ("RTX","RTX Corporation","NYSE","Industrials","US"),
    ("LMT","Lockheed Martin","NYSE","Industrials","US"),
    ("NOC","Northrop Grumman","NYSE","Industrials","US"),
    ("UPS","United Parcel Service","NYSE","Industrials","US"),
    ("FDX","FedEx Corporation","NYSE","Industrials","US"),
    # US — Real Estate & Utilities
    ("AMT","American Tower Corp","NYSE","Real Estate","US"),
    ("PLD","Prologis Inc","NYSE","Real Estate","US"),
    ("NEE","NextEra Energy","NYSE","Utilities","US"),
    # Israeli — NASDAQ/NYSE
    ("CHKP","Check Point Software","NASDAQ","Technology","IL"),
    ("NICE","NICE Systems Ltd","NASDAQ","Technology","IL"),
    ("WIX","Wix.com Ltd","NASDAQ","Technology","IL"),
    ("MNDY","Monday.com Ltd","NASDAQ","Technology","IL"),
    ("GLBE","Global-E Online","NASDAQ","Technology","IL"),
    ("CEVA","CEVA Inc","NASDAQ","Technology","IL"),
    ("RDWR","Radware Ltd","NASDAQ","Technology","IL"),
    ("TSEM","Tower Semiconductor","NASDAQ","Technology","IL"),
    ("DOX","Amdocs Limited","NASDAQ","Technology","IL"),
    ("ESLT","Elbit Systems of America","NASDAQ","Industrials","IL"),
    # Israeli — TASE
    ("TEVA.TA","Teva Pharmaceutical","TASE","Healthcare","IL"),
    ("POLI.TA","Bank Hapoalim","TASE","Financial","IL"),
    ("LUMI.TA","Bank Leumi","TASE","Financial","IL"),
    ("DSCT.TA","Israel Discount Bank","TASE","Financial","IL"),
    ("FIBI.TA","First International Bank","TASE","Financial","IL"),
    ("MSBI.TA","Mizrahi Tefahot Bank","TASE","Financial","IL"),
    ("ICL.TA","ICL Group (Israel Chemicals)","TASE","Materials","IL"),
    ("ESLT.TA","Elbit Systems","TASE","Industrials","IL"),
    ("BEZQ.TA","Bezeq Israeli Telecom","TASE","Communication","IL"),
    ("NICE.TA","NICE Systems","TASE","Technology","IL"),
    ("CHKP.TA","Check Point Software","TASE","Technology","IL"),
    ("TSEM.TA","Tower Semiconductor","TASE","Technology","IL"),
    ("ELAL.TA","El Al Israel Airlines","TASE","Industrials","IL"),
    ("PHOE.TA","Phoenix Holdings","TASE","Financial","IL"),
    ("CLAL.TA","Clal Insurance","TASE","Financial","IL"),
    ("ENLT.TA","Enlight Renewable Energy","TASE","Utilities","IL"),
    ("RDWR.TA","Radware Ltd","TASE","Technology","IL"),
    # Israeli — TASE (TA-35 extended)
    ("HARL.TA","Harel Insurance Investments","TASE","Financial","IL"),
    ("MGDL.TA","Migdal Insurance","TASE","Financial","IL"),
    ("AZRG.TA","Azrieli Group","TASE","Real Estate","IL"),
    ("AMOT.TA","Amot Investments","TASE","Real Estate","IL"),
    ("GVYM.TA","Gav-Yam Lands Corp","TASE","Real Estate","IL"),
    ("SAE.TA","Shufersal Ltd","TASE","Consumer Defensive","IL"),
    ("PTNR.TA","Partner Communications","TASE","Communication","IL"),
    ("CEL.TA","Cellcom Israel","TASE","Communication","IL"),
    ("NWMD.TA","NewMed Energy","TASE","Energy","IL"),
    ("DLEKG.TA","Delek Group","TASE","Energy","IL"),
    ("ORL.TA","Bazan Oil Refineries","TASE","Energy","IL"),
    ("NXSN.TA","Next Vision Stabilized Systems","TASE","Industrials","IL"),
    ("ELCO.TA","Elco Holdings","TASE","Industrials","IL"),
    ("ISIN.TA","Israel Corp","TASE","Industrials","IL"),
    ("MTDS.TA","Meitav Investment House","TASE","Financial","IL"),
    ("ALGS.TA","Algomizer","TASE","Technology","IL"),
    ("SPEN.TA","Shapir Engineering","TASE","Industrials","IL"),
    ("FORTY.TA","Formula Systems","TASE","Technology","IL"),
    ("BONS.TA","Bonus BioGroup","TASE","Healthcare","IL"),
    ("OPCT.TA","OPC Energy","TASE","Utilities","IL"),
    ("GFC.TA","GFC Industries","TASE","Industrials","IL"),
    # Israeli — NASDAQ/NYSE (additional)
    ("INMD","InMode Ltd","NASDAQ","Healthcare","IL"),
    ("FVRR","Fiverr International","NYSE","Technology","IL"),
    ("KRNT","Kornit Digital","NASDAQ","Industrials","IL"),
    ("PAYO","Payoneer Global","NASDAQ","Financial","IL"),
    ("ALLT","Allot Communications","NASDAQ","Technology","IL"),
    ("NNDM","Nano Dimension","NASDAQ","Technology","IL"),
    # Israeli NASDAQ — additional
    ("CYBR","CyberArk Software","NASDAQ","Technology","IL"),
    ("SEDG","SolarEdge Technologies","NASDAQ","Technology","IL"),
    ("CAMT","Camtek Ltd","NASDAQ","Technology","IL"),
    ("SPNS","Sapiens International","NASDAQ","Technology","IL"),
    ("KMDA","Kamada Ltd","NASDAQ","Healthcare","IL"),
    ("GILT","Gilat Satellite Networks","NASDAQ","Technology","IL"),
    ("PERI","Perion Network","NASDAQ","Technology","IL"),
    ("ITRN","Ituran Location and Control","NASDAQ","Technology","IL"),
    ("MGIC","Magic Software Enterprises","NASDAQ","Technology","IL"),
    ("KPLT","Katapult Holdings","NASDAQ","Financial","IL"),
    # Israeli — TASE (TA-125 extended)
    ("CAMT.TA","Camtek Ltd","TASE","Technology","IL"),
    ("HLAN.TA","Hilan Technologies","TASE","Technology","IL"),
    ("MLSR.TA","Melisron Real Estate","TASE","Real Estate","IL"),
    ("ISRO.TA","Isrotel Hotels","TASE","Consumer Cyclical","IL"),
    ("FTAL.TA","Fattal Hotels","TASE","Consumer Cyclical","IL"),
    ("ELRN.TA","Elron Electronic Industries","TASE","Technology","IL"),
    ("SPNS.TA","Sapiens International","TASE","Technology","IL"),
    ("KMDA.TA","Kamada Ltd","TASE","Healthcare","IL"),
    ("GILT.TA","Gilat Satellite Networks","TASE","Technology","IL"),
    ("PERI.TA","Perion Network","TASE","Technology","IL"),
    ("CYBR.TA","CyberArk Software","TASE","Technology","IL"),
    ("SEDG.TA","SolarEdge Technologies","TASE","Technology","IL"),
    ("MNDY.TA","Monday.com","TASE","Technology","IL"),
    ("WKME.TA","WalkMe Ltd","TASE","Technology","IL"),
    ("AYAL.TA","Ayalon Insurance","TASE","Financial","IL"),
    ("ILDC.TA","IDB Development Corp","TASE","Financial","IL"),
    ("DANE.TA","Dan Hotels Corp","TASE","Consumer Cyclical","IL"),
    ("STRS.TA","Strauss Group","TASE","Consumer Defensive","IL"),
    ("OSEM.TA","Osem Investments","TASE","Consumer Defensive","IL"),
    ("MGIC.TA","Magic Software Enterprises","TASE","Technology","IL"),
    ("ITRN.TA","Ituran Location and Control","TASE","Technology","IL"),
    ("ORBT.TA","Orbit International","TASE","Industrials","IL"),
    ("AFHL.TA","Africa Israel Holdings","TASE","Real Estate","IL"),
    ("ALHE.TA","Allied Healthcare Israel","TASE","Healthcare","IL"),
    ("DPPA.TA","Discount Investments","TASE","Financial","IL"),
    ("RTEN.TA","Roten Real Estate","TASE","Real Estate","IL"),
    ("CLIS.TA","Clal Industries","TASE","Industrials","IL"),
    ("BYSD.TA","Bydesign Group","TASE","Consumer Cyclical","IL"),
    # US — More Tech / Cloud / Security
    ("DDOG","Datadog Inc","NASDAQ","Technology","US"),
    ("CRWD","CrowdStrike Holdings","NASDAQ","Technology","US"),
    ("ZS","Zscaler Inc","NASDAQ","Technology","US"),
    ("PANW","Palo Alto Networks","NASDAQ","Technology","US"),
    ("NET","Cloudflare Inc","NYSE","Technology","US"),
    ("OKTA","Okta Inc","NASDAQ","Technology","US"),
    ("MDB","MongoDB Inc","NASDAQ","Technology","US"),
    ("TTD","The Trade Desk","NASDAQ","Technology","US"),
    ("RBLX","Roblox Corp","NYSE","Communication","US"),
    ("ROKU","Roku Inc","NASDAQ","Communication","US"),
    ("ABNB","Airbnb Inc","NASDAQ","Consumer Cyclical","US"),
    ("DASH","DoorDash Inc","NYSE","Consumer Cyclical","US"),
    ("ARM","Arm Holdings","NASDAQ","Technology","GB"),
    ("SMCI","Super Micro Computer","NASDAQ","Technology","US"),
    ("DELL","Dell Technologies","NYSE","Technology","US"),
    ("HPQ","HP Inc","NYSE","Technology","US"),
    ("CSCO","Cisco Systems","NASDAQ","Technology","US"),
    ("IBM","IBM Corporation","NYSE","Technology","US"),
    ("ACN","Accenture plc","NYSE","Technology","IE"),
    # US — SaaS / Cloud / Enterprise
    ("ZM","Zoom Video Communications","NASDAQ","Technology","US"),
    ("WDAY","Workday Inc","NASDAQ","Technology","US"),
    ("HUBS","HubSpot Inc","NYSE","Technology","US"),
    ("ADSK","Autodesk Inc","NASDAQ","Technology","US"),
    ("VEEV","Veeva Systems Inc","NYSE","Healthcare","US"),
    ("TWLO","Twilio Inc","NYSE","Technology","US"),
    ("CFLT","Confluent Inc","NASDAQ","Technology","US"),
    ("ZI","ZoomInfo Technologies","NASDAQ","Technology","US"),
    ("BILL","Bill.com Holdings","NYSE","Technology","US"),
    ("PCTY","Paylocity Holding","NASDAQ","Technology","US"),
    ("PAYC","Paycom Software","NYSE","Technology","US"),
    ("SMAR","Smartsheet Inc","NYSE","Technology","US"),
    ("NTNX","Nutanix Inc","NASDAQ","Technology","US"),
    ("DOCN","DigitalOcean Holdings","NYSE","Technology","US"),
    ("GTLB","GitLab Inc","NASDAQ","Technology","US"),
    ("PATH","UiPath Inc","NYSE","Technology","US"),
    ("ESTC","Elastic NV","NYSE","Technology","US"),
    ("CDNS","Cadence Design Systems","NASDAQ","Technology","US"),
    ("SNPS","Synopsys Inc","NASDAQ","Technology","US"),
    ("ANSS","Ansys Inc","NASDAQ","Technology","US"),
    ("FTNT","Fortinet Inc","NASDAQ","Technology","US"),
    ("AI","C3.ai Inc","NYSE","Technology","US"),
    # US — Fintech / Finance
    ("SOFI","SoFi Technologies","NASDAQ","Financial","US"),
    ("HOOD","Robinhood Markets","NASDAQ","Financial","US"),
    ("AFRM","Affirm Holdings","NASDAQ","Financial","US"),
    ("UPST","Upstart Holdings","NASDAQ","Financial","US"),
    ("MSCI","MSCI Inc","NYSE","Financial","US"),
    ("CME","CME Group Inc","NASDAQ","Financial","US"),
    ("NDAQ","Nasdaq Inc","NASDAQ","Financial","US"),
    # US — EV / Clean Energy
    ("RIVN","Rivian Automotive","NASDAQ","Consumer Cyclical","US"),
    ("LCID","Lucid Group","NASDAQ","Consumer Cyclical","US"),
    ("ENPH","Enphase Energy","NASDAQ","Technology","US"),
    ("FSLR","First Solar Inc","NASDAQ","Technology","US"),
    ("RUN","Sunrun Inc","NASDAQ","Utilities","US"),
    ("BE","Bloom Energy Corp","NYSE","Utilities","US"),
    # US — Gaming / Entertainment
    ("DKNG","DraftKings Inc","NASDAQ","Consumer Cyclical","US"),
    ("EA","Electronic Arts Inc","NASDAQ","Communication","US"),
    ("TTWO","Take-Two Interactive","NASDAQ","Communication","US"),
    # US — Healthcare / Biotech (additional)
    ("DXCM","DexCom Inc","NASDAQ","Healthcare","US"),
    ("IDXX","IDEXX Laboratories","NASDAQ","Healthcare","US"),
    ("VRTX","Vertex Pharmaceuticals","NASDAQ","Healthcare","US"),
    ("REGN","Regeneron Pharmaceuticals","NASDAQ","Healthcare","US"),
    ("ILMN","Illumina Inc","NASDAQ","Healthcare","US"),
    ("TDOC","Teladoc Health","NYSE","Healthcare","US"),
    ("HIMS","Hims & Hers Health","NYSE","Healthcare","US"),
    ("NTRA","Natera Inc","NASDAQ","Healthcare","US"),
    ("RXRX","Recursion Pharmaceuticals","NASDAQ","Healthcare","US"),
    # US — Consumer / E-commerce
    ("ETSY","Etsy Inc","NASDAQ","Consumer Cyclical","US"),
    ("CHWY","Chewy Inc","NYSE","Consumer Cyclical","US"),
    ("W","Wayfair Inc","NYSE","Consumer Cyclical","US"),
    ("CVNA","Carvana Co","NYSE","Consumer Cyclical","US"),
    ("LULU","Lululemon Athletica","NASDAQ","Consumer Cyclical","CA"),
    ("ROST","Ross Stores Inc","NASDAQ","Consumer Defensive","US"),
    # US — Semiconductor (additional)
    ("MRVL","Marvell Technology","NASDAQ","Technology","US"),
    ("MPWR","Monolithic Power Systems","NASDAQ","Technology","US"),
    ("SWKS","Skyworks Solutions","NASDAQ","Technology","US"),
    ("ON","ON Semiconductor","NASDAQ","Technology","US"),
    ("WOLF","Wolfspeed Inc","NYSE","Technology","US"),
    ("ACLS","Axcelis Technologies","NASDAQ","Technology","US"),
    # US — Space / Quantum / AI
    ("RKLB","Rocket Lab USA","NASDAQ","Industrials","US"),
    ("JOBY","Joby Aviation","NYSE","Industrials","US"),
    ("IONQ","IonQ Inc","NYSE","Technology","US"),
    ("SOUN","SoundHound AI","NASDAQ","Technology","US"),
    ("NBIS","Nebius Group N.V.","NASDAQ","Technology","NL"),
    # Global ADR / Large-Cap
    ("MELI","MercadoLibre Inc","NASDAQ","Consumer Cyclical","AR"),
    ("SE","Sea Limited","NYSE","Technology","SG"),
    ("BIDU","Baidu Inc","NASDAQ","Technology","CN"),
    ("PDD","PDD Holdings","NASDAQ","Consumer Cyclical","CN"),
    ("TSM","Taiwan Semiconductor","NYSE","Technology","TW"),
    ("NVO","Novo Nordisk","NYSE","Healthcare","DK"),
    ("BABA","Alibaba Group","NYSE","Consumer Cyclical","CN"),
    ("JD","JD.com Inc","NASDAQ","Consumer Cyclical","CN"),
    # ETFs
    ("SPY","SPDR S&P 500 ETF","NYSE","ETF","US"),
    ("QQQ","Invesco QQQ Trust","NASDAQ","ETF","US"),
    ("IWM","iShares Russell 2000","NYSE","ETF","US"),
    ("GLD","SPDR Gold Shares","NYSE","ETF","US"),
    ("SLV","iShares Silver Trust","NYSE","ETF","US"),
    ("USO","United States Oil Fund","NYSE","ETF","US"),
    ("TLT","iShares 20+ Year Treasury","NASDAQ","ETF","US"),
    ("VIX","CBOE Volatility Index","CBOE","Index","US"),
    # Crypto
    ("BTC-USD","Bitcoin","Crypto","Cryptocurrency","Global"),
    ("ETH-USD","Ethereum","Crypto","Cryptocurrency","Global"),
    ("SOL-USD","Solana","Crypto","Cryptocurrency","Global"),
    ("XRP-USD","XRP / Ripple","Crypto","Cryptocurrency","Global"),
    ("BNB-USD","Binance Coin","Crypto","Cryptocurrency","Global"),
    ("DOGE-USD","Dogecoin","Crypto","Cryptocurrency","Global"),
    ("ADA-USD","Cardano","Crypto","Cryptocurrency","Global"),
    ("AVAX-USD","Avalanche","Crypto","Cryptocurrency","Global"),
    # Commodities
    ("GC=F","Gold Futures","COMEX","Commodities","Global"),
    ("SI=F","Silver Futures","COMEX","Commodities","Global"),
    ("CL=F","Crude Oil WTI","NYMEX","Commodities","Global"),
    ("NG=F","Natural Gas","NYMEX","Commodities","Global"),
    ("HG=F","Copper Futures","COMEX","Commodities","Global"),
    # Forex
    ("ILS=X","USD/ILS Exchange Rate","Forex","Forex","IL"),
    ("EURUSD=X","EUR/USD Rate","Forex","Forex","EU"),
    ("GBPUSD=X","GBP/USD Rate","Forex","Forex","GB"),
    ("JPY=X","USD/JPY Rate","Forex","Forex","JP"),
    ("CADUSD=X","CAD/USD Rate","Forex","Forex","CA"),
    ("AUDUSD=X","AUD/USD Rate","Forex","Forex","AU"),
    ("CHFUSD=X","CHF/USD Rate","Forex","Forex","CH"),
    ("CNHUSD=X","CNH/USD Rate","Forex","Forex","CN"),
    ("INRUSD=X","INR/USD Rate","Forex","Forex","IN"),
    ("BRLUSD=X","BRL/USD Rate","Forex","Forex","BR"),
    ("KRWUSD=X","KRW/USD Rate","Forex","Forex","KR"),
    # ─── Global Indexes ───────────────────────────────────────────────
    ("^GSPC","S&P 500 Index","INDEX","Index","US"),
    ("^IXIC","NASDAQ Composite","INDEX","Index","US"),
    ("^DJI","Dow Jones Industrial Average","INDEX","Index","US"),
    ("^RUT","Russell 2000 Index","INDEX","Index","US"),
    ("^TA35.TA","TA-35 Index","INDEX","Index","IL"),
    ("^TA125.TA","TA-125 Index","INDEX","Index","IL"),
    ("^TA90.TA","TA-90 Index","INDEX","Index","IL"),
    ("^FTSE","FTSE 100 Index","INDEX","Index","GB"),
    ("^GDAXI","DAX 40 Index","INDEX","Index","DE"),
    ("^FCHI","CAC 40 Index","INDEX","Index","FR"),
    ("^N225","Nikkei 225","INDEX","Index","JP"),
    ("^HSI","Hang Seng Index","INDEX","Index","HK"),
    ("^STOXX50E","EURO STOXX 50","INDEX","Index","EU"),
    ("^BSESN","BSE SENSEX","INDEX","Index","IN"),
    ("^KS11","KOSPI Index","INDEX","Index","KR"),
    ("^AXJO","ASX 200","INDEX","Index","AU"),
    ("^BVSP","Bovespa Index","INDEX","Index","BR"),
    ("^AEX","AEX Amsterdam Index","INDEX","Index","NL"),
    ("^SSMI","Swiss Market Index","INDEX","Index","CH"),
    ("^IBEX","IBEX 35","INDEX","Index","ES"),
    ("^MXX","IPC Mexico","INDEX","Index","MX"),
    ("^AORD","All Ordinaries Australia","INDEX","Index","AU"),
    ("^STI","Straits Times Index","INDEX","Index","SG"),
    ("^NSEI","Nifty 50","INDEX","Index","IN"),
    # ─── Sector & Broad ETFs ──────────────────────────────────────────
    ("VTI","Vanguard Total Market ETF","NYSE","ETF","US"),
    ("VOO","Vanguard S&P 500 ETF","NYSE","ETF","US"),
    ("VEA","Vanguard Dev Markets ETF","NYSE","ETF","US"),
    ("VWO","Vanguard Emerging Mkts ETF","NYSE","ETF","US"),
    ("EEM","iShares MSCI Emerging Mkts","NYSE","ETF","US"),
    ("EWJ","iShares MSCI Japan ETF","NYSE","ETF","US"),
    ("EWZ","iShares MSCI Brazil ETF","NYSE","ETF","US"),
    ("FXI","iShares China Large-Cap","NYSE","ETF","CN"),
    ("KWEB","KraneShares CSI China Internet","NYSE","ETF","CN"),
    ("EWG","iShares MSCI Germany ETF","NYSE","ETF","DE"),
    ("EWU","iShares MSCI United Kingdom","NYSE","ETF","GB"),
    ("EWY","iShares MSCI South Korea","NYSE","ETF","KR"),
    ("EWA","iShares MSCI Australia ETF","NYSE","ETF","AU"),
    ("XLF","Financial Select Sector SPDR","NYSE","ETF","US"),
    ("XLK","Technology Select Sector SPDR","NYSE","ETF","US"),
    ("XLV","Health Care Select Sector SPDR","NYSE","ETF","US"),
    ("XLE","Energy Select Sector SPDR","NYSE","ETF","US"),
    ("XLY","Consumer Discret Select SPDR","NYSE","ETF","US"),
    ("XLP","Consumer Staples Select SPDR","NYSE","ETF","US"),
    ("XLI","Industrial Select Sector SPDR","NYSE","ETF","US"),
    ("XLB","Materials Select Sector SPDR","NYSE","ETF","US"),
    ("XLRE","Real Estate Select Sector SPDR","NYSE","ETF","US"),
    ("XLU","Utilities Select Sector SPDR","NYSE","ETF","US"),
    ("XLC","Communication Services SPDR","NYSE","ETF","US"),
    ("ARKK","ARK Innovation ETF","NYSE","ETF","US"),
    ("ARKG","ARK Genomic Revolution ETF","NYSE","ETF","US"),
    ("IBB","iShares Nasdaq Biotechnology","NASDAQ","ETF","US"),
    ("XBI","SPDR S&P Biotech ETF","NYSE","ETF","US"),
    ("SOXX","iShares Semiconductor ETF","NASDAQ","ETF","US"),
    ("SMH","VanEck Semiconductor ETF","NASDAQ","ETF","US"),
    ("GDX","VanEck Gold Miners ETF","NYSE","ETF","US"),
    ("GDXJ","VanEck Junior Gold Miners","NYSE","ETF","US"),
    ("VNQ","Vanguard Real Estate ETF","NYSE","ETF","US"),
    ("TAN","Invesco Solar ETF","NYSE","ETF","US"),
    ("ICLN","iShares Global Clean Energy","NASDAQ","ETF","US"),
    ("HYG","iShares iBoxx High Yield Corp","NYSE","ETF","US"),
    ("LQD","iShares iBoxx Invest Grade","NYSE","ETF","US"),
    ("AGG","iShares Core US Aggregate Bond","NYSE","ETF","US"),
    ("IEF","iShares 7-10 Year Treasury","NASDAQ","ETF","US"),
    ("BIL","SPDR 1-3 Month T-Bill ETF","NYSE","ETF","US"),
    ("TIPS","iShares TIPS Bond ETF","NYSE","ETF","US"),
    ("IAU","iShares Gold Trust","NYSE","ETF","US"),
    ("PDBC","Invesco Optimum Yield Commodity","NASDAQ","ETF","US"),
    ("IWF","iShares Russell 1000 Growth","NYSE","ETF","US"),
    ("IWD","iShares Russell 1000 Value","NYSE","ETF","US"),
    ("MDY","SPDR S&P MidCap 400 ETF","NYSE","ETF","US"),
    ("OIH","VanEck Oil Services ETF","NYSE","ETF","US"),
    ("XOP","SPDR S&P Oil & Gas ETF","NYSE","ETF","US"),
    ("CIBR","First Trust Cybersecurity ETF","NASDAQ","ETF","US"),
    ("HACK","ETFMG Prime Cyber Security ETF","NYSE","ETF","US"),
    # ─── Financials ───────────────────────────────────────────────────
    ("BRK-B","Berkshire Hathaway Class B","NYSE","Financial","US"),
    ("USB","US Bancorp","NYSE","Financial","US"),
    ("PNC","PNC Financial Services","NYSE","Financial","US"),
    ("TFC","Truist Financial Corp","NYSE","Financial","US"),
    ("COF","Capital One Financial","NYSE","Financial","US"),
    ("KEY","KeyCorp","NYSE","Financial","US"),
    ("RF","Regions Financial Corp","NYSE","Financial","US"),
    ("FITB","Fifth Third Bancorp","NASDAQ","Financial","US"),
    ("HBAN","Huntington Bancshares","NASDAQ","Financial","US"),
    ("CFG","Citizens Financial Group","NYSE","Financial","US"),
    ("MTB","M&T Bank Corp","NYSE","Financial","US"),
    ("ZION","Zions Bancorporation","NASDAQ","Financial","US"),
    ("FHN","First Horizon National","NYSE","Financial","US"),
    ("CB","Chubb Limited","NYSE","Financial","CH"),
    ("AON","Aon plc","NYSE","Financial","IE"),
    ("MMC","Marsh & McLennan Companies","NYSE","Financial","US"),
    ("TRV","Travelers Companies Inc","NYSE","Financial","US"),
    ("PGR","Progressive Corporation","NYSE","Financial","US"),
    ("AFL","Aflac Incorporated","NYSE","Financial","US"),
    ("AIG","American International Group","NYSE","Financial","US"),
    ("MET","MetLife Inc","NYSE","Financial","US"),
    ("PRU","Prudential Financial Inc","NYSE","Financial","US"),
    ("HIG","Hartford Financial Services","NYSE","Financial","US"),
    ("ALL","Allstate Corporation","NYSE","Financial","US"),
    ("LNC","Lincoln National Corp","NYSE","Financial","US"),
    ("ICE","Intercontinental Exchange","NYSE","Financial","US"),
    ("SPGI","S&P Global Inc","NYSE","Financial","US"),
    ("MCO","Moody's Corporation","NYSE","Financial","US"),
    ("WTW","Willis Towers Watson","NASDAQ","Financial","IE"),
    ("FDS","FactSet Research Systems","NASDAQ","Financial","US"),
    ("VRSK","Verisk Analytics Inc","NASDAQ","Financial","US"),
    ("IBKR","Interactive Brokers Group","NASDAQ","Financial","US"),
    ("RJF","Raymond James Financial","NYSE","Financial","US"),
    ("CINF","Cincinnati Financial Corp","NASDAQ","Financial","US"),
    ("HRB","H&R Block Inc","NYSE","Financial","US"),
    # ─── Healthcare ───────────────────────────────────────────────────
    ("TMO","Thermo Fisher Scientific","NYSE","Healthcare","US"),
    ("DHR","Danaher Corporation","NYSE","Healthcare","US"),
    ("ABT","Abbott Laboratories","NYSE","Healthcare","US"),
    ("MDT","Medtronic plc","NYSE","Healthcare","IE"),
    ("SYK","Stryker Corporation","NYSE","Healthcare","US"),
    ("BSX","Boston Scientific Corp","NYSE","Healthcare","US"),
    ("EW","Edwards Lifesciences","NYSE","Healthcare","US"),
    ("HCA","HCA Healthcare Inc","NYSE","Healthcare","US"),
    ("CVS","CVS Health Corporation","NYSE","Healthcare","US"),
    ("CI","Cigna Group","NYSE","Healthcare","US"),
    ("HUM","Humana Inc","NYSE","Healthcare","US"),
    ("MCK","McKesson Corporation","NYSE","Healthcare","US"),
    ("ABC","Cencora Inc","NYSE","Healthcare","US"),
    ("CAH","Cardinal Health Inc","NYSE","Healthcare","US"),
    ("BAX","Baxter International Inc","NYSE","Healthcare","US"),
    ("BDX","Becton Dickinson and Co","NYSE","Healthcare","US"),
    ("ZBH","Zimmer Biomet Holdings","NYSE","Healthcare","US"),
    ("HOLX","Hologic Inc","NASDAQ","Healthcare","US"),
    ("RMD","ResMed Inc","NYSE","Healthcare","US"),
    ("ALGN","Align Technology Inc","NASDAQ","Healthcare","US"),
    ("PODD","Insulet Corporation","NASDAQ","Healthcare","US"),
    ("NVCR","NovoCure Limited","NASDAQ","Healthcare","US"),
    ("INSP","Inspire Medical Systems","NYSE","Healthcare","US"),
    ("IRTC","iRhythm Technologies","NASDAQ","Healthcare","US"),
    ("EXAS","Exact Sciences Corp","NASDAQ","Healthcare","US"),
    ("GEHC","GE HealthCare Technologies","NASDAQ","Healthcare","US"),
    ("MOH","Molina Healthcare Inc","NYSE","Healthcare","US"),
    ("CNC","Centene Corporation","NYSE","Healthcare","US"),
    ("ELV","Elevance Health Inc","NYSE","Healthcare","US"),
    ("SEM","Select Medical Holdings","NYSE","Healthcare","US"),
    ("AMED","Amedisys Inc","NASDAQ","Healthcare","US"),
    ("ACAD","ACADIA Pharmaceuticals","NASDAQ","Healthcare","US"),
    ("ARWR","Arrowhead Pharmaceuticals","NASDAQ","Healthcare","US"),
    ("BEAM","Beam Therapeutics","NASDAQ","Healthcare","US"),
    ("CRSP","CRISPR Therapeutics","NASDAQ","Healthcare","CH"),
    ("EDIT","Editas Medicine Inc","NASDAQ","Healthcare","US"),
    ("NTLA","Intellia Therapeutics","NASDAQ","Healthcare","US"),
    ("RARE","Ultragenyx Pharmaceutical","NASDAQ","Healthcare","US"),
    # ─── Consumer Staples ─────────────────────────────────────────────
    ("PG","Procter & Gamble Company","NYSE","Consumer Defensive","US"),
    ("CL","Colgate-Palmolive Company","NYSE","Consumer Defensive","US"),
    ("KMB","Kimberly-Clark Corporation","NYSE","Consumer Defensive","US"),
    ("EL","Estee Lauder Companies","NYSE","Consumer Defensive","US"),
    ("MDLZ","Mondelez International","NASDAQ","Consumer Defensive","US"),
    ("GIS","General Mills Inc","NYSE","Consumer Defensive","US"),
    ("K","Kellanova","NYSE","Consumer Defensive","US"),
    ("CPB","Campbell Soup Company","NYSE","Consumer Defensive","US"),
    ("HSY","Hershey Company","NYSE","Consumer Defensive","US"),
    ("MKC","McCormick & Company","NYSE","Consumer Defensive","US"),
    ("HRL","Hormel Foods Corporation","NYSE","Consumer Defensive","US"),
    ("TSN","Tyson Foods Inc","NYSE","Consumer Defensive","US"),
    ("CAG","ConAgra Brands Inc","NYSE","Consumer Defensive","US"),
    ("SJM","J.M. Smucker Company","NYSE","Consumer Defensive","US"),
    ("MO","Altria Group Inc","NYSE","Consumer Defensive","US"),
    ("PM","Philip Morris International","NYSE","Consumer Defensive","US"),
    ("BTI","British American Tobacco","NYSE","Consumer Defensive","GB"),
    ("STZ","Constellation Brands Inc","NYSE","Consumer Defensive","US"),
    ("MNST","Monster Beverage Corporation","NASDAQ","Consumer Defensive","US"),
    ("TAP","Molson Coors Beverage Co","NYSE","Consumer Defensive","US"),
    ("SYY","Sysco Corporation","NYSE","Consumer Defensive","US"),
    ("DG","Dollar General Corporation","NYSE","Consumer Defensive","US"),
    ("DLTR","Dollar Tree Inc","NASDAQ","Consumer Defensive","US"),
    ("KR","Kroger Company","NYSE","Consumer Defensive","US"),
    ("CELH","Celsius Holdings Inc","NASDAQ","Consumer Defensive","US"),
    ("BJ","BJ's Wholesale Club Holdings","NYSE","Consumer Defensive","US"),
    ("PFGC","Performance Food Group","NYSE","Consumer Defensive","US"),
    ("USFD","US Foods Holding Corp","NYSE","Consumer Defensive","US"),
    # ─── Consumer Cyclical ────────────────────────────────────────────
    ("F","Ford Motor Company","NYSE","Consumer Cyclical","US"),
    ("GM","General Motors Company","NYSE","Consumer Cyclical","US"),
    ("STLA","Stellantis N.V.","NYSE","Consumer Cyclical","NL"),
    ("TM","Toyota Motor Corporation","NYSE","Consumer Cyclical","JP"),
    ("HMC","Honda Motor Co Ltd","NYSE","Consumer Cyclical","JP"),
    ("BMWYY","BMW Group ADR","OTC","Consumer Cyclical","DE"),
    ("VWAGY","Volkswagen AG ADR","OTC","Consumer Cyclical","DE"),
    ("LI","Li Auto Inc","NASDAQ","Consumer Cyclical","CN"),
    ("NIO","NIO Inc","NYSE","Consumer Cyclical","CN"),
    ("XPEV","XPeng Inc","NYSE","Consumer Cyclical","CN"),
    ("TJX","TJX Companies Inc","NYSE","Consumer Cyclical","US"),
    ("BURL","Burlington Stores Inc","NYSE","Consumer Cyclical","US"),
    ("FIVE","Five Below Inc","NASDAQ","Consumer Cyclical","US"),
    ("AZO","AutoZone Inc","NYSE","Consumer Cyclical","US"),
    ("ORLY","O'Reilly Automotive Inc","NASDAQ","Consumer Cyclical","US"),
    ("AAP","Advance Auto Parts Inc","NYSE","Consumer Cyclical","US"),
    ("KSS","Kohl's Corporation","NYSE","Consumer Cyclical","US"),
    ("M","Macy's Inc","NYSE","Consumer Cyclical","US"),
    ("ANF","Abercrombie & Fitch Co","NYSE","Consumer Cyclical","US"),
    ("PVH","PVH Corp","NYSE","Consumer Cyclical","US"),
    ("RL","Ralph Lauren Corporation","NYSE","Consumer Cyclical","US"),
    ("VFC","VF Corporation","NYSE","Consumer Cyclical","US"),
    ("PHM","PulteGroup Inc","NYSE","Consumer Cyclical","US"),
    ("DHI","D.R. Horton Inc","NYSE","Consumer Cyclical","US"),
    ("LEN","Lennar Corporation","NYSE","Consumer Cyclical","US"),
    ("TOL","Toll Brothers Inc","NYSE","Consumer Cyclical","US"),
    ("NVR","NVR Inc","NYSE","Consumer Cyclical","US"),
    ("KBH","KB Home","NYSE","Consumer Cyclical","US"),
    ("CCL","Carnival Corporation","NYSE","Consumer Cyclical","US"),
    ("RCL","Royal Caribbean Group","NYSE","Consumer Cyclical","US"),
    ("NCLH","Norwegian Cruise Line Holdings","NYSE","Consumer Cyclical","US"),
    ("MAR","Marriott International","NASDAQ","Consumer Cyclical","US"),
    ("HLT","Hilton Worldwide Holdings","NYSE","Consumer Cyclical","US"),
    ("H","Hyatt Hotels Corporation","NYSE","Consumer Cyclical","US"),
    ("WYNN","Wynn Resorts Limited","NASDAQ","Consumer Cyclical","US"),
    ("MGM","MGM Resorts International","NYSE","Consumer Cyclical","US"),
    ("LVS","Las Vegas Sands Corp","NYSE","Consumer Cyclical","US"),
    ("CZR","Caesars Entertainment Inc","NASDAQ","Consumer Cyclical","US"),
    ("PENN","Penn Entertainment Inc","NASDAQ","Consumer Cyclical","US"),
    ("YUM","Yum! Brands Inc","NYSE","Consumer Cyclical","US"),
    ("QSR","Restaurant Brands Intl","NYSE","Consumer Cyclical","CA"),
    ("DPZ","Domino's Pizza Inc","NASDAQ","Consumer Cyclical","US"),
    ("CMG","Chipotle Mexican Grill","NYSE","Consumer Cyclical","US"),
    ("BJRI","BJ's Restaurants Inc","NASDAQ","Consumer Cyclical","US"),
    ("SFM","Sprouts Farmers Market","NASDAQ","Consumer Cyclical","US"),
    # ─── Industrials ──────────────────────────────────────────────────
    ("UNP","Union Pacific Corporation","NYSE","Industrials","US"),
    ("CSX","CSX Corporation","NASDAQ","Industrials","US"),
    ("NSC","Norfolk Southern Corp","NYSE","Industrials","US"),
    ("CP","Canadian Pacific Kansas City","NYSE","Industrials","CA"),
    ("CNI","Canadian National Railway","NYSE","Industrials","CA"),
    ("EMR","Emerson Electric Co","NYSE","Industrials","US"),
    ("ETN","Eaton Corporation plc","NYSE","Industrials","IE"),
    ("PH","Parker-Hannifin Corporation","NYSE","Industrials","US"),
    ("ROK","Rockwell Automation Inc","NYSE","Industrials","US"),
    ("AME","AMETEK Inc","NYSE","Industrials","US"),
    ("ITW","Illinois Tool Works Inc","NASDAQ","Industrials","US"),
    ("CMI","Cummins Inc","NYSE","Industrials","US"),
    ("MMM","3M Company","NYSE","Industrials","US"),
    ("GD","General Dynamics Corp","NYSE","Industrials","US"),
    ("HII","Huntington Ingalls Industries","NYSE","Industrials","US"),
    ("TXT","Textron Inc","NYSE","Industrials","US"),
    ("HWM","Howmet Aerospace Inc","NYSE","Industrials","US"),
    ("LHX","L3Harris Technologies Inc","NYSE","Industrials","US"),
    ("LDOS","Leidos Holdings Inc","NYSE","Industrials","US"),
    ("BAH","Booz Allen Hamilton Holding","NYSE","Industrials","US"),
    ("SAIC","Science Applications Intl","NYSE","Industrials","US"),
    ("AXON","Axon Enterprise Inc","NASDAQ","Industrials","US"),
    ("WM","Waste Management Inc","NYSE","Industrials","US"),
    ("RSG","Republic Services Inc","NYSE","Industrials","US"),
    ("CLH","Clean Harbors Inc","NYSE","Industrials","US"),
    ("WCN","Waste Connections Inc","NYSE","Industrials","CA"),
    ("FAST","Fastenal Company","NASDAQ","Industrials","US"),
    ("GWW","W.W. Grainger Inc","NYSE","Industrials","US"),
    ("TT","Trane Technologies plc","NYSE","Industrials","IE"),
    ("CARR","Carrier Global Corporation","NYSE","Industrials","US"),
    ("OTIS","Otis Worldwide Corporation","NYSE","Industrials","US"),
    ("JCI","Johnson Controls International","NYSE","Industrials","IE"),
    ("PCAR","PACCAR Inc","NASDAQ","Industrials","US"),
    ("DE","Deere & Company","NYSE","Industrials","US"),
    ("AGCO","AGCO Corporation","NYSE","Industrials","US"),
    ("TDG","TransDigm Group Inc","NYSE","Industrials","US"),
    ("CHRW","C.H. Robinson Worldwide","NASDAQ","Industrials","US"),
    ("EXPD","Expeditors International","NASDAQ","Industrials","US"),
    ("XPO","XPO Inc","NYSE","Industrials","US"),
    ("ODFL","Old Dominion Freight Line","NASDAQ","Industrials","US"),
    ("JBHT","J.B. Hunt Transport Services","NASDAQ","Industrials","US"),
    ("DAL","Delta Air Lines Inc","NYSE","Industrials","US"),
    ("UAL","United Airlines Holdings","NASDAQ","Industrials","US"),
    ("AAL","American Airlines Group","NASDAQ","Industrials","US"),
    ("LUV","Southwest Airlines Co","NYSE","Industrials","US"),
    ("ALK","Alaska Air Group Inc","NYSE","Industrials","US"),
    ("JBLU","JetBlue Airways Corp","NASDAQ","Industrials","US"),
    ("SAVE","Spirit Airlines Inc","NYSE","Industrials","US"),
    ("FLR","Fluor Corporation","NYSE","Industrials","US"),
    ("J","Jacobs Solutions Inc","NYSE","Industrials","US"),
    ("ACM","AECOM","NYSE","Industrials","US"),
    ("PWR","Quanta Services Inc","NYSE","Industrials","US"),
    ("MTZ","MasTec Inc","NYSE","Industrials","US"),
    ("ROLL","RBC Bearings Inc","NASDAQ","Industrials","US"),
    ("GNRC","Generac Holdings Inc","NYSE","Industrials","US"),
    ("AWI","Armstrong World Industries","NYSE","Industrials","US"),
    # ─── Energy ───────────────────────────────────────────────────────
    ("OXY","Occidental Petroleum Corp","NYSE","Energy","US"),
    ("VLO","Valero Energy Corporation","NYSE","Energy","US"),
    ("MPC","Marathon Petroleum Corp","NYSE","Energy","US"),
    ("PSX","Phillips 66","NYSE","Energy","US"),
    ("HES","Hess Corporation","NYSE","Energy","US"),
    ("DVN","Devon Energy Corporation","NYSE","Energy","US"),
    ("FANG","Diamondback Energy Inc","NASDAQ","Energy","US"),
    ("MRO","Marathon Oil Corporation","NYSE","Energy","US"),
    ("APA","APA Corporation","NASDAQ","Energy","US"),
    ("HAL","Halliburton Company","NYSE","Energy","US"),
    ("BKR","Baker Hughes Company","NASDAQ","Energy","US"),
    ("OKE","ONEOK Inc","NYSE","Energy","US"),
    ("KMI","Kinder Morgan Inc","NYSE","Energy","US"),
    ("WMB","Williams Companies Inc","NYSE","Energy","US"),
    ("LNG","Cheniere Energy Inc","NYSE","Energy","US"),
    ("OVV","Ovintiv Inc","NYSE","Energy","CA"),
    ("CTRA","Coterra Energy Inc","NYSE","Energy","US"),
    ("SM","SM Energy Company","NYSE","Energy","US"),
    ("CNX","CNX Resources Corp","NYSE","Energy","US"),
    ("AR","Antero Resources Corp","NYSE","Energy","US"),
    ("EQT","EQT Corporation","NYSE","Energy","US"),
    ("SWN","SWN Communities","NYSE","Energy","US"),
    ("RRC","Range Resources Corp","NYSE","Energy","US"),
    ("MTDR","Matador Resources Co","NYSE","Energy","US"),
    ("CHRD","Chord Energy Corp","NASDAQ","Energy","US"),
    # ─── Utilities ────────────────────────────────────────────────────
    ("DUK","Duke Energy Corporation","NYSE","Utilities","US"),
    ("SO","Southern Company","NYSE","Utilities","US"),
    ("D","Dominion Energy Inc","NYSE","Utilities","US"),
    ("AEP","American Electric Power","NASDAQ","Utilities","US"),
    ("EXC","Exelon Corporation","NASDAQ","Utilities","US"),
    ("XEL","Xcel Energy Inc","NASDAQ","Utilities","US"),
    ("ETR","Entergy Corporation","NYSE","Utilities","US"),
    ("EIX","Edison International","NYSE","Utilities","US"),
    ("AWK","American Water Works","NYSE","Utilities","US"),
    ("SRE","Sempra Energy","NYSE","Utilities","US"),
    ("PCG","PG&E Corporation","NYSE","Utilities","US"),
    ("WEC","WEC Energy Group Inc","NYSE","Utilities","US"),
    ("DTE","DTE Energy Company","NYSE","Utilities","US"),
    ("AES","AES Corporation","NYSE","Utilities","US"),
    ("CNP","CenterPoint Energy Inc","NYSE","Utilities","US"),
    ("NRG","NRG Energy Inc","NYSE","Utilities","US"),
    ("CEG","Constellation Energy Corp","NASDAQ","Utilities","US"),
    ("VST","Vistra Corp","NYSE","Utilities","US"),
    ("PPL","PPL Corporation","NYSE","Utilities","US"),
    ("FE","FirstEnergy Corp","NYSE","Utilities","US"),
    ("ES","Eversource Energy","NYSE","Utilities","US"),
    ("CMS","CMS Energy Corporation","NYSE","Utilities","US"),
    ("EVRG","Evergy Inc","NASDAQ","Utilities","US"),
    ("OGE","OGE Energy Corp","NYSE","Utilities","US"),
    ("NI","NiSource Inc","NYSE","Utilities","US"),
    ("UGI","UGI Corporation","NYSE","Utilities","US"),
    # ─── Materials ────────────────────────────────────────────────────
    ("LIN","Linde plc","NASDAQ","Materials","IE"),
    ("APD","Air Products and Chemicals","NASDAQ","Materials","US"),
    ("ECL","Ecolab Inc","NYSE","Materials","US"),
    ("SHW","Sherwin-Williams Company","NYSE","Materials","US"),
    ("PPG","PPG Industries Inc","NYSE","Materials","US"),
    ("NEM","Newmont Corporation","NYSE","Materials","US"),
    ("FCX","Freeport-McMoRan Inc","NYSE","Materials","US"),
    ("GOLD","Barrick Gold Corporation","NYSE","Materials","CA"),
    ("AEM","Agnico Eagle Mines Ltd","NYSE","Materials","CA"),
    ("WPM","Wheaton Precious Metals","NYSE","Materials","CA"),
    ("NUE","Nucor Corporation","NYSE","Materials","US"),
    ("STLD","Steel Dynamics Inc","NASDAQ","Materials","US"),
    ("X","United States Steel Corp","NYSE","Materials","US"),
    ("CLF","Cleveland-Cliffs Inc","NYSE","Materials","US"),
    ("ALB","Albemarle Corporation","NYSE","Materials","US"),
    ("LIVENT","Livent Corp","NYSE","Materials","US"),
    ("CF","CF Industries Holdings","NYSE","Materials","US"),
    ("MOS","Mosaic Company","NYSE","Materials","US"),
    ("NTR","Nutrien Ltd","NYSE","Materials","CA"),
    ("LYB","LyondellBasell Industries","NYSE","Materials","NL"),
    ("DOW","Dow Inc","NYSE","Materials","US"),
    ("DD","DuPont de Nemours Inc","NYSE","Materials","US"),
    ("VMC","Vulcan Materials Company","NYSE","Materials","US"),
    ("MLM","Martin Marietta Materials","NYSE","Materials","US"),
    ("IFF","International Flavors & Fragrances","NYSE","Materials","US"),
    ("RPM","RPM International Inc","NYSE","Materials","US"),
    ("EMN","Eastman Chemical Company","NYSE","Materials","US"),
    ("CE","Celanese Corporation","NYSE","Materials","US"),
    ("OLN","Olin Corporation","NYSE","Materials","US"),
    ("CC","Chemours Company","NYSE","Materials","US"),
    ("AA","Alcoa Corporation","NYSE","Materials","US"),
    ("CENX","Century Aluminum Company","NASDAQ","Materials","US"),
    ("CMP","Compass Minerals International","NYSE","Materials","US"),
    # ─── Telecom / Communication ──────────────────────────────────────
    ("T","AT&T Inc","NYSE","Communication","US"),
    ("VZ","Verizon Communications","NYSE","Communication","US"),
    ("TMUS","T-Mobile US Inc","NASDAQ","Communication","US"),
    ("CMCSA","Comcast Corporation","NASDAQ","Communication","US"),
    ("CHTR","Charter Communications Inc","NASDAQ","Communication","US"),
    ("WBD","Warner Bros Discovery Inc","NASDAQ","Communication","US"),
    ("PARA","Paramount Global","NASDAQ","Communication","US"),
    ("FOX","Fox Corporation","NASDAQ","Communication","US"),
    ("NYT","New York Times Company","NYSE","Communication","US"),
    ("SIRI","Sirius XM Holdings","NASDAQ","Communication","US"),
    ("LUMN","Lumen Technologies Inc","NYSE","Communication","US"),
    # ─── Real Estate ──────────────────────────────────────────────────
    ("O","Realty Income Corporation","NYSE","Real Estate","US"),
    ("WELL","Welltower Inc","NYSE","Real Estate","US"),
    ("VICI","VICI Properties Inc","NYSE","Real Estate","US"),
    ("EQR","Equity Residential","NYSE","Real Estate","US"),
    ("PSA","Public Storage","NYSE","Real Estate","US"),
    ("DLR","Digital Realty Trust","NYSE","Real Estate","US"),
    ("EQIX","Equinix Inc","NASDAQ","Real Estate","US"),
    ("CCI","Crown Castle Inc","NYSE","Real Estate","US"),
    ("SPG","Simon Property Group Inc","NYSE","Real Estate","US"),
    ("EXR","Extra Space Storage Inc","NYSE","Real Estate","US"),
    ("AVB","AvalonBay Communities Inc","NYSE","Real Estate","US"),
    ("BXP","BXP Inc","NYSE","Real Estate","US"),
    ("ARE","Alexandria Real Estate Equities","NYSE","Real Estate","US"),
    ("VTR","Ventas Inc","NYSE","Real Estate","US"),
    ("PEAK","Healthpeak Properties Inc","NYSE","Real Estate","US"),
    ("HST","Host Hotels and Resorts","NASDAQ","Real Estate","US"),
    ("WPC","W.P. Carey Inc","NYSE","Real Estate","US"),
    ("STAG","Stag Industrial Inc","NYSE","Real Estate","US"),
    ("REXR","Rexford Industrial Realty","NYSE","Real Estate","US"),
    ("NNN","NNN REIT Inc","NYSE","Real Estate","US"),
    ("ADC","Agree Realty Corporation","NYSE","Real Estate","US"),
    ("LTC","LTC Properties Inc","NYSE","Real Estate","US"),
    ("OHI","Omega Healthcare Investors","NYSE","Real Estate","US"),
    ("CUBE","CubeSmart","NYSE","Real Estate","US"),
    ("LSI","Life Storage Inc","NYSE","Real Estate","US"),
    ("NSA","National Storage Affiliates","NYSE","Real Estate","US"),
    ("ESS","Essex Property Trust","NYSE","Real Estate","US"),
    ("UDR","UDR Inc","NYSE","Real Estate","US"),
    ("MAA","Mid-America Apartment Communities","NYSE","Real Estate","US"),
    ("CPT","Camden Property Trust","NYSE","Real Estate","US"),
    # ─── More Technology ──────────────────────────────────────────────
    ("PAYX","Paychex Inc","NASDAQ","Technology","US"),
    ("ADP","Automatic Data Processing","NASDAQ","Technology","US"),
    ("CTSH","Cognizant Technology Solutions","NASDAQ","Technology","US"),
    ("EPAM","EPAM Systems Inc","NYSE","Technology","US"),
    ("G","Genpact Limited","NYSE","Technology","IN"),
    ("WEX","WEX Inc","NYSE","Technology","US"),
    ("JKHY","Jack Henry & Associates","NASDAQ","Technology","US"),
    ("FISV","Fiserv Inc","NASDAQ","Technology","US"),
    ("FIS","Fidelity National Info Services","NYSE","Technology","US"),
    ("GPN","Global Payments Inc","NYSE","Technology","US"),
    ("NTAP","NetApp Inc","NASDAQ","Technology","US"),
    ("HPE","Hewlett Packard Enterprise","NYSE","Technology","US"),
    ("JNPR","Juniper Networks Inc","NYSE","Technology","US"),
    ("FFIV","F5 Inc","NASDAQ","Technology","US"),
    ("VRNS","Varonis Systems Inc","NASDAQ","Technology","US"),
    ("S","SentinelOne Inc","NYSE","Technology","US"),
    ("TENB","Tenable Holdings Inc","NASDAQ","Technology","US"),
    ("QLYS","Qualys Inc","NASDAQ","Technology","US"),
    ("RPD","Rapid7 Inc","NASDAQ","Technology","US"),
    ("INFA","Informatica Inc","NYSE","Technology","US"),
    ("CIEN","Ciena Corporation","NYSE","Technology","US"),
    ("TRMB","Trimble Inc","NASDAQ","Technology","US"),
    ("MKSI","MKS Instruments Inc","NASDAQ","Technology","US"),
    ("ONTO","Onto Innovation Inc","NYSE","Technology","US"),
    ("AMBA","Ambarella Inc","NASDAQ","Technology","US"),
    ("SLAB","Silicon Laboratories Inc","NASDAQ","Technology","US"),
    ("ENTG","Entegris Inc","NASDAQ","Technology","US"),
    ("CRUS","Cirrus Logic Inc","NASDAQ","Technology","US"),
    ("CLS","Celestica Inc","NYSE","Technology","CA"),
    ("FLEX","Flex Ltd","NASDAQ","Technology","SG"),
    ("JBL","Jabil Inc","NYSE","Technology","US"),
    ("SANM","Sanmina Corporation","NASDAQ","Technology","US"),
    ("FORM","FormFactor Inc","NASDAQ","Technology","US"),
    ("MTSI","MACOM Technology Solutions","NASDAQ","Technology","US"),
    ("ICHR","Ichor Holdings Ltd","NASDAQ","Technology","US"),
    ("GDDY","GoDaddy Inc","NYSE","Technology","US"),
    ("ZD","Ziff Davis Inc","NASDAQ","Technology","US"),
    ("IAC","IAC Inc","NASDAQ","Technology","US"),
    ("CARS","Cars.com Inc","NYSE","Technology","US"),
    ("ANGI","Angi Inc","NASDAQ","Technology","US"),
    ("TRIP","TripAdvisor Inc","NASDAQ","Technology","US"),
    ("BKNG","Booking Holdings Inc","NASDAQ","Consumer Cyclical","US"),
    ("EXPE","Expedia Group Inc","NASDAQ","Consumer Cyclical","US"),
    # ─── International ADRs ───────────────────────────────────────────
    ("SONY","Sony Group Corporation","NYSE","Technology","JP"),
    ("NVS","Novartis AG","NYSE","Healthcare","CH"),
    ("AZN","AstraZeneca plc","NASDAQ","Healthcare","GB"),
    ("GSK","GSK plc","NYSE","Healthcare","GB"),
    ("SNY","Sanofi S.A.","NASDAQ","Healthcare","FR"),
    ("BP","BP p.l.c.","NYSE","Energy","GB"),
    ("SHEL","Shell plc","NYSE","Energy","GB"),
    ("TTE","TotalEnergies SE","NYSE","Energy","FR"),
    ("ENI","ENI S.p.A.","NYSE","Energy","IT"),
    ("RIO","Rio Tinto plc","NYSE","Materials","GB"),
    ("BHP","BHP Group Limited","NYSE","Materials","AU"),
    ("VALE","Vale S.A.","NYSE","Materials","BR"),
    ("ITUB","Itau Unibanco Holding S.A.","NYSE","Financial","BR"),
    ("BBD","Banco Bradesco S.A.","NYSE","Financial","BR"),
    ("BBAS3","Banco do Brasil","OTC","Financial","BR"),
    ("AMX","America Movil S.A.B.","NYSE","Communication","MX"),
    ("ORAN","Orange S.A.","NYSE","Communication","FR"),
    ("UBS","UBS Group AG","NYSE","Financial","CH"),
    ("DB","Deutsche Bank AG","NYSE","Financial","DE"),
    ("BCS","Barclays plc","NYSE","Financial","GB"),
    ("LLOY","Lloyds Banking Group plc","NYSE","Financial","GB"),
    ("HSBC","HSBC Holdings plc","NYSE","Financial","GB"),
    ("SMFG","Sumitomo Mitsui Financial","NYSE","Financial","JP"),
    ("MFG","Mizuho Financial Group","NYSE","Financial","JP"),
    ("MTU","Mitsubishi UFJ Financial","NYSE","Financial","JP"),
    ("INFY","Infosys Limited","NYSE","Technology","IN"),
    ("WIT","Wipro Limited","NYSE","Technology","IN"),
    ("HDB","HDFC Bank Limited","NYSE","Financial","IN"),
    ("IBN","ICICI Bank Limited","NYSE","Financial","IN"),
    ("BNTX","BioNTech SE","NASDAQ","Healthcare","DE"),
    ("BAYRY","Bayer AG ADR","OTC","Healthcare","DE"),
    ("NOVO-B.CO","Novo Nordisk Copenhagen","CPH","Healthcare","DK"),
    ("RHHBY","Roche Holding AG ADR","OTC","Healthcare","CH"),
    ("SIEGY","Siemens AG ADR","OTC","Industrials","DE"),
    ("ABB","ABB Ltd","NYSE","Industrials","CH"),
    ("ALIZY","Allianz SE ADR","OTC","Financial","DE"),
    ("ING","ING Group N.V.","NYSE","Financial","NL"),
    ("PHG","Philips N.V.","NYSE","Healthcare","NL"),
    ("STM","STMicroelectronics","NYSE","Technology","CH"),
    ("ERIC","Ericsson AB ADR","NASDAQ","Technology","SE"),
    ("NOK","Nokia Corporation","NYSE","Technology","FI"),
    ("LOGI","Logitech International","NASDAQ","Technology","CH"),
    ("CNQ","Canadian Natural Resources","NYSE","Energy","CA"),
    ("SU","Suncor Energy Inc","NYSE","Energy","CA"),
    ("CVE","Cenovus Energy Inc","NYSE","Energy","CA"),
    ("IMO","Imperial Oil Limited","NYSE","Energy","CA"),
    ("ENB","Enbridge Inc","NYSE","Energy","CA"),
    ("TRP","TC Energy Corporation","NYSE","Energy","CA"),
    ("BCE","BCE Inc","NYSE","Communication","CA"),
    ("T.TO","Telus Corporation","TSX","Communication","CA"),
    ("RY","Royal Bank of Canada","NYSE","Financial","CA"),
    ("TD","Toronto-Dominion Bank","NYSE","Financial","CA"),
    ("BNS","Bank of Nova Scotia","NYSE","Financial","CA"),
    ("BMO","Bank of Montreal","NYSE","Financial","CA"),
    ("CM","CIBC","NYSE","Financial","CA"),
    ("MFC","Manulife Financial","NYSE","Financial","CA"),
    ("SLF","Sun Life Financial","NYSE","Financial","CA"),
    # ─── Additional Crypto ────────────────────────────────────────────
    ("LTC-USD","Litecoin","Crypto","Cryptocurrency","Global"),
    ("DOT-USD","Polkadot","Crypto","Cryptocurrency","Global"),
    ("LINK-USD","Chainlink","Crypto","Cryptocurrency","Global"),
    ("MATIC-USD","Polygon (MATIC)","Crypto","Cryptocurrency","Global"),
    ("UNI-USD","Uniswap","Crypto","Cryptocurrency","Global"),
    ("ATOM-USD","Cosmos","Crypto","Cryptocurrency","Global"),
    ("NEAR-USD","NEAR Protocol","Crypto","Cryptocurrency","Global"),
    ("APT-USD","Aptos","Crypto","Cryptocurrency","Global"),
    ("ARB-USD","Arbitrum","Crypto","Cryptocurrency","Global"),
    ("OP-USD","Optimism","Crypto","Cryptocurrency","Global"),
    ("SUI-USD","Sui","Crypto","Cryptocurrency","Global"),
    ("INJ-USD","Injective","Crypto","Cryptocurrency","Global"),
    ("TIA-USD","Celestia","Crypto","Cryptocurrency","Global"),
    ("FET-USD","Fetch.ai","Crypto","Cryptocurrency","Global"),
    ("RNDR-USD","Render Token","Crypto","Cryptocurrency","Global"),
    ("TAO-USD","Bittensor","Crypto","Cryptocurrency","Global"),
    ("WLD-USD","Worldcoin","Crypto","Cryptocurrency","Global"),
    # ─── Additional Commodities ───────────────────────────────────────
    ("ZC=F","Corn Futures","CBOT","Commodities","Global"),
    ("ZW=F","Wheat Futures","CBOT","Commodities","Global"),
    ("ZS=F","Soybean Futures","CBOT","Commodities","Global"),
    ("KC=F","Coffee Futures","NYBOT","Commodities","Global"),
    ("SB=F","Sugar #11 Futures","NYBOT","Commodities","Global"),
    ("CT=F","Cotton #2 Futures","NYBOT","Commodities","Global"),
    ("PL=F","Platinum Futures","NYMEX","Commodities","Global"),
    ("PA=F","Palladium Futures","NYMEX","Commodities","Global"),
    ("LBS=F","Lumber Futures","CME","Commodities","Global"),
    ("LE=F","Live Cattle Futures","CME","Commodities","Global"),
    # ─── TASE (TA-125 Extended) ───────────────────────────────────────
    ("GZIT.TA","Gazit Globe Ltd","TASE","Real Estate","IL"),
    ("ENRG.TA","Energix Renewable Energies","TASE","Utilities","IL"),
    ("MTRX.TA","Matrix IT Ltd","TASE","Technology","IL"),
    ("HOT.TA","HOT Telecommunications","TASE","Communication","IL"),
    ("TDGR.TA","Tadiran Group Ltd","TASE","Industrials","IL"),
    ("IGUD.TA","Bank Igud Israel","TASE","Financial","IL"),
    ("INVR.TA","Investec Bank Israel","TASE","Financial","IL"),
    ("RBLI.TA","Rami Levy Chain Stores","TASE","Consumer Defensive","IL"),
    ("SANO.TA","Sano Bruno Enterprises","TASE","Consumer Defensive","IL"),
    ("PRGO.TA","Perrigo Company plc","TASE","Healthcare","IL"),
    ("ARAD.TA","Arad Investment","TASE","Industrials","IL"),
    ("SHLD.TA","Shlomo Holdings","TASE","Consumer Cyclical","IL"),
    ("MNUL.TA","Menora Mivtachim Insurance","TASE","Financial","IL"),
    ("MGOR.TA","Mega Or Holdings","TASE","Consumer Defensive","IL"),
    ("ISCO.TA","Israel Corp Ltd","TASE","Industrials","IL"),
    ("XLBV.TA","XTL Biopharmaceuticals","TASE","Healthcare","IL"),
    ("OPKO.TA","OPKO Health Israel","TASE","Healthcare","IL"),
    ("ESCOM.TA","Comverse Technology Israel","TASE","Technology","IL"),
    ("LBDB.TA","Leumi Mortgage Bank","TASE","Financial","IL"),
    ("MXLX.TA","Maxler Ltd","TASE","Consumer Cyclical","IL"),
    ("PLRM.TA","Pilgrim Medical","TASE","Healthcare","IL"),
    ("ISCR.TA","Israel Credit Cards","TASE","Financial","IL"),
    ("HWAY.TA","Highway 90 Ltd","TASE","Industrials","IL"),
    ("AMRK.TA","A.Dankner Real Estate","TASE","Real Estate","IL"),
    ("BRAN.TA","Brack Capital Real Estate","TASE","Real Estate","IL"),
    ("KNFM.TA","Kanaf-Nesher Investments","TASE","Financial","IL"),
    ("GILI.TA","Gili Sports","TASE","Consumer Cyclical","IL"),
]
# Build search index: lowercase name + symbol → catalog entry
_CATALOG_IDX = []
_CATALOG_NAME_MAP = {}   # symbol → (name, exchange, sector, country)
for _c in CATALOG:
    _CATALOG_IDX.append({
        "symbol": _c[0], "name": _c[1], "exchange": _c[2],
        "sector": _c[3], "country": _c[4]
    })
    _CATALOG_NAME_MAP[_c[0]] = (_c[1], _c[2], _c[3], _c[4])

def calc_rsi(closes, period=14):
    """Relative Strength Index."""
    try:
        import pandas as pd
        delta = closes.diff()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain.iloc[-1] / loss.iloc[-1]
        return round(float(100 - 100 / (1 + rs)), 1) if loss.iloc[-1] != 0 else 100.0
    except:
        return None

def calc_macd(closes):
    """MACD, Signal, Histogram."""
    try:
        ema12  = closes.ewm(span=12, adjust=False).mean()
        ema26  = closes.ewm(span=26, adjust=False).mean()
        macd   = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist   = macd - signal
        return {
            "macd":   round(float(macd.iloc[-1]),   3),
            "signal": round(float(signal.iloc[-1]), 3),
            "hist":   round(float(hist.iloc[-1]),   3),
            "trend":  "bullish" if hist.iloc[-1] > 0 else "bearish",
        }
    except:
        return None

def load_stock(sym):
    """Fetch 1yr history via yfinance, compute MAs and fundamentals."""
    global loading_set
    with data_lock:
        if sym in loading_set:
            return
        loading_set.add(sym)
    _t0 = time.time()
    # Create a custom APM span for the yfinance data fetch
    _span_ctx = tracer.start_span("stock.load", service="stocklens-backend", resource=sym) if _DD_AVAILABLE else None
    if _span_ctx:
        _span_ctx.set_tag("stock.symbol", sym)
        _span_ctx.set_tag("stock.is_tase", sym.endswith(".TA"))
        _span_ctx.set_tag("stock.exchange", "TASE" if sym.endswith(".TA") else "US")
    try:
        import yfinance as yf
        import pandas as pd
        logger.info("Loading stock data", extra={"stock.symbol": sym, "event": "stock_load_start"})
        t    = yf.Ticker(sym)
        hist = t.history(period="1y", auto_adjust=True)
        if hist.empty or len(hist) < 5:
            logger.warning("No history for symbol", extra={"stock.symbol": sym, "event": "stock_no_history"})
            if _span_ctx:
                _span_ctx.set_tag("stock.result", "no_history")
                _span_ctx.error = 1
            return
        closes = hist["Close"]
        cur    = float(closes.iloc[-1])
        prev   = float(closes.iloc[-2]) if len(closes) > 1 else cur
        chg    = cur - prev
        pct    = (chg / prev * 100) if prev else 0.0
        def ma(w):
            v = closes.rolling(w).mean().iloc[-1]
            return round(float(v), 2) if not pd.isna(v) and len(closes) >= w else None
        ma50  = ma(50)
        ma100 = ma(100)
        ma150 = ma(150)
        ma200 = ma(200)
        rsi  = calc_rsi(closes)
        macd = calc_macd(closes)
        N = min(120, len(hist))
        def rolling_series(w):
            r = closes.rolling(w).mean().iloc[-N:]
            return [None if pd.isna(v) else round(float(v), 2) for v in r]
        chart = {
            "dates":  [d.strftime("%Y-%m-%d") for d in hist.index[-N:]],
            "closes": [round(float(v), 2) for v in closes.iloc[-N:]],
            "ma50":   rolling_series(50),
            "ma100":  rolling_series(100),
            "ma150":  rolling_series(150),
            "ma200":  rolling_series(200),
        }
        # Fundamentals
        try:
            info = t.info
        except Exception:
            info = {}
        def fmt_cap(v):
            if not v: return None
            if v >= 1e12: return f"${v/1e12:.2f}T"
            if v >= 1e9:  return f"${v/1e9:.2f}B"
            if v >= 1e6:  return f"${v/1e6:.2f}M"
            return f"${v:,.0f}"
        # Use catalog name as fallback if yfinance doesn't return longName
        _cat = _CATALOG_NAME_MAP.get(sym, (None, None, None, None))
        _cat_name = _cat[0]
        fund = {
            "name":          info.get("longName") or info.get("shortName") or _cat_name or sym,
            "sector":        info.get("sector", "—"),
            "industry":      info.get("industry", "—"),
            "market_cap":    fmt_cap(info.get("marketCap")),
            "market_cap_raw":info.get("marketCap"),
            "trailing_pe":   round(float(info["trailingPE"]), 2) if info.get("trailingPE") else None,
            "forward_pe":    round(float(info["forwardPE"]), 2) if info.get("forwardPE") else None,
            "eps":           info.get("trailingEps"),
            "div_yield":     round(float(info["dividendYield"]), 4) if info.get("dividendYield") else None,
            "high_52w":      info.get("fiftyTwoWeekHigh"),
            "low_52w":       info.get("fiftyTwoWeekLow"),
            "avg_vol":       info.get("averageVolume"),
            "beta":          round(float(info["beta"]), 2) if info.get("beta") else None,
            "pb":            round(float(info["priceToBook"]), 2) if info.get("priceToBook") else None,
            "profit_margin": round(float(info["profitMargins"]) * 100, 1) if info.get("profitMargins") else None,
            "revenue_growth":round(float(info["revenueGrowth"]) * 100, 1) if info.get("revenueGrowth") else None,
            "description":   (info.get("longBusinessSummary") or "")[:300],
            "currency":      info.get("currency", "USD"),
            "rec":           info.get("recommendationKey"),
            "target_mean":   info.get("targetMeanPrice"),
            "target_high":   info.get("targetHighPrice"),
            "target_low":    info.get("targetLowPrice"),
            "num_analysts":  info.get("numberOfAnalystOpinions"),
            "strong_buy":    info.get("recommendationMean"),
        }
        raw_ccy = info.get("currency", "USD")
        # yfinance quotes some TASE stocks in ILA (Israeli Agoroth = 1/100 ILS)
        # Convert to ILS for human-readable display
        if raw_ccy == "ILA":
            factor = 0.01
            display_ccy = "ILS"
        else:
            factor = 1.0
            display_ccy = raw_ccy
        def rescale(v): return round(v * factor, 2) if v else v
        entry = {
            "price":    rescale(cur), "change": rescale(chg), "pct": round(pct, 2),
            "ma50":     rescale(ma50), "ma100": rescale(ma100), "ma150": rescale(ma150), "ma200": rescale(ma200),
            "volume":   int(hist["Volume"].iloc[-1]),
            "name":     fund["name"], "sector": fund["sector"],
            "currency": display_ccy,
            "rsi":      rsi, "macd_data": macd,
            "chart":    chart, "_ts": time.time(),
            "_factor":             factor,
            "_prev_close_display": rescale(prev),
        }
        with data_lock:
            price_cache[sym] = entry
            fund_cache[sym]  = fund
        elapsed = round(time.time() - _t0, 3)
        logger.info("Stock loaded successfully",
                    extra={"stock.symbol": sym, "stock.price": round(cur, 2),
                           "stock.currency": display_ccy, "load_time_s": elapsed,
                           "event": "stock_load_success"})
        if _span_ctx:
            _span_ctx.set_tag("stock.price", round(cur, 2))
            _span_ctx.set_tag("stock.currency", display_ccy)
            _span_ctx.set_tag("stock.result", "success")
            _span_ctx.set_metric("stock.load_time_s", elapsed)
    except Exception as e:
        elapsed = round(time.time() - _t0, 3)
        logger.error("Failed to load stock", exc_info=True,
                     extra={"stock.symbol": sym, "error": str(e), "load_time_s": elapsed,
                            "event": "stock_load_error"})
        if _span_ctx:
            _span_ctx.set_tag("stock.result", "error")
            _span_ctx.set_tag("error.message", str(e))
            _span_ctx.error = 1
    finally:
        if _span_ctx:
            _span_ctx.finish()
        with data_lock:
            loading_set.discard(sym)

def refresh_loop():
    while True:
        with stocks_lock:
            syms = list(stocks)
        for sym in syms:
            with data_lock:
                age = time.time() - price_cache.get(sym, {}).get("_ts", 0)
            if age > 300:      # refresh every 5 minutes
                threading.Thread(target=load_stock, args=(sym,), daemon=True).start()
        time.sleep(60)

def initial_load():
    with stocks_lock:
        syms = list(stocks)
    threads = [threading.Thread(target=load_stock, args=(s,), daemon=True) for s in syms]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"All {len(syms)} stocks loaded.", flush=True)

threading.Thread(target=initial_load, daemon=True).start()
threading.Thread(target=refresh_loop, daemon=True).start()

def price_refresh_loop():
    """Fetch current prices from Nasdaq/TASE via Yahoo Finance every 15 seconds.
    Uses fast_info per ticker to avoid batch alignment issues with mixed US/TASE symbols."""
    import yfinance as yf
    while True:
        time.sleep(15)
        try:
            with stocks_lock:
                syms = list(stocks)
            with data_lock:
                loaded = [s for s in syms if s in price_cache]
            if not loaded:
                continue
            updated = 0
            for sym in loaded:
                try:
                    fi = yf.Ticker(sym).fast_info
                    cur_raw = fi.last_price
                    if not cur_raw or cur_raw <= 0:
                        continue
                    prev_raw = fi.previous_close or cur_raw
                    with data_lock:
                        cached = price_cache.get(sym, {})
                        factor = cached.get("_factor", 1.0)
                    cur_disp  = round(cur_raw  * factor, 2)
                    prev_disp = round(prev_raw * factor, 2)
                    chg = round(cur_disp - prev_disp, 2)
                    pct = round((chg / prev_disp * 100) if prev_disp else 0.0, 2)
                    with data_lock:
                        if sym in price_cache:
                            price_cache[sym]["price"]              = cur_disp
                            price_cache[sym]["change"]             = chg
                            price_cache[sym]["pct"]                = pct
                            price_cache[sym]["_prev_close_display"]= prev_disp
                            price_cache[sym]["_price_ts"]          = time.time()
                    updated += 1
                except Exception:
                    pass
            # Publish to Kafka
            try:
                from kafka import KafkaProducer
                if not hasattr(price_refresh_loop, '_producer'):
                    price_refresh_loop._producer = KafkaProducer(
                        bootstrap_servers='kafka.kafka.svc.cluster.local:9092',
                        value_serializer=lambda v: json.dumps(v).encode()
                    )
                batch = {}
                with data_lock:
                    for s in loaded:
                        d = price_cache.get(s)
                        if d:
                            batch[s] = {'price': d['price'], 'pct': d['pct'], 'change': d['change']}
                if batch:
                    price_refresh_loop._producer.send('stock-prices', batch)
                    price_refresh_loop._producer.flush()
                    print(f"[kafka] published {len(batch)} symbols to stock-prices", flush=True)
            except Exception as ke:
                print(f"[kafka] publish error: {ke}", flush=True)
            print(f"[price_refresh] updated {updated}/{len(loaded)} symbols", flush=True)
        except Exception as e:
            print(f"price_refresh_loop error: {e}", flush=True)

threading.Thread(target=price_refresh_loop, daemon=True).start()

def fetch_recommendations():
    """Fetch StockTwits trending + combine with yfinance analyst data."""
    global rec_cache
    time.sleep(90)   # wait for initial_load to complete first
    ctx = ssl.create_default_context()
    catalog_syms = {c[0] for c in CATALOG}
    while True:
        try:
            # ── 1. StockTwits trending symbols (1 HTTP call) ──────
            trending_pairs = []
            try:
                req = _ureq.Request(
                    "https://api.stocktwits.com/api/2/trending/symbols.json",
                    headers={"User-Agent": "Mozilla/5.0 (compatible; StockApp/1.0)"})
                with _ureq.urlopen(req, context=ctx, timeout=8) as h:
                    data = json.loads(h.read())
                trending_pairs = [(s["symbol"], s.get("watchlist_count", 0))
                                  for s in data.get("symbols", [])[:30]]
                print(f"StockTwits: {[s[0] for s in trending_pairs[:8]]}", flush=True)
            except Exception as e:
                print(f"StockTwits unavailable: {e}", flush=True)

            # ── 2. Merge trending + analyst-rated from fund_cache ──
            seen, ranked = set(), []
            # Trending first (social signal)
            for sym, wl in trending_pairs:
                if sym in catalog_syms and sym not in seen:
                    ranked.append((sym, wl, True))
                    seen.add(sym)
            # Analyst picks from already-loaded data (fallback + supplement)
            with data_lock:
                fund_snap  = dict(fund_cache)
                price_snap = dict(price_cache)
            for sym, fd in fund_snap.items():
                if sym in seen: continue
                if (fd.get("rec") or "") in ("strong_buy", "buy"):
                    ranked.append((sym, 0, False))
                    seen.add(sym)

            # ── 3. Trigger load for top unloaded catalog symbols ───
            needs_load = [s for s, _, _ in ranked[:15] if s not in price_snap and s in catalog_syms]
            threads = [threading.Thread(target=load_stock, args=(s,), daemon=True) for s in needs_load]
            for t in threads: t.start()
            if threads:
                for t in threads: t.join(timeout=30)   # wait up to 30s for data

            # ── 4. Build result list ───────────────────────────────
            results = []
            for rank_i, (sym, wl_cnt, is_social) in enumerate(ranked):
                with data_lock:
                    pd = price_cache.get(sym)
                    fd = fund_cache.get(sym)
                if not pd or not fd: continue
                rec    = (fd.get("rec") or "hold").lower()
                target = fd.get("target_mean")
                price  = pd.get("price", 0)
                upside = round((target - price) / price * 100, 1) if (target and price > 0) else None
                results.append({
                    "symbol":      sym,
                    "name":        fd.get("name", sym),
                    "price":       price,
                    "change":      pd.get("change", 0),
                    "pct":         pd.get("pct", 0),
                    "currency":    pd.get("currency", "USD"),
                    "rec":         rec,
                    "rec_mean":    fd.get("strong_buy"),
                    "target":      target,
                    "upside":      upside,
                    "analysts":    fd.get("num_analysts") or 0,
                    "sector":      fd.get("sector", ""),
                    "social_rank": rank_i + 1 if is_social else None,
                    "wl_count":    wl_cnt,
                })

            # ── 5. Sort: strong_buy first, then by upside% ─────────
            results.sort(key=lambda x: (
                REC_ORDER.get(x["rec"], 3),
                -(x.get("upside") or -999)
            ))
            with rec_lock:
                rec_cache = results[:10]
            print(f"Recs updated: {[r['symbol']+'/'+r['rec'] for r in rec_cache[:5]]}", flush=True)
        except Exception as e:
            print(f"fetch_recommendations error: {e}", flush=True)
        time.sleep(900)  # refresh every 15 minutes

threading.Thread(target=fetch_recommendations, daemon=True).start()

@app.route("/health")
def health():
    return "ok"

@app.route("/api/stocks")
def get_stocks():
    global request_count
    with state_lock:
        request_count += 1
        rc = request_count
    with data_lock:
        result = []
        for sym in stocks:
            d = price_cache.get(sym)
            # Map internal symbols to frontend-friendly names
            display_sym = sym.lstrip('^')  # ^VIX → VIX
            if d:
                result.append({
                    "symbol": display_sym, "name": d.get("name", display_sym),
                    "price": d["price"], "change": d["change"], "pct": d["pct"],
                    "ma50": d.get("ma50"), "ma100": d.get("ma100"), "ma150": d.get("ma150"), "ma200": d.get("ma200"),
                    "volume": d.get("volume", 0), "sector": d.get("sector", ""),
                    "currency": d.get("currency", "USD"),
                    "rsi": d.get("rsi"), "macd_data": d.get("macd_data"),
                    "age_s": int(time.time() - d.get("_ts", 0)),
                })
            else:
                result.append({"symbol": sym, "loading": True})
    return jsonify({
        "stocks": result, "request_count": rc,
        "uptime_s": round(time.time() - start_time, 1),
        "pod_ip": os.environ.get("POD_IP", ""),
        "node": os.environ.get("NODE_NAME", ""),
        "hostname": os.environ.get("HOSTNAME", ""),
        "pid": os.getpid(),
    })

@app.route("/api/stock/<symbol>")
def get_stock_detail(symbol):
    symbol = symbol.upper()
    with data_lock:
        d = price_cache.get(symbol)
        f = fund_cache.get(symbol, {})
    if not d:
        # On-demand load for any symbol (e.g. NBIS found via Yahoo Finance search)
        logger.info("On-demand stock load triggered", extra={"stock.symbol": symbol, "event": "ondemand_load"})
        ev = threading.Event()
        def _load():
            load_stock(symbol)
            ev.set()
        threading.Thread(target=_load, daemon=True).start()
        ev.wait(timeout=25)
        with data_lock:
            d = price_cache.get(symbol)
            f = fund_cache.get(symbol, {})
        if not d:
            logger.warning("Stock not found after on-demand load", extra={"stock.symbol": symbol, "event": "stock_not_found"})
            return jsonify({"error": "not found or no data available for " + symbol}), 404
    logger.info("Stock detail served", extra={"stock.symbol": symbol, "stock.price": d.get("price"), "event": "stock_detail_served"})
    return jsonify({"symbol": symbol, **d, "fundamentals": f})

@app.route("/api/recommendations")
def get_recommendations():
    with rec_lock:
        recs = list(rec_cache)
    return jsonify({"recommendations": recs, "ts": int(time.time())})

# Social feed cache (StockTwits per-symbol)
social_cache = {}
social_lock  = threading.Lock()

@app.route("/api/social/<symbol>")
def get_social(symbol):
    symbol = symbol.upper()
    # Check 5-min cache
    with social_lock:
        cached = social_cache.get(symbol)
        if cached and time.time() - cached['ts'] < 300:
            return jsonify(cached['data'])
    # Map symbol to StockTwits format
    st_sym = symbol
    if '.TA' in st_sym:
        st_sym = st_sym.replace('.TA', '')
    elif '-USD' in st_sym:
        st_sym = st_sym.replace('-USD', '')
    st_map = {'GC=F':'GOLD','SI=F':'SILVER','CL=F':'OIL','NG=F':'GAS',
              'HG=F':'COPPER','ILS=X':'USDILS','EURUSD=X':'EURUSD',
              'GBPUSD=X':'GBPUSD','JPY=X':'USDJPY'}
    st_sym = st_map.get(symbol, st_sym)
    ctx = ssl.create_default_context()
    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{st_sym}.json?limit=10"
        req = _ureq.Request(url, headers={"User-Agent":"Mozilla/5.0 (compatible; TraderPro/1.0)"})
        with _ureq.urlopen(req, context=ctx, timeout=8) as h:
            data = json.loads(h.read())
        messages = []
        for msg in data.get('messages', [])[:8]:
            sent_obj  = (msg.get('entities') or {}).get('sentiment') or {}
            sentiment = sent_obj.get('basic', '')
            likes     = (msg.get('likes') or {}).get('total', 0)
            messages.append({
                'id':        msg.get('id'),
                'text':      (msg.get('body') or '')[:280],
                'user':      (msg.get('user') or {}).get('username', 'trader'),
                'sentiment': sentiment,
                'likes':     likes,
                'time':      msg.get('created_at', ''),
            })
        bullish = sum(1 for m in messages if m['sentiment'] == 'Bullish')
        bearish = sum(1 for m in messages if m['sentiment'] == 'Bearish')
        result  = {'symbol': symbol, 'st_sym': st_sym, 'messages': messages,
                   'bullish': bullish, 'bearish': bearish, 'ts': int(time.time())}
        with social_lock:
            social_cache[symbol] = {'data': result, 'ts': time.time()}
        return jsonify(result)
    except Exception as e:
        return jsonify({'symbol': symbol, 'messages': [], 'error': str(e), 'ts': int(time.time())})

@app.route("/api/catalog")
def get_catalog():
    with stocks_lock:
        wl = set(stocks)
    return jsonify({"catalog": [
        {**item, "in_watchlist": item["symbol"] in wl}
        for item in _CATALOG_IDX
    ]})

@app.route("/api/search")
def search_stocks():
    q = (request.args.get("q") or "").strip()
    if len(q) < 1:
        return jsonify({"results": []})
    qu = q.upper()

    # ── 1. Local catalog search (curated, fast) ──────────────────────────
    results = []
    with stocks_lock:
        wl = set(stocks)
    for item in _CATALOG_IDX:
        sym  = item["symbol"].upper()
        name = item["name"].upper()
        score = 0
        if sym == qu:                                            score = 100
        elif sym.startswith(qu):                                 score = 85
        elif qu in sym:                                          score = 70
        elif name.startswith(qu):                                score = 65
        elif any(w.startswith(qu) for w in name.split() if w):  score = 60
        elif qu in name:                                         score = 40
        else:
            continue
        results.append({**item, "score": score, "in_watchlist": item["symbol"] in wl})
    results.sort(key=lambda x: -x["score"])
    seen = set()
    deduped = []
    for r in results:
        if r["symbol"] not in seen:
            seen.add(r["symbol"])
            deduped.append(r)

    # ── 2. Yahoo Finance live search — covers ALL exchanges ──────────────
    # Runs for every query; local results appear first (higher scores 40-100)
    # YF results fill in anything not in local catalog (NBIS, TASE, etc.)
    try:
        yf_url = ("https://query2.finance.yahoo.com/v1/finance/search"
                  "?q=" + _ureq.quote(q) +
                  "&quotesCount=15&newsCount=0&enableFuzzyQuery=false")
        req = _ureq.Request(yf_url, headers={"User-Agent": "Mozilla/5.0"})
        with _ureq.urlopen(req, timeout=3) as resp:
            yf_data = json.loads(resp.read())

        _EXCH_MAP = {
            "NASDAQ": "NASDAQ", "NasdaqGS": "NASDAQ", "NMS": "NASDAQ",
            "NYSE": "NYSE", "NYSE American": "AMEX", "AMEX": "AMEX",
            "Tel Aviv": "TASE", "TLV": "TASE",
            "London": "LSE", "Frankfurt": "FRA", "Toronto": "TSX",
            "BATS Trading": "BATS", "Chicago": "CBOE",
        }
        for qt in yf_data.get("quotes", []):
            if qt.get("quoteType") not in ("EQUITY", "ETF", "MUTUALFUND"):
                continue
            sym = qt.get("symbol", "")
            if not sym or sym in seen:
                continue
            name = qt.get("shortname") or qt.get("longname") or sym
            exch_raw  = qt.get("exchDisp") or qt.get("exchange", "")
            exchange  = _EXCH_MAP.get(exch_raw, exch_raw or "OTC")
            sector    = qt.get("sectorDisp") or qt.get("sector", "")
            country   = ("IL" if exchange == "TASE"
                         else "US" if exchange in ("NASDAQ","NYSE","AMEX","BATS","CBOE")
                         else "")
            seen.add(sym)
            deduped.append({
                "symbol":      sym,
                "name":        name,
                "exchange":    exchange,
                "sector":      sector,
                "country":     country,
                "score":       max(1, int(qt.get("score", 20000) / 2000)),
                "in_watchlist": sym in wl,
            })
    except Exception:
        pass  # graceful degradation — local results still returned

    deduped.sort(key=lambda x: -x["score"])
    return jsonify({"results": deduped[:15]})

@app.route("/api/stocks/add", methods=["POST"])
def add_stock():
    sym = ((request.json or {}).get("symbol") or "").upper().strip()
    if not sym:
        return jsonify({"error": "symbol required"}), 400
    with stocks_lock:
        if sym in stocks:
            return jsonify({"status": "exists", "symbol": sym})
        stocks.append(sym)
    # Load synchronously in a short-timeout thread and validate
    result = {"ok": False}
    def load_and_check():
        load_stock(sym)
        with data_lock:
            result["ok"] = sym in price_cache
    t = threading.Thread(target=load_and_check, daemon=True)
    t.start()
    t.join(timeout=30)  # wait up to 30s for yfinance
    if not result["ok"]:
        with stocks_lock:
            if sym in stocks: stocks.remove(sym)
        with data_lock:
            price_cache.pop(sym, None); fund_cache.pop(sym, None)
        return jsonify({"status": "error", "symbol": sym, "error": "Symbol not found or no data available"}), 404
    return jsonify({"status": "ok", "symbol": sym})

@app.route("/api/stocks/<symbol>", methods=["DELETE"])
def remove_stock(symbol):
    symbol = symbol.upper()
    with stocks_lock:
        if symbol in stocks:
            stocks.remove(symbol)
    with data_lock:
        price_cache.pop(symbol, None)
        fund_cache.pop(symbol, None)
    return jsonify({"status": "removed", "symbol": symbol})

@app.route("/api/status")
def status():
    with state_lock:
        rc = request_count; tc = trade_count; pnl = pnl_total
    return jsonify({
        "request_count": rc, "trade_count": tc, "pnl_total": round(pnl, 2),
        "uptime_s": round(time.time() - start_time, 1),
        "pod_ip": os.environ.get("POD_IP", ""),
        "node": os.environ.get("NODE_NAME", ""),
        "hostname": os.environ.get("HOSTNAME", ""),
        "pid": os.getpid(),
    })

@app.route("/api/trade", methods=["POST"])
def trade():
    global trade_count, pnl_total
    body  = request.json or {}
    qty   = int(body.get("qty", 10))
    sym   = body.get("symbol", "AAPL").upper()
    with data_lock:
        p = price_cache.get(sym, {}).get("price", 100.0)
    gain = random.uniform(-0.04, 0.06) * p * qty
    with state_lock:
        trade_count += 1
        pnl_total   += gain
        tc = trade_count; pnl = pnl_total
    return jsonify({"trades": tc, "pnl": round(pnl, 2), "gain": round(gain, 2)})

@app.route("/api/financials/<symbol>")
def get_financials(symbol):
    symbol = symbol.upper()
    with data_lock:
        f = dict(fund_cache.get(symbol, {}))
        d = dict(price_cache.get(symbol, {}))
    if not f:
        return jsonify({"error": "not found or loading"}), 404
    # Build quarterly stubs from fundamentals if real quarterly unavailable
    # Try to pull quarterly via yfinance
    try:
        import yfinance as yf, pandas as pd
        t = yf.Ticker(symbol)
        qf = t.quarterly_financials
        qinc = t.quarterly_income_stmt
        src = qf if (qf is not None and not qf.empty) else qinc
        quarters = []
        if src is not None and not src.empty:
            rev_row = None
            for key in ["Total Revenue", "Revenue", "Revenues"]:
                if key in src.index:
                    rev_row = src.loc[key]
                    break
            ni_row = None
            for key in ["Net Income", "Net Income Common Stockholders"]:
                if key in src.index:
                    ni_row = src.loc[key]
                    break
            gp_row = None
            for key in ["Gross Profit"]:
                if key in src.index:
                    gp_row = src.loc[key]
                    break
            cols = sorted(src.columns)[-8:]
            for col in cols:
                rev = float(rev_row[col]) if rev_row is not None and not pd.isna(rev_row[col]) else None
                ni  = float(ni_row[col])  if ni_row  is not None and not pd.isna(ni_row[col])  else None
                gp  = float(gp_row[col])  if gp_row  is not None and not pd.isna(gp_row[col])  else None
                quarters.append({
                    "period": col.strftime("%Y-Q%q") if hasattr(col,'strftime') else str(col)[:7],
                    "revenue_b":  round(rev / 1e9, 2) if rev else None,
                    "net_income_b": round(ni / 1e9, 2) if ni else None,
                    "gross_profit_b": round(gp / 1e9, 2) if gp else None,
                    "gross_margin_pct": round(gp / rev * 100, 1) if gp and rev else None,
                    "net_margin_pct":   round(ni  / rev * 100, 1) if ni  and rev else None,
                    "yoy_revenue_growth_pct": None,
                })
            # compute yoy growth
            for i in range(len(quarters)):
                if i >= 4 and quarters[i]["revenue_b"] and quarters[i-4]["revenue_b"]:
                    old = quarters[i-4]["revenue_b"]
                    new = quarters[i]["revenue_b"]
                    quarters[i]["yoy_revenue_growth_pct"] = round((new-old)/old*100,1)
        # summary
        latest = quarters[-1] if quarters else {}
        summary = {
            "latest_revenue_b": latest.get("revenue_b"),
            "latest_yoy_revenue_growth_pct": latest.get("yoy_revenue_growth_pct"),
            "latest_gross_margin_pct": latest.get("gross_margin_pct"),
            "latest_net_margin_pct": latest.get("net_margin_pct"),
        }
        # growth verdict
        recent_growths = [q["yoy_revenue_growth_pct"] for q in quarters[-4:] if q.get("yoy_revenue_growth_pct") is not None]
        if len(recent_growths) >= 2:
            trend = recent_growths[-1] - recent_growths[0]
            if recent_growths[-1] > 10 and trend > 0:   state = "accelerating"
            elif recent_growths[-1] > 0:                 state = "growing"
            elif trend < 0 and recent_growths[-1] < 0:  state = "contracting"
            else:                                         state = "decelerating"
            labels_map = {"accelerating":"🚀 Accelerating","growing":"📈 Growing",
                         "decelerating":"📉 Decelerating","contracting":"⬇ Contracting"}
            cagr = None
            if len(recent_growths) >= 2:
                import math
                try: cagr = round(math.pow(1+recent_growths[-1]/100, 0.5) * math.pow(1+recent_growths[0]/100, 0.5) * 100 - 100, 1)
                except: cagr = None
            verdict = {"state": state, "label": labels_map.get(state,""), "cagr_2y": cagr}
        else:
            verdict = {}
        return jsonify({"symbol": symbol, "quarterly": quarters, "summary": summary, "growth_verdict": verdict})
    except Exception as e:
        return jsonify({"symbol": symbol, "quarterly": [], "summary": {}, "growth_verdict": {}, "error": str(e)})


@app.route("/api/earnings/<symbol>")
def get_earnings(symbol):
    symbol = symbol.upper()
    try:
        import yfinance as yf, pandas as pd
        t = yf.Ticker(symbol)
        earnings = []
        # Use quarterly income statement for EPS approximation
        qis = t.quarterly_income_stmt
        if qis is not None and not qis.empty:
            ni_row = None
            rev_row = None
            for key in ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operation Net Minority Interest"]:
                if key in qis.index:
                    ni_row = qis.loc[key]; break
            for key in ["Total Revenue", "Revenue"]:
                if key in qis.index:
                    rev_row = qis.loc[key]; break
            info = t.fast_info
            shares = getattr(info, 'shares', None) or 1e9
            cols = sorted(qis.columns)[-8:]
            for col in cols:
                ni = float(ni_row[col]) if ni_row is not None and not pd.isna(ni_row.get(col, float('nan'))) else None
                eps = round(ni / shares, 2) if ni else None
                earnings.append({
                    "period": col.strftime("%Y Q%q") if hasattr(col, 'strftime') else str(col)[:7],
                    "actual": eps,
                    "estimate": None,
                    "surprise": None,
                })
        return jsonify({"symbol": symbol, "earnings": earnings})
    except Exception as e:
        return jsonify({"symbol": symbol, "earnings": [], "error": str(e)})


# ─────────────────────────────────────────────────────────────────────────────
# BUY READINESS SCORE + INVESTOR LENS
# ─────────────────────────────────────────────────────────────────────────────

_analysis_cache     = {}
_analysis_cache_ts  = {}
_ANALYSIS_TTL       = 300  # 5 min

def _clamp(v, lo, hi): return max(lo, min(hi, v))

def _compute_analysis(sym):
    pc = price_cache.get(sym, {})
    fc = fund_cache.get(sym, {})
    if not pc:
        return None

    price     = pc.get("price") or 0
    ma50      = pc.get("ma50")
    ma200     = pc.get("ma200")
    rsi       = pc.get("rsi") or 50
    pe        = fc.get("trailing_pe")
    fwd_pe    = fc.get("forward_pe")
    pb        = fc.get("pb")
    profit_m  = fc.get("profit_margin") or 0   # already in %
    rev_growth= fc.get("revenue_growth") or 0  # already in %
    beta      = fc.get("beta") or 1.0
    high_52w  = fc.get("high_52w") or price
    low_52w   = fc.get("low_52w") or price
    target_m  = fc.get("target_mean")
    rec_mean  = fc.get("strong_buy")            # 1=StrongBuy … 5=StrongSell
    n_analysts= fc.get("num_analysts") or 0
    ccy       = pc.get("currency", "USD")

    # ── sub-scores used across multiple components ──
    pe_score     = _clamp(100 - (pe - 10) * 2, 5, 95)    if pe      else 50
    pb_score     = _clamp(100 - (pb - 1) * 8, 5, 95)     if pb      else 50
    upside_pct   = ((target_m / price) - 1) * 100         if (target_m and price) else 0
    upside_score = _clamp(50 + upside_pct * 1.0, 5, 95)
    margin_score = _clamp(50 + profit_m * 1.5, 5, 95)
    rev_score    = _clamp(50 + rev_growth * 2,  5, 95)
    rec_score    = _clamp(100 - (rec_mean - 1) * 25, 5, 95) if rec_mean else 50

    # ── Valuation (25%) ──
    fwd_disc  = _clamp(100 - (fwd_pe / pe) * 50, 30, 80) if (fwd_pe and pe) else 50
    valuation = round(0.35*pe_score + 0.25*pb_score + 0.30*upside_score + 0.10*fwd_disc)

    # ── Quality (25%) ──
    quality = round(0.40*margin_score + 0.30*rev_score + 0.30*rec_score)

    # ── Momentum (20%) ──
    if price and ma50 and ma200:
        if   price > ma50 > ma200: ma_score = 90   # golden / strong uptrend
        elif price > ma200:        ma_score = 65   # above LT MA, pullback
        elif price > ma50:         ma_score = 55   # early recovery
        else:                      ma_score = 30   # below both (downtrend)
    else:
        ma_score = 50

    rsi_score = _clamp(100 - abs(rsi - 47) * 2, 20, 90)   # sweet-spot ~47

    if high_52w > low_52w and price:
        pos_52w      = (price - low_52w) / (high_52w - low_52w)
        range_score  = _clamp(80 - abs(pos_52w - 0.55) * 60, 30, 85)
    else:
        range_score = 50

    momentum = round(0.40*ma_score + 0.35*rsi_score + 0.25*range_score)

    # ── Sentiment (15%) ──
    upside_sent  = _clamp(50 + upside_pct * 1.5, 5, 95)
    coverage     = _clamp(n_analysts * 4, 10, 90)
    sentiment    = round(0.45*upside_sent + 0.35*rec_score + 0.20*coverage)

    # ── Risk Adjusted (15%) ──
    beta_risk      = _clamp(100 - (beta - 0.5) * 30, 20, 90)
    drawdown_pct   = ((high_52w - price) / high_52w * 100) if high_52w else 0
    drawdown_score = _clamp(80 - abs(drawdown_pct - 15) * 1.0, 20, 90)
    rsi_risk       = _clamp(100 - (rsi - 30) * 1.2, 25, 90)
    risk_adj       = round(0.35*beta_risk + 0.35*drawdown_score + 0.30*rsi_risk)

    # ── Buy Score ──
    buy_score = round(0.25*valuation + 0.25*quality + 0.20*momentum + 0.15*sentiment + 0.15*risk_adj)

    if   buy_score >= 72: verdict = "Strong Buy"
    elif buy_score >= 58: verdict = "Reasonable Entry"
    elif buy_score >= 45: verdict = "Hold / Watch"
    else:                 verdict = "Avoid"

    # ── Investor Lens ──

    # Buffett — quality moat, consistent earnings, reasonable price
    buffett_s = round(_clamp(0.35*margin_score + 0.25*rec_score + 0.20*pe_score + 0.20*rev_score, 0, 100))
    if   buffett_s >= 70: buffett_v = "Buy"
    elif buffett_s >= 50: buffett_v = "Hold"
    else:                 buffett_v = "Avoid"
    if   margin_score >= 70: buff_r = "Strong margins indicate durable competitive moat"
    elif pe_score >= 65:     buff_r = "Reasonable valuation for a quality business"
    else:                    buff_r = "Margins or earnings consistency below Buffett threshold"

    # Burry — deep value, contrarian, oversold
    burry_contrarian = _clamp(100 - rsi, 30, 90)   # loves oversold
    burry_s = round(_clamp(0.35*pe_score + 0.30*pb_score + 0.20*burry_contrarian + 0.15*upside_score, 0, 100))
    if   burry_s >= 70: burry_v = "Buy"
    elif burry_s >= 50: burry_v = "Hold"
    else:               burry_v = "Avoid"
    if   pb_score >= 70: burry_r = "Low P/B suggests deep value opportunity"
    elif pe_score >= 70: burry_r = "Trading at significant discount to intrinsic value"
    else:                burry_r = "Insufficient margin of safety for a contrarian bet"

    # Lynch — GARP: growth at reasonable price
    if pe and rev_growth and rev_growth > 0:
        peg_raw   = pe / rev_growth
        peg_score = _clamp(100 - peg_raw * 20, 10, 90)
    else:
        peg_score = 50
    lynch_s = round(_clamp(0.40*peg_score + 0.35*rev_score + 0.25*margin_score, 0, 100))
    if   lynch_s >= 70: lynch_v = "Buy"
    elif lynch_s >= 50: lynch_v = "Hold"
    else:               lynch_v = "Avoid"
    if   peg_score >= 70: lynch_r = "PEG ratio attractive — growth priced reasonably"
    elif rev_score >= 70: lynch_r = "Strong revenue growth, watch valuation"
    else:                 lynch_r = "Growth rate doesn't justify current multiple"

    # Simons — quant: momentum + statistical patterns
    simons_mr  = _clamp(100 - abs(rsi - 50) * 2, 30, 90)
    beta_pred  = _clamp(100 - abs(beta - 1.0) * 40, 20, 90)  # likes predictable beta ~1
    simons_s   = round(_clamp(0.40*ma_score + 0.35*simons_mr + 0.25*beta_pred, 0, 100))
    if   simons_s >= 70: simons_v = "Buy"
    elif simons_s >= 50: simons_v = "Hold"
    else:                simons_v = "Avoid"
    if   ma_score >= 80: simons_r = "Strong trend alignment across moving averages"
    elif simons_mr >= 70: simons_r = "Statistical momentum pattern identified"
    else:                simons_r = "Insufficient quantitative signal clarity"

    # Dalio — macro balanced: low volatility, diversified, fair value
    dalio_stable = _clamp(80 - abs(beta - 0.8) * 25, 20, 85)
    dalio_s      = round(_clamp(0.30*dalio_stable + 0.30*valuation + 0.25*rec_score + 0.15*risk_adj, 0, 100))
    if   dalio_s >= 70: dalio_v = "Buy"
    elif dalio_s >= 50: dalio_v = "Hold"
    else:               dalio_v = "Avoid"
    if   dalio_stable >= 65: dalio_r = "Stable beta fits balanced macro portfolio"
    elif valuation >= 60:    dalio_r = "Fair valuation supports all-weather allocation"
    else:                    dalio_r = "Volatility profile too high for macro balance strategy"

    # ── Insights ──
    insights = []
    ccy_sym = "₪" if ccy == "ILS" else "$"
    if target_m and price:
        dir_str = f"+{upside_pct:.1f}% upside" if upside_pct > 0 else f"{upside_pct:.1f}% downside risk"
        insights.append(f"Analyst target: {ccy_sym}{target_m:.2f} ({dir_str})")
    if rsi > 70:
        insights.append(f"RSI {rsi:.0f} — overbought, risk of near-term pullback")
    elif rsi < 30:
        insights.append(f"RSI {rsi:.0f} — oversold, watch for reversal signal")
    if high_52w and price:
        below_high = (high_52w - price) / high_52w * 100
        if below_high > 25:
            insights.append(f"{below_high:.0f}% below 52-week high ({ccy_sym}{high_52w:.2f})")
    if ma50 and ma200:
        if ma50 > ma200 and price > ma50:
            insights.append("Golden cross active — 50MA above 200MA (bullish trend)")
        elif ma50 < ma200:
            insights.append("Death cross — 50MA below 200MA (bearish caution)")
    if beta > 1.5:
        insights.append(f"High beta ({beta:.1f}x) — elevated volatility vs market")
    if pe and pe > 40:
        insights.append(f"P/E of {pe:.1f}x — premium multiple, growth must justify it")

    return {
        "ticker":    sym,
        "buy_score": buy_score,
        "verdict":   verdict,
        "components": {
            "valuation": valuation,
            "quality":   quality,
            "momentum":  momentum,
            "sentiment": sentiment,
            "risk":      risk_adj,
        },
        "investor_lens": {
            "buffett": {"score": buffett_s, "verdict": buffett_v, "reason": buff_r},
            "burry":   {"score": burry_s,   "verdict": burry_v,   "reason": burry_r},
            "lynch":   {"score": lynch_s,   "verdict": lynch_v,   "reason": lynch_r},
            "simons":  {"score": simons_s,  "verdict": simons_v,  "reason": simons_r},
            "dalio":   {"score": dalio_s,   "verdict": dalio_v,   "reason": dalio_r},
        },
        "insights": insights,
    }


@app.route("/api/analysis/<symbol>")
def get_analysis(symbol):
    sym = symbol.upper()
    now = time.time()
    if sym in _analysis_cache and now - _analysis_cache_ts.get(sym, 0) < _ANALYSIS_TTL:
        return jsonify(_analysis_cache[sym])
    result = _compute_analysis(sym)
    if result is None:
        return jsonify({"error": "symbol not loaded", "ticker": sym}), 404
    _analysis_cache[sym]    = result
    _analysis_cache_ts[sym] = now
    return jsonify(result)


# ── Earnings Whisper Score ────────────────────────────────────────────────────
try:
    from earnings_whisper import get_earnings_whisper_score as _ew_score
    _EW_AVAILABLE = True
    logger.info("earnings_whisper module loaded")
except ImportError as _e:
    _EW_AVAILABLE = False
    logger.warning(f"earnings_whisper module not available: {_e}")

_ew_cache    = {}
_ew_cache_ts = {}
_EW_TTL      = 4 * 3600  # 4 hours

@app.route("/api/stock/<symbol>/earnings-whisper")
def earnings_whisper_route(symbol):
    sym = symbol.upper().strip()
    now = time.time()
    # Serve from cache if fresh
    if sym in _ew_cache and now - _ew_cache_ts.get(sym, 0) < _EW_TTL:
        cached = dict(_ew_cache[sym])
        cached["cache_hit"] = True
        return jsonify(cached)
    if not _EW_AVAILABLE:
        return jsonify({"error": "earnings_whisper module not loaded", "symbol": sym}), 503
    try:
        result = _ew_score(sym)
        _ew_cache[sym]    = result
        _ew_cache_ts[sym] = now
        result["cache_hit"] = False
        if _DD_AVAILABLE:
            span = tracer.current_span()
            if span:
                span.set_tag("stock.symbol", sym)
                span.set_tag("earnings.score", result.get("score"))
                span.set_tag("earnings.signal", result.get("signal"))
        logger.info("Earnings Whisper served", extra={"stock.symbol": sym, "earnings.score": result.get("score"), "event": "earnings_whisper_served"})
        return jsonify(result)
    except Exception as exc:
        logger.error(f"Earnings Whisper error for {sym}: {exc}", exc_info=True)
        return jsonify({"error": str(exc), "symbol": sym}), 500


# ── Google OAuth + User Management ───────────────────────────────────────────
try:
    from auth_module import register_auth_blueprints
    register_auth_blueprints(app)
    logger.info("Auth blueprints registered (Google OAuth + user endpoints)")
except ImportError as _e:
    logger.warning(f"auth_module not available (Google OAuth disabled): {_e}")
    # Stub endpoints so frontend doesn't get 404s
    @app.route("/auth/google", methods=["POST"])
    def auth_google_stub():
        return jsonify({"error": "Google OAuth not configured. Set GOOGLE_CLIENT_ID."}), 501

    @app.route("/auth/me")
    def auth_me_stub():
        return jsonify({"error": "Auth not configured"}), 501

    @app.route("/api/user/watchlist", methods=["GET", "POST"])
    def user_watchlist_stub():
        return jsonify({"symbols": [], "note": "Auth not configured — using local watchlist"}), 200

    @app.route("/api/user/watchlist/<symbol>", methods=["DELETE"])
    def user_watchlist_delete_stub(symbol):
        return jsonify({"removed": symbol, "note": "Auth not configured"}), 200



# ── AI Chat (Claude API) ──────────────────────────────────────────────────────
try:
    from ai_features import get_earnings_explanation as _ai_explain
    _AI_AVAILABLE = True
    logger.info("ai_features module loaded (Claude API)")
except ImportError as _e:
    _AI_AVAILABLE = False
    logger.warning(f"ai_features module not available: {_e}")

@app.route("/api/stock/<symbol>/earnings-whisper/explain")
def earnings_whisper_explain(symbol):
    sym = symbol.upper().strip()
    if not _EW_AVAILABLE:
        return jsonify({"explanation": "Earnings Whisper not available."}), 503
    score_data = _ew_cache.get(sym) or _ew_score(sym)
    if not _AI_AVAILABLE:
        score = score_data.get("score", 0)
        signal = score_data.get("signal", "Unknown")
        return jsonify({"explanation": f"{sym} has an Earnings Whisper Score of {score} ({signal}). Install the anthropic package for AI-generated explanations."})
    try:
        explanation = _ai_explain(sym, score_data)
        return jsonify({"explanation": explanation, "symbol": sym})
    except Exception as exc:
        return jsonify({"explanation": f"AI explanation unavailable: {exc}", "symbol": sym}), 200


# ── Live News endpoint ─────────────────────────────────────────────────────────
import xml.etree.ElementTree as _ET, re as _re, datetime as _dt

_news_cache = {}

def _fetch_rss(url):
    try:
        req = _ureq.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; KestrelNewsBot/1.0)'})
        with _ureq.urlopen(req, timeout=5) as r:
            return r.read()
    except Exception:
        return None

def _parse_rss(xml_bytes, default_src):
    if not xml_bytes: return []
    items = []
    try:
        root = _ET.fromstring(xml_bytes)
        ch   = root.find('channel')
        entries = ch.findall('item') if ch is not None else root.findall('.//item')
        for item in entries:
            title = (item.findtext('title') or '').strip()
            link  = (item.findtext('link')  or '').strip()
            pub   = (item.findtext('pubDate') or '').strip()
            src_el = item.find('source')
            src = src_el.text.strip() if src_el is not None and src_el.text else default_src
            if title and link:
                items.append({'headline': title, 'source': src, 'url': link, 'pubDate': pub})
    except _ET.ParseError:
        pass
    return items

def _parse_pubdate(s):
    for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S GMT', '%a, %d %b %Y %H:%M:%S +0000'):
        try:
            d = _dt.datetime.strptime(s, fmt)
            if d.tzinfo is None: d = d.replace(tzinfo=_dt.timezone.utc)
            return d.timestamp()
        except ValueError:
            continue
    return 0.0

def _time_ago(ts):
    if not ts: return ''
    d = int(time.time() - ts)
    if d < 60:    return f'{d}s ago'
    if d < 3600:  return f'{d//60}m ago'
    if d < 86400: return f'{d//3600}h ago'
    return f'{d//86400}d ago'

_POS = _re.compile(r'\b(beats?|beat|upgrade[sd]?|rally|surge[sd]?|record|rise[sd]?|gain[sd]?)\b', _re.I)
_NEG = _re.compile(r'\b(miss(es|ed)?|downgrade[sd]?|falls?|crash(es|ed)?|cut[s]?|warn[s]?|drop[s]?|decline[sd]?)\b', _re.I)

def _sentiment(h):
    if _POS.search(h): return 'pos'
    if _NEG.search(h): return 'neg'
    return 'neu'

def _dedup(items, n=8):
    seen, kept = [], []
    for item in items:
        words = set(_re.sub(r'[^a-z0-9 ]', '', item['headline'].lower()).split())
        if not any(words and sw and len(words & sw)/max(len(words),len(sw)) > 0.6 for sw in seen):
            kept.append(item); seen.append(words)
        if len(kept) >= n: break
    return kept

@app.route('/api/stock/<symbol>/news')
def stock_news(symbol):
    sym = symbol.upper()
    now = time.time()
    cached = _news_cache.get(sym)
    if cached and (now - cached['ts']) < 600:
        return jsonify(cached['data'])

    g_raw = _fetch_rss(f'https://news.google.com/rss/search?q={sym}+stock&hl=en-US&gl=US&ceid=US:en')
    y_raw = _fetch_rss(f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US')

    merged = _parse_rss(g_raw, 'Google News') + _parse_rss(y_raw, 'Yahoo Finance')
    merged.sort(key=lambda x: _parse_pubdate(x['pubDate']), reverse=True)
    deduped = _dedup(merged)

    result = [{'headline': i['headline'], 'source': i['source'], 'url': i['url'],
               'published_at': i['pubDate'], 'time_ago': _time_ago(_parse_pubdate(i['pubDate'])),
               'sentiment': _sentiment(i['headline'])} for i in deduped]

    _news_cache[sym] = {'data': result, 'ts': now}
    return jsonify(result)


# ── Social Sentiment endpoint (Stocktwits) ────────────────────────────────────
_sentiment_cache = {}
_SENTIMENT_CACHE_TTL = 300  # 5 minutes

@app.route('/api/stock/<symbol>/social-sentiment')
def stock_social_sentiment(symbol):
    sym = symbol.upper().replace('.TA', '')  # Stocktwits uses US tickers

    now = time.time()
    if sym in _sentiment_cache and now - _sentiment_cache[sym]['ts'] < _SENTIMENT_CACHE_TTL:
        return jsonify(_sentiment_cache[sym]['data'])

    try:
        import urllib.request
        url = f'https://api.stocktwits.com/api/2/streams/symbol/{sym}.json?limit=30'
        req = urllib.request.Request(url, headers={'User-Agent': 'KestrelApp/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = json.loads(resp.read().decode())

        msgs = raw.get('messages', [])

        # Sentiment keywords fallback
        BULL_KW = {'breakout','buy','calls','moon','bullish','support','accumulate','long','upgrade','beat','strong','rally','upside'}
        BEAR_KW = {'puts','short','sell','bearish','resistance','overvalued','downgrade','miss','weak','drop','crash','dump'}

        def classify(text, explicit):
            if explicit == 'Bullish': return True
            if explicit == 'Bearish': return False
            words = set(text.lower().split())
            bull_hits = len(words & BULL_KW)
            bear_hits = len(words & BEAR_KW)
            if bull_hits > bear_hits: return True
            if bear_hits > bull_hits: return False
            return None  # neutral/unknown

        def time_ago(ts_str):
            try:
                from datetime import datetime, timezone
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                diff = datetime.now(timezone.utc) - dt
                s = int(diff.total_seconds())
                if s < 60: return f'{s}s ago'
                if s < 3600: return f'{s//60}m ago'
                if s < 86400: return f'{s//3600}h ago'
                return f'{s//86400}d ago'
            except: return 'recently'

        processed = []
        bull_count = 0
        bear_count = 0

        for m in msgs:
            explicit = ((m.get('entities') or {}).get('sentiment') or {}).get('basic')
            text = m.get('body', '')
            is_bull = classify(text, explicit)
            user = m.get('user', {}).get('username', 'anonymous')
            msg_id = m.get('id', '')

            if is_bull is True: bull_count += 1
            elif is_bull is False: bear_count += 1

            processed.append({
                'user': user,
                'text': text[:200],
                'bull': is_bull if is_bull is not None else True,
                'time_ago': time_ago(m.get('created_at', '')),
                'url': f'https://stocktwits.com/{user}/message/{msg_id}'
            })

        total_labeled = bull_count + bear_count
        if total_labeled == 0:
            bull_pct = 50
            bear_pct = 50
        else:
            bull_pct = round(bull_count / total_labeled * 100, 1)
            bear_pct = round(100 - bull_pct, 1)

        result = {
            'bullPct': bull_pct,
            'bearPct': bear_pct,
            'sample_size': len(msgs),
            'confidence': 'high' if total_labeled >= 15 else 'medium' if total_labeled >= 5 else 'low',
            'messages': processed[:8],
            'source': 'stocktwits'
        }

        _sentiment_cache[sym] = {'ts': now, 'data': result}
        return jsonify(result)

    except Exception as e:
        logger.warning(f'Social sentiment fetch failed for {sym}: {e}')
        # Return mock fallback
        return jsonify({
            'bullPct': 50, 'bearPct': 50,
            'messages': [], 'source': 'unavailable',
            'sample_size': 0, 'confidence': 'low'
        })


print(f"Stock backend v2 (yfinance) | pid={os.getpid()} | node={os.environ.get('NODE_NAME','')} | ip={os.environ.get('POD_IP','')}", flush=True)
app.run(host="0.0.0.0", port=8080, threaded=True)
