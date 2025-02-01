from flask import Flask, render_template, request, jsonify
import yfinance as yf
from newsapi import NewsApiClient
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from flask_babel import Babel
from models import db, StockRecommendation, UserSettings

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stocks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
babel = Babel(app)

# Je potřeba získat vlastní API klíče
NEWS_API_KEY = '2e213b8081484c74934e9b1f0b46456a'
newsapi = NewsApiClient(api_key=NEWS_API_KEY)

def calculate_rsi(data, periods=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(data):
    exp1 = data.ewm(span=12, adjust=False).mean()
    exp2 = data.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return {'macd': macd, 'signal': signal, 'histogram': histogram}

def get_top_stocks():
    symbols = ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'META', 'TSLA', 'AMD', 'AMZN']
    recommendations = []
    
    for symbol in symbols:
        try:
            stock = analyze_stock(symbol)
            if stock.get('recommendation') == "Koupit":
                recommendations.append(stock)
        except:
            continue
            
    return sorted(recommendations, key=lambda x: x['confidence'], reverse=True)[:5]

def analyze_stock(symbol):
    try:
        # Získání dat o akciích
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")
        
        # Základní analýza
        current_price = hist['Close'][-1]
        target_price = current_price * 1.1  # 10% nad současnou cenou
        avg_50day = hist['Close'].tail(50).mean()
        avg_200day = hist['Close'].tail(200).mean()
        
        # Získání zpráv
        news = newsapi.get_everything(
            q=symbol,
            language='en',
            from_param=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            to=datetime.now().strftime('%Y-%m-%d'),
            sort_by='relevancy'
        )
        
        # Jednoduchá analýza trendu
        trend = "Rostoucí" if current_price > avg_50day else "Klesající"
        risk = "Vysoké" if hist['Close'].std() > hist['Close'].mean() * 0.02 else "Střední"
        
        # Technické indikátory
        rsi = calculate_rsi(hist['Close'])
        macd = calculate_macd(hist['Close'])
        
        # Rozšířená analýza
        technical_score = 0
        if rsi < 30: technical_score += 1  # Překoupený trh
        if macd['histogram'][-1] > 0: technical_score += 1  # Pozitivní momentum
        
        # Analýza sentimentu zpráv a technických indikátorů
        confidence = 0
        if rsi[-1] < 30: confidence += 20
        if macd['histogram'][-1] > 0: confidence += 20
        if current_price > hist['Close'].rolling(50).mean()[-1]: confidence += 20
        
        return {
            'symbol': symbol,
            'company_name': stock.info.get('longName', symbol),
            'current_price': round(current_price, 2),
            'target_price': round(target_price, 2),
            'estimated_days': 7,
            'confidence': confidence,
            'trend': trend,
            'risk': risk,
            'recommendation': "Koupit" if confidence > 50 else "Držet",
            'news': news['articles'][:5],
            'technical_indicators': {
                'rsi': round(rsi[-1], 2),
                'macd': round(macd['histogram'][-1], 2)
            }
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def home():
    top_stocks = get_top_stocks()
    return render_template('index.html', recommendations=top_stocks)

@app.route('/stock/<symbol>')
def stock_detail(symbol):
    analysis = analyze_stock(symbol)
    return render_template('stock_detail.html', stock=analysis)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    symbol = data.get('symbol')
    question = data.get('question')
    
    # Zde by byla implementace chatbota
    response = f"Analýza pro {symbol}: {question}"
    return jsonify({'response': response})

# Přidáme nové funkce pro statistiky
def get_statistics(start_date, end_date, risk_levels=None):
    query = StockRecommendation.query.filter(
        StockRecommendation.recommended_at.between(start_date, end_date)
    )
    
    if risk_levels:
        query = query.filter(StockRecommendation.risk_level.in_(risk_levels))
    
    recommendations = query.all()
    
    return {
        'total_trades': len(recommendations),
        'profitable_trades': len([r for r in recommendations if r.profit_loss and r.profit_loss > 0]),
        'total_profit': sum(r.profit_loss or 0 for r in recommendations),
        'avg_profit_per_trade': sum(r.profit_loss or 0 for r in recommendations) / len(recommendations) if recommendations else 0,
        'recommendations': recommendations
    }

@app.route('/api/statistics', methods=['POST'])
def get_stats():
    data = request.json
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    risk_levels = data.get('risk_levels')
    
    return jsonify(get_statistics(start_date, end_date, risk_levels))

@app.route('/settings', methods=['POST'])
def update_settings():
    data = request.json
    settings = UserSettings.query.first()
    if not settings:
        settings = UserSettings()
        db.session.add(settings)
    
    settings.language = data.get('language', settings.language)
    settings.theme = data.get('theme', settings.theme)
    db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True) 