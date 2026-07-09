from config.db import get_db


STORE_STATE_MAP = {
    "x": "CA",
    "y": "TX",
    "z": "WI",
}


def get_day_columns(period_days: int) -> list[str]:
    db = get_db()
    cal_docs = list(
        db.calender
          .find({}, {"d": 1, "_id": 0})
          .sort("date", -1)
    )
    all_d_cols = [doc["d"] for doc in cal_docs if "d" in doc]
    sample = db.sales.find_one({})
    if not sample:
        return []
    sales_cols = set(k for k in sample.keys() if k.startswith("d_"))
    valid = [d for d in all_d_cols if d in sales_cols]
    return valid[:period_days]


def get_summary(store: str = None):
    db = get_db()
    day_cols = get_day_columns(30)

    match = {}
    if store and store in STORE_STATE_MAP:
        match["state_id"] = STORE_STATE_MAP[store]

    pipeline = []
    if match:
        pipeline.append({"$match": match})
    pipeline += [
        {"$project": {
            "total_units": {
                "$add": [{"$ifNull": [f"${d}", 0]} for d in day_cols]
            }
        }},
        {"$group": {
            "_id": None,
            "total_units": {"$sum": "$total_units"}
        }}
    ]

    agg = list(db.sales.aggregate(pipeline))
    total_units = agg[0]["total_units"] if agg else 0

    num_products = db.products.count_documents({})
    num_stores   = db.stores.count_documents(
        {"state_id": STORE_STATE_MAP[store]} if store and store in STORE_STATE_MAP else {}
    )

    price_match = {}
    if store and store in STORE_STATE_MAP:
        price_match["store_id"] = {"$regex": f"^{STORE_STATE_MAP[store]}"}

    avg_price_pipeline = []
    if price_match:
        avg_price_pipeline.append({"$match": price_match})
    avg_price_pipeline.append({"$group": {"_id": None, "avg": {"$avg": "$sell_price"}}})

    avg_price_agg = list(db.prices.aggregate(avg_price_pipeline))
    avg_price     = avg_price_agg[0]["avg"] if avg_price_agg else 0
    total_revenue = round(total_units * avg_price, 2)

    return {
        "total_units_sold": total_units,
        "total_revenue":    total_revenue,
        "num_products":     num_products,
        "num_stores":       num_stores,
        "avg_price":        round(avg_price, 2),
    }


def get_sales_trend(period: str = "30d", store: str = None):
    period_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
    days     = period_map.get(period, 30)
    db       = get_db()
    day_cols = get_day_columns(days)

    pipeline = []
    if store and store in STORE_STATE_MAP:
        pipeline.append({"$match": {"state_id": STORE_STATE_MAP[store]}})

    group_stage = {"$group": {"_id": None}}
    for d in day_cols:
        group_stage["$group"][d] = {"$sum": {"$ifNull": [f"${d}", 0]}}
    pipeline.append(group_stage)

    agg    = list(db.sales.aggregate(pipeline))
    totals = agg[0] if agg else {}

    cal_map = {
        doc["d"]: doc["date"].strftime("%Y-%m-%d") if hasattr(doc["date"], "strftime") else str(doc["date"])[:10]
        for doc in db.calender.find({"d": {"$in": day_cols}}, {"d": 1, "date": 1, "_id": 0})
    }

    result = []
    for d in reversed(day_cols):
        result.append({
            "date":   cal_map.get(d, d),
            "actual": totals.get(d, 0),
        })
    return result


def get_top_products(limit: int = 10, store: str = None):
    db       = get_db()
    day_cols = get_day_columns(30)

    pipeline = []
    if store and store in STORE_STATE_MAP:
        pipeline.append({"$match": {"state_id": STORE_STATE_MAP[store]}})

    pipeline += [
        {"$project": {
            "item_id": 1,
            "total": {"$add": [{"$ifNull": [f"${d}", 0]} for d in day_cols]}
        }},
        {"$group": {
            "_id":   "$item_id",
            "total": {"$sum": "$total"}
        }},
        {"$sort":  {"total": -1}},
        {"$limit": limit},
        {"$lookup": {
            "from":         "products",
            "localField":   "_id",
            "foreignField": "item_id",
            "as":           "product_info"
        }},
        {"$project": {
            "item_id":      "$_id",
            "total_sold":   "$total",
            "product_name": {"$arrayElemAt": ["$product_info.product_name", 0]}
        }}
    ]
    return list(db.sales.aggregate(pipeline))


def get_sales_by_category(store: str = None):
    db       = get_db()
    day_cols = get_day_columns(30)

    pipeline = []
    if store and store in STORE_STATE_MAP:
        pipeline.append({"$match": {"state_id": STORE_STATE_MAP[store]}})

    pipeline += [
        {"$project": {
            "cat_id": 1,
            "total":  {"$add": [{"$ifNull": [f"${d}", 0]} for d in day_cols]}
        }},
        {"$group": {
            "_id":   "$cat_id",
            "total": {"$sum": "$total"}
        }},
        {"$sort": {"total": -1}}
    ]
    return list(db.sales.aggregate(pipeline))


def get_sales_by_store(store: str = None):
    db       = get_db()
    day_cols = get_day_columns(30)

    pipeline = []
    if store and store in STORE_STATE_MAP:
        pipeline.append({"$match": {"state_id": STORE_STATE_MAP[store]}})

    pipeline += [
        {"$project": {
            "store_id": 1,
            "total":    {"$add": [{"$ifNull": [f"${d}", 0]} for d in day_cols]}
        }},
        {"$group": {
            "_id":   "$store_id",
            "total": {"$sum": "$total"}
        }},
        {"$sort": {"total": -1}}
    ]
    return list(db.sales.aggregate(pipeline))