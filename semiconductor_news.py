import feedparser
import smtplib
import yfinance as yf
import pandas as pd
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- CONFIGURATION FROM GITHUB SECRETS ---
# These grab the secure variables you set in GitHub Settings
SENDER_EMAIL = os.environ.get("huangzhizhong100@gmail.com")
SENDER_PASSWORD = os.environ.get("kruw xyah jgxc gajt")
RECEIVER_EMAIL = os.environ.get("huangzhizhong100@gmail.com")

# Define Major Semiconductor Companies (Tickers)
SEMI_TICKERS = [
    "NVDA", "TSM", "AVGO", "ASML", "AMD", 
    "QCOM", "TXN", "INTC", "MU", "AMAT", "LRCX", "ADI"
]

# News Search Settings
TOPIC = "Semiconductor"
KEYWORDS = "(strategy OR finance OR investment OR fundraising OR 'new product' OR 'major event' OR earnings)"
TIME_WINDOW = "when:1d"

def fetch_news():
    """Fetches news from Google News RSS."""
    print("Fetching news...")
    query = f"{TOPIC} AND {KEYWORDS} {TIME_WINDOW}"
    encoded_query = query.replace(" ", "%20")
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(rss_url)
    news_items = []
    
    for entry in feed.entries[:10]: 
        item = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'source': entry.source.title if 'source' in entry else 'Unknown Source'
        }
        news_items.append(item)
    return news_items

def fetch_earnings_and_prices():
    """Checks for recent earnings and current stock prices."""
    print("Fetching market data...")
    earnings_updates = []
    market_summary = []
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    for ticker in SEMI_TICKERS:
        try:
            stock = yf.Ticker(ticker)
            
            # 1. Get Current Price info
            hist = stock.history(period="2d")
            if len(hist) >= 1:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                pct_change = ((current_price - prev_close) / prev_close) * 100
                
                market_summary.append({
                    'ticker': ticker,
                    'price': f"${current_price:.2f}",
                    'change': f"{pct_change:+.2f}%",
                    'color': "green" if pct_change >= 0 else "red"
                })

            # 2. Check Earnings Calendar
            dates = stock.earnings_dates
            if dates is not None and not dates.empty:
                recent_earnings = dates[
                    (dates.index.date == today) | 
                    (dates.index.date == yesterday)
                ]
                
                if not recent_earnings.empty:
                    row = recent_earnings.iloc[0]
                    est = row.get('EPS Estimate', 'N/A')
                    act = row.get('Reported EPS', 'N/A')
                    
                    earnings_updates.append({
                        'ticker': ticker,
                        'date': recent_earnings.index[0].strftime('%Y-%m-%d'),
                        'estimate': f"{est:.2f}" if isinstance(est, (int, float)) else "N/A",
                        'actual': f"{act:.2f}" if isinstance(act, (int, float)) else "Pending"
                    })
                    
        except Exception as e:
            print(f"Note: Could not fetch data for {ticker} ({e})")
            continue

    return market_summary, earnings_updates

def format_email_body(news_items, market_summary, earnings_updates):
    """Formats the email with News, Market Data, and Earnings."""
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #003366;">⚡ Semi Industry Daily - {today_date}</h2>
        
        <div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="margin-top: 0; font-size: 16px;">📈 Major Players Snapshot</h3>
            <table style="width: 100%; font-size: 14px;">
                <tr>
    """
    
    for i, stock in enumerate(market_summary):
        if i > 0 and i % 4 == 0: html += "</tr><tr>"
        html += f"""
        <td style="padding: 5px;">
            <strong>{stock['ticker']}</strong>: {stock['price']} 
            <span style="color: {stock['color']};">({stock['change']})</span>
        </td>
        """
    html += "</tr></table></div>"

    if earnings_updates:
        html += """
        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #ffa500;">
            <h3 style="margin-top: 0; color: #d35400;">📢 Earnings Alert (Last 24h)</h3>
            <ul>
        """
        for item in earnings_updates:
            html += f"<li><strong>{item['ticker']}</strong> ({item['date']}): Est: {item['estimate']} vs Act: <strong>{item['actual']}</strong></li>"
        html += "</ul></div>"

    html += "<h3>📰 Strategic & Financial News</h3><hr><ul>"
    
    if not news_items:
        html += "<p>No major news updates found today.</p>"
    else:
        for item in news_items:
            html += f"""
            <li style="margin-bottom: 15px;">
                <strong><a href="{item['link']}" style="text-decoration: none; color: #0056b3;">{item['title']}</a></strong><br>
                <span style="font-size: 12px; color: #666;">{item['source']} | {item['published']}</span>
            </li>
            """
            
    html += """
        </ul>
        <hr>
        <p style="font-size: 12px; color: #888;">Automated GitHub Report</p>
    </body>
    </html>
    """
    return html

def send_email(subject, body):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Error: Email credentials missing. Check GitHub Secrets.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    print("Starting daily job...")
    
    news = fetch_news()
    market, earnings = fetch_earnings_and_prices()
    body = format_email_body(news, market, earnings)
    
    subject_prefix = "📢 Earnings & " if earnings else ""
    subject = f"{subject_prefix}Semiconductor Daily: {datetime.now().strftime('%b %d')}"
    
    send_email(subject, body)
