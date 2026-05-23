# Stockwise Flask API

## Setup

```bash
pip install -r requirements.txt
```

افتح `.env` وحط الـ MongoDB URI بتاعك:
```
MONGO_URI=mongodb+srv://<user>:<pass>@cluster0.xxxxx.mongodb.net/demand_forecasting
```

```bash
python app.py
```

---

## Endpoints

### Dashboard
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/dashboard/summary` | الـ 4 summary cards |
| GET | `/api/dashboard/trend?period=30d` | بيانات الشارت (7d/30d/90d/1y) |
| GET | `/api/dashboard/top-products?limit=10` | أكتر المنتجات مبيعاً |
| GET | `/api/dashboard/by-category` | مبيعات حسب category |
| GET | `/api/dashboard/by-store` | مبيعات حسب store |

### Sales
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/sales/?store_id=CA_1&cat_id=HOBBIES&period=30d` | قائمة المبيعات مع فلتر |
| GET | `/api/sales/item/<item_id>` | مبيعات منتج عبر الزمن |
| GET | `/api/sales/stores` | قائمة المتاجر |
| GET | `/api/sales/categories` | قائمة الـ categories |

### Products
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/products/?search=toy` | بحث في المنتجات |
| GET | `/api/products/<item_id>` | تفاصيل منتج + آخر سعر |
| GET | `/api/products/<item_id>/price-history?store_id=CA_1` | تاريخ السعر |

### Forecast (للـ ML Model)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/forecast/input/<item_id>?store_id=CA_1` | بيانات input للـ model |
| POST | `/api/forecast/result` | الـ model يبعت النتائج هنا |
| GET | `/api/forecast/result/<item_id>?store_id=CA_1` | عرض نتائج الـ forecast |

---

## للـ Data Scientist

الـ workflow مع الـ ML model:

1. **اجيب الداتا:** `GET /api/forecast/input/HOBBIES_1_003?store_id=CA_1`
2. **شغّل الـ model** على الـ `history` array
3. **ابعت النتائج:** `POST /api/forecast/result`
   ```json
   {
     "item_id": "HOBBIES_1_003",
     "store_id": "CA_1",
     "predictions": [
       {"date": "2016-06-20", "forecast": 3.5},
       {"date": "2016-06-21", "forecast": 4.1}
     ]
   }
   ```
4. الداشبورد يجيب النتائج من `GET /api/forecast/result/HOBBIES_1_003`
