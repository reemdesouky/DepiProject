from flask import Blueprint, jsonify, request, session
from services.dashboard_service import (
    get_summary,
    get_sales_trend,
    get_top_products,
    get_sales_by_category,
    get_sales_by_store,
)

dashboard_bp = Blueprint("dashboard", __name__)


def get_store():
    """بياخد الـ store من الـ session أو من الـ query param"""
    return request.args.get("store") or session.get("store")


@dashboard_bp.route("/summary")
def summary():
    return jsonify(get_summary(get_store()))


@dashboard_bp.route("/trend")
def trend():
    period = request.args.get("period", "30d")
    return jsonify(get_sales_trend(period, get_store()))


@dashboard_bp.route("/top-products")
def top_products():
    limit = int(request.args.get("limit", 10))
    data  = get_top_products(limit, get_store())
    for d in data:
        d["_id"] = str(d["_id"]) if "_id" in d else None
    return jsonify(data)


@dashboard_bp.route("/by-category")
def by_category():
    data = get_sales_by_category(get_store())
    return jsonify([{"category": d["_id"], "total": d["total"]} for d in data])


@dashboard_bp.route("/by-store")
def by_store():
    data = get_sales_by_store(get_store())
    return jsonify([{"store": d["_id"], "total": d["total"]} for d in data])