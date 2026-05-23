from flask import Flask
from flask_cors import CORS
from config.db import init_db
from routes.dashboard import dashboard_bp
from routes.sales import sales_bp
from routes.products import products_bp
from routes.forecast import forecast_bp
from dotenv import load_dotenv
from routes.auth import auth_bp
import os
 
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "stockwise-secret-key-change-in-prod")
 


CORS(app, supports_credentials=True, origins=["http://localhost:8080", "http://127.0.0.1:8080"])
 


init_db(app)
app.register_blueprint(auth_bp,      url_prefix="/api/auth")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(sales_bp,     url_prefix="/api/sales")
app.register_blueprint(products_bp,  url_prefix="/api/products")
app.register_blueprint(forecast_bp,  url_prefix="/api/forecast")

@app.route("/api/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(debug=True, port=5000)
