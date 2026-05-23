from flask import Blueprint, jsonify, request
from config.db import get_db

products_bp = Blueprint("products", __name__)


@products_bp.route("/")
def get_products():
    """
    GET /api/products?search=toy&page=1&limit=20
   
    """
    db      = get_db()
    search  = request.args.get("search", "")
    page    = int(request.args.get("page", 1))
    limit   = int(request.args.get("limit", 20))

    query = {}
    if search:
        query["product_name"] = {"$regex": search, "$options": "i"}

    skip  = (page - 1) * limit
    docs  = list(db.products.find(query, {"_id": 0}).skip(skip).limit(limit))
    total = db.products.count_documents(query)

    return jsonify({
        "data":  docs,
        "total": total,
        "page":  page,
        "pages": (total + limit - 1) // limit,
    })


@products_bp.route("/<item_id>")
def get_product(item_id):
    """
    GET /api/products/HOBBIES_1_003
   
    """
    db      = get_db()
    product = db.products.find_one({"item_id": item_id}, {"_id": 0})

    if not product:
        return jsonify({"error": "Product not found"}), 404

    latest_price = db.prices.find_one(
        {"item_id": item_id},
        {"sell_price": 1, "wm_yr_wk": 1, "_id": 0},
        sort=[("wm_yr_wk", -1)]
    )
    if latest_price:
        product["sell_price"]  = latest_price["sell_price"]
        product["price_week"]  = latest_price["wm_yr_wk"]

    return jsonify(product)


@products_bp.route("/<item_id>/price-history")
def price_history(item_id):
    """
    GET /api/products/HOBBIES_1_003/price-history?store_id=CA_1
   
    """
    db       = get_db()
    store_id = request.args.get("store_id")

    query = {"item_id": item_id}
    if store_id:
        query["store_id"] = store_id

    prices = list(
        db.prices
          .find(query, {"_id": 0, "wm_yr_wk": 1, "sell_price": 1, "store_id": 1})
          .sort("wm_yr_wk", 1)
    )
    return jsonify(prices)
