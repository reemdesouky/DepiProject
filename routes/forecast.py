from flask import Blueprint, jsonify, request
from config.db import get_db
from services.dashboard_service import get_day_columns
from services.forecast_service import run_forecast

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/run/<item_id>")
def run(item_id):
    """
    GET /api/forecast/run/HOBBIES_1_003?store_id=CA_1&horizon=28
    بيشغل الـ ML model ويرجع predictions
    """
    store_id = request.args.get("store_id")
    horizon  = int(request.args.get("horizon", 28))

    if not store_id:
        return jsonify({"error": "store_id is required"}), 400

    result = run_forecast(item_id, store_id, horizon)

    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 404

    # احفظ النتائج في DB
    db  = get_db()
    import datetime
    db.forecasts.replace_one(
        {"item_id": item_id, "store_id": store_id},
        {
            "item_id":     item_id,
            "store_id":    store_id,
            "predictions": result,
            "created_at":  datetime.datetime.utcnow(),
        },
        upsert=True
    )

    return jsonify({
        "item_id":     item_id,
        "store_id":    store_id,
        "horizon":     horizon,
        "predictions": result,
    })


@forecast_bp.route("/input/<item_id>")
def get_forecast_input(item_id):
    db       = get_db()
    store_id = request.args.get("store_id")
    day_cols = get_day_columns(365)

    cal_map = {
        doc["d"]: {
            "date":    doc["date"].strftime("%Y-%m-%d") if hasattr(doc["date"], "strftime") else str(doc["date"])[:10],
            "weekday": doc.get("weekday"),
            "month":   doc.get("month"),
            "year":    doc.get("year"),
            "snap_CA": doc.get("snap_CA", 0),
            "snap_TX": doc.get("snap_TX", 0),
            "snap_WI": doc.get("snap_WI", 0),
        }
        for doc in db.calender.find(
            {"d": {"$in": day_cols}},
            {"d": 1, "date": 1, "weekday": 1, "month": 1, "year": 1,
             "snap_CA": 1, "snap_TX": 1, "snap_WI": 1, "_id": 0}
        )
    }

    query = {"item_id": item_id}
    if store_id:
        query["store_id"] = store_id

    sales_docs = list(db.sales.find(
        query,
        {"store_id": 1, "dept_id": 1, "cat_id": 1, "state_id": 1,
         "_id": 0, **{d: 1 for d in day_cols}}
    ))

    result = []
    for doc in sales_docs:
        for d in day_cols:
            cal = cal_map.get(d, {})
            result.append({
                "item_id":  item_id,
                "store_id": doc.get("store_id"),
                "dept_id":  doc.get("dept_id"),
                "cat_id":   doc.get("cat_id"),
                "state_id": doc.get("state_id"),
                "d_col":    d,
                "date":     cal.get("date"),
                "weekday":  cal.get("weekday"),
                "month":    cal.get("month"),
                "year":     cal.get("year"),
                "snap_CA":  cal.get("snap_CA", 0),
                "snap_TX":  cal.get("snap_TX", 0),
                "snap_WI":  cal.get("snap_WI", 0),
                "units":    doc.get(d, 0),
            })

    price_doc = db.prices.find_one(
        {"item_id": item_id},
        {"sell_price": 1, "_id": 0},
        sort=[("wm_yr_wk", -1)]
    )

    return jsonify({
        "item_id":    item_id,
        "store_id":   store_id,
        "sell_price": price_doc["sell_price"] if price_doc else None,
        "history":    result,
    })


@forecast_bp.route("/result", methods=["POST"])
def save_forecast_result():
    db   = get_db()
    body = request.get_json()

    if not body or "item_id" not in body or "predictions" not in body:
        return jsonify({"error": "item_id and predictions are required"}), 400

    import datetime
    doc = {
        "item_id":     body["item_id"],
        "store_id":    body.get("store_id"),
        "predictions": body["predictions"],
        "created_at":  datetime.datetime.utcnow(),
    }
    result = db.forecasts.replace_one(
        {"item_id": body["item_id"], "store_id": body.get("store_id")},
        doc,
        upsert=True
    )
    return jsonify({"status": "saved", "upserted": result.upserted_id is not None})


@forecast_bp.route("/result/<item_id>")
def get_forecast_result(item_id):
    db       = get_db()
    store_id = request.args.get("store_id")

    query = {"item_id": item_id}
    if store_id:
        query["store_id"] = store_id

    doc = db.forecasts.find_one(query, {"_id": 0})
    if not doc:
        return jsonify({"error": "No forecast found"}), 404

    if "created_at" in doc:
        doc["created_at"] = doc["created_at"].isoformat()

    return jsonify(doc)
# ضيف الـ import ده فوق مع باقي الـ imports في ملف الـ routes:
from services.forecast_service import run_forecast, get_last_available_date


# وضيف الـ route ده في أي مكان جوه forecast_bp:
@forecast_bp.route("/last-date")
def last_date():
    """
    بيرجع آخر تاريخ متاح في الـ dataset.
    الفرونت إند بيستخدمه كـ 'النهارده' عشان يحسب الـ horizon صح،
    لأن الداتا (M5) تاريخها 2014-2016 مش تاريخ النهارده الحقيقي.
    """
    date = get_last_available_date()
    if not date:
        return jsonify({"error": "No calendar data found"}), 404
    return jsonify({"last_date": date})