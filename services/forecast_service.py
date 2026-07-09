import pickle
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config.db import get_db

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "lightgbm_model.pkl")

# الـ categories بالترتيب الصح اللي الـ model اتدرب عليها
PANDAS_CATEGORIES = [
    # item_id
    None,  # placeholder - هيتجاب من الـ model
]

CAT_COLS = [
    "item_id", "store_id", "dept_id", "cat_id", "state_id",
    "weekday",
    "event_name_1", "event_type_1",
    "event_name_2", "event_type_2",
]

FEATURE_COLS = [
    'item_id', 'store_id', 'dept_id', 'cat_id', 'state_id',
    'day', 'wm_yr_wk', 'weekday', 'wday', 'month', 'year',
    'event_name_1', 'event_type_1', 'event_name_2', 'event_type_2',
    'snap_CA', 'snap_TX', 'snap_WI', 'sell_price', 'week',
    'lag_1', 'lag_7', 'lag_28',
    'rolling_mean_7', 'rolling_mean_28',
    'store_lag_7', 'store_lag_28', 'store_rolling_mean_7', 'store_rolling_mean_28',
    'state_lag_28', 'state_rolling_mean_28'
]

_model   = None
_encoders = None



# آخر يوم فعلي اتدرب عليه الموديل - قيمة ثابتة مرتبطة بالـ pickle نفسه،
# مش بيانات الـ collection اللي ممكن يبقى فيها أعمدة d_ لأيام مستقبلية
# قيمتها صفر (placeholder) مش بيانات حقيقية.
TRAIN_LAST_DATE = "2015-12-12"


def get_last_available_date():
    """
    بيرجع آخر تاريخ فعلي اتدرب عليه الموديل.
    ده ثابت (hardcoded) عمدًا، مش مستنتج من وجود أعمدة d_ في sales
    collection، لأن الأعمدة دي بتمتد لأيام بعد آخر يوم تدريب فعلي
    بقيم صفرية وهمية (placeholder)، فأي استنتاج من مجرد وجود العمود
    كان بيرجع تاريخ غلط.
    """
    return TRAIN_LAST_DATE


def load_model():
    global _model
    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
    return _model



def get_historical_data(item_id: str, store_id: str, days: int = 60):
    """بيجيب الـ historical sales من MongoDB"""
    db = get_db()

    # جيب الـ sales doc كامل الأول (من غير تحديد أعمدة d)، عشان نعرف آخر
    # يوم فيه فعلًا بيانات مبيعات حقيقية للصنف/الفرع ده
    sales_doc = db.sales.find_one(
        {"item_id": item_id, "store_id": store_id}, {"_id": 0}
    )
    if not sales_doc:
        return None

    # كل أعمدة الـ d المتاحة فعليًا (يعني عندها بيانات train حقيقية)، مرتبة رقميًا
    available_d_cols = [k for k in sales_doc.keys() if k.startswith("d_")]
    if not available_d_cols:
        return None
    available_d_cols.sort(key=lambda x: int(x.split("_")[1]))

    # خد آخر N يوم فعلي من الـ train بس - مش من الـ calendar اللي ممكن يمتد
    # لتواريخ متأخرة مفيهاش بيانات مبيعات حقيقية أصلاً (فتترجم بصفر وهمي)
    d_cols = available_d_cols[-days:]

    cal_docs = list(
        db.calender.find({"d": {"$in": d_cols}}, {
            "d": 1, "date": 1, "wm_yr_wk": 1, "weekday": 1,
            "wday": 1, "month": 1, "year": 1,
            "event_name_1": 1, "event_type_1": 1,
            "event_name_2": 1, "event_type_2": 1,
            "snap_CA": 1, "snap_TX": 1, "snap_WI": 1, "_id": 0
        }).sort("date", 1)
    )

    # جيب الـ sell_price
    price_doc = db.prices.find_one(
        {"item_id": item_id, "store_id": store_id},
        {"sell_price": 1, "_id": 0},
        sort=[("wm_yr_wk", -1)]
    )
    sell_price = price_doc["sell_price"] if price_doc else 0.0

    rows = []
    for doc in cal_docs:
        d = doc["d"]
        rows.append({
            "item_id":      item_id,
            "store_id":     store_id,
            "dept_id":      sales_doc.get("dept_id", "None"),
            "cat_id":       sales_doc.get("cat_id", "None"),
            "state_id":     sales_doc.get("state_id", "None"),
            "date":         doc["date"] if isinstance(doc["date"], str) else doc["date"].strftime("%Y-%m-%d"),
            "wm_yr_wk":     doc.get("wm_yr_wk", 0),
            "weekday":      doc.get("weekday", "None"),
            "wday":         doc.get("wday", 0),
            "month":        doc.get("month", 0),
            "year":         doc.get("year", 0),
            "event_name_1": str(doc.get("event_name_1") or "None"),
            "event_type_1": str(doc.get("event_type_1") or "None"),
            "event_name_2": str(doc.get("event_name_2") or "None"),
            "event_type_2": str(doc.get("event_type_2") or "None"),
            "snap_CA":      doc.get("snap_CA", 0),
            "snap_TX":      doc.get("snap_TX", 0),
            "snap_WI":      doc.get("snap_WI", 0),
            "sell_price":   sell_price,
            "sales":        sales_doc.get(d, 0),
        })

    return pd.DataFrame(rows)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """بيحسب الـ lag وrolling features"""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["item_id", "store_id", "date"])
    df["day"]  = df["date"].dt.dayofyear
    df["week"] = df["date"].dt.isocalendar().week.astype(int)

    # Item lags
    grp = df.groupby(["item_id", "store_id"])["sales"]
    df["lag_1"]          = grp.shift(1)
    df["lag_7"]          = grp.shift(7)
    df["lag_28"]         = grp.shift(28)
    df["rolling_mean_7"] = grp.shift(1).rolling(7).mean()
    df["rolling_mean_28"]= grp.shift(1).rolling(28).mean()

    # Store lags
    store_daily = (
        df.groupby(["store_id", "day"])["sales"].sum()
        .reset_index().sort_values(["store_id", "day"])
    )
    sg = store_daily.groupby("store_id")["sales"]
    store_daily["store_lag_7"]          = sg.shift(7)
    store_daily["store_lag_28"]         = sg.shift(28)
    store_daily["store_rolling_mean_7"] = sg.shift(1).rolling(7).mean()
    store_daily["store_rolling_mean_28"]= sg.shift(1).rolling(28).mean()
    store_daily.fillna(0, inplace=True)

    df = df.merge(
        store_daily[["store_id", "day", "store_lag_7", "store_lag_28",
                     "store_rolling_mean_7", "store_rolling_mean_28"]],
        on=["store_id", "day"], how="left"
    )

    # State lags
    state_daily = (
        df.groupby(["state_id", "day"])["sales"].sum()
        .reset_index().sort_values(["state_id", "day"])
    )
    sg2 = state_daily.groupby("state_id")["sales"]
    state_daily["state_lag_28"]          = sg2.shift(28)
    state_daily["state_rolling_mean_28"] = sg2.shift(1).rolling(28).mean()
    state_daily.fillna(0, inplace=True)

    df = df.merge(
        state_daily[["state_id", "day", "state_lag_28", "state_rolling_mean_28"]],
        on=["state_id", "day"], how="left"
    )

    df[["lag_1","lag_7","lag_28","rolling_mean_7","rolling_mean_28"]] = \
        df[["lag_1","lag_7","lag_28","rolling_mean_7","rolling_mean_28"]].fillna(0)

    return df


def get_model_categories():
    """بيجيب الـ pandas_categorical من الـ model نفسه"""
    model = load_model()
    cats  = model._Booster.dump_model().get("pandas_categorical", [])
    # الترتيب بالظبط زي ما الـ model اتدرب عليه
    cat_col_order = [
        "item_id",      # Group 0 - 3049 items
        "store_id",     # Group 1 - 10 stores
        "dept_id",      # Group 2 - 7 depts
        "cat_id",       # Group 3 - 3 cats
        "state_id",     # Group 4 - 3 states
        "weekday",      # Group 5 - 7 days
        "event_name_1", # Group 6 - 31 events
        "event_type_1", # Group 7 - 5 types
        "event_name_2", # Group 8 - 3 events
        "event_type_2", # Group 9 - 3 types
    ]
    return {col: cats[i] for i, col in enumerate(cat_col_order) if i < len(cats)}


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """بيحول الـ categorical columns لـ pd.Categorical بنفس الـ categories اللي الـ model اتدرب عليها"""
    categories = get_model_categories()
    df = df.copy()

    for col, cats in categories.items():
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = pd.Categorical(df[col], categories=cats)

    return df


def run_forecast(item_id: str, store_id: str, horizon: int = 28):
    """
    بيعمل forecast للـ horizon يوم الجاية
    بيرجع list من {"date": "...", "forecast": float}
    """
    model = load_model()

    # جيب historical data (محتاج على الأقل 28 يوم للـ lags)
    df = get_historical_data(item_id, store_id, days=60)
    if df is None:
        return {"error": f"No data found for {item_id} / {store_id}"}

    df = build_features(df)
    df = df.sort_values("date").reset_index(drop=True)

    # خريطة اسم اليوم (weekday) -> رقم الـ wday المستخدم في الداتا، عشان نطابق نفس الترميز
    # لما نحسب weekday/wday ليوم مستقبلي
    weekday_map = df.drop_duplicates("weekday").set_index("weekday")["wday"].to_dict()

    df = encode_features(df)

    # آخر يوم في الداتا
    last_date = pd.to_datetime(df["date"].max())
    last_row  = df.iloc[-1].copy()

    # سلسلة المبيعات (تاريخي) اللي هنضيفلها كل تنبؤ جديد، وهي أساس حساب الـ lags والـ rolling
    # بشكل تراكمي صحيح بدل ما نرجع لقيم آخر يوم حقيقي في كل تكرار
    sales_history = df["sales"].tolist()

    predictions = []

    for i in range(1, horizon + 1):
        pred_date    = last_date + timedelta(days=i)
        weekday_name = pred_date.strftime("%A")

        # اعمل row جديد للـ prediction
        row = last_row.copy()
        row["date"]    = pred_date
        row["day"]     = pred_date.dayofyear
        row["week"]    = int(pred_date.isocalendar()[1])
        row["month"]   = pred_date.month
        row["year"]    = pred_date.year
        row["weekday"] = weekday_name
        row["wday"]    = weekday_map.get(weekday_name, last_row["wday"])

        # ملحوظة/قيود معروفة:
        # - مفيش بيانات calendar فعلية بعد آخر تاريخ متاح، فـ event_name/type وsnap_CA/TX/WI
        #   وsell_price بتفضل بآخر قيمة معروفة (نفس افتراض last_row) لحد ما يبقى فيه
        #   calendar حقيقي للمستقبل.
        # - store_lag/state_lag/rolling كمان بتفضل مجمدة على آخر قيمة معروفة، لأن حسابها
        #   الصح محتاج نعمل forecast لكل الأصناف التانية في نفس الـ store/state مع بعض،
        #   وده خارج نطاق الدالة دي (بتشتغل على صنف واحد بس).

        # الـ lags والـ rolling الصحيحة لنفس الصنف - بتتحسب من سلسلة المبيعات المتراكمة
        # (تاريخي + كل تنبؤ سابق)، مش من last_row الثابتة
        row["lag_1"]  = sales_history[-1]
        row["lag_7"]  = sales_history[-7]  if len(sales_history) >= 7  else 0
        row["lag_28"] = sales_history[-28] if len(sales_history) >= 28 else 0
        row["rolling_mean_7"]  = float(np.mean(sales_history[-7:]))
        row["rolling_mean_28"] = float(np.mean(sales_history[-28:]))

        X = pd.DataFrame([row])[FEATURE_COLS]
        for col, cats in get_model_categories().items():
            if col in X.columns:
                X[col] = pd.Categorical(X[col].astype(str), categories=cats)
        pred = float(model.predict(X)[0])
        pred = max(0, round(pred, 2))

        predictions.append({
            "date":     pred_date.strftime("%Y-%m-%d"),
            "forecast": pred
        })

        # ضيف التنبؤ للسلسلة عشان الأيام الجاية تحسب الـ lags/rolling بتاعتها صح
        sales_history.append(pred)

    return predictions