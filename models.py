from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class StockRecommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    stop_loss = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    confidence = db.Column(db.Integer, nullable=False)
    recommended_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)
    exit_price = db.Column(db.Float, nullable=True)
    profit_loss = db.Column(db.Float, nullable=True)

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    language = db.Column(db.String(2), default='cs')
    theme = db.Column(db.String(10), default='light') 