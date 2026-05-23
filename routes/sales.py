from flask import Blueprint, jsonify, request
from config.db import get_db
from services.dashboard_service import get_day_columns

sales_bp = Blueprint("sales", __name__)


@sales_bp.route("/")
def get_sales():
    """
    GET /api/sales?store_id=CA_1&cat_id=HOBBIES&period=30d&page=1&limit=50
   
    """
    db       = get_db()
    store_id = request.args.get("store_id")
    cat_id   = request.args.get("cat_id")
    period   = request.args.get("period", "30d")
    page     = int(request.args.get("page", 1))
    limit    = int(request.args.get("limit", 50))

    period_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days     = period_map.get(period, 30)
    day_cols = get_day_columns(days)

    query = {}
    if store_id:
        query["store_id"] = store_id
    if cat_id:
        query["cat_id"] = cat_id

    projection = {"item_id": 1, "store_id": 1, "cat_id": 1, "dept_id": 1, "_id": 0}
    for d in day_cols:
        projection[d] = 1

    skip  = (page - 1) * limit
    docs  = list(db.sales.find(query, projection).skip(skip).limit(limit))
    total = db.sales.count_documents(query)

    return jsonify({
        "data":    docs,
        "total":   total,
        "page":    page,
        "pages":   (total + limit - 1) // limit,
        "period":  period,
        "columns": day_cols,
    })


@sales_bp.route("/item/<item_id>")
def get_item_sales(item_id):
    """
    GET /api/sales/item/HOBBIES_1_003
   
    """
    db       = get_db()
    day_cols = get_day_columns(90)

    cal_map = {
        doc["d"]: doc["date"].strftime("%Y-%m-%d") if hasattr(doc["date"], "strftime") else str(doc["date"])[:10]
        for doc in db.calender.find({"d": {"$in": day_cols}}, {"d": 1, "date": 1, "_id": 0})
    }

    docs = list(db.sales.find(
        {"item_id": item_id},
        {"store_id": 1, "_id": 0, **{d: 1 for d in day_cols}}
    ))

    result = []
    for doc in docs:
        for d in day_cols:
            result.append({
                "store_id": doc.get("store_id"),
                "date":     cal_map.get(d, d),
                "units":    doc.get(d, 0),
            })

    return jsonify(result)


@sales_bp.route("/stores")
def get_stores():
    """GET /api/sales/stores — """
    db    = get_db()
    stores = list(db.stores.find({}, {"_id": 0}))
    return jsonify(stores)


@sales_bp.route("/categories")
def get_categories():
    """GET /api/sales/categories — categories"""
    db   = get_db()
    cats = db.sales.distinct("cat_id")
    return jsonify(cats)
