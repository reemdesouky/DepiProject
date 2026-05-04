def prepare_data(path):
    
    import pandas as pd

    # =========================
    # 1. LOAD DATA
    # =========================
    sales = pd.read_csv(f"{path}/sales_train_evaluation.csv")
    calendar = pd.read_csv(f"{path}/calendar.csv")
    prices = pd.read_csv(f"{path}/sell_prices.csv")

    # =========================
    # 2. MELT SALES (wide → long)
    # =========================
    id_vars = [
        "id", "item_id", "dept_id",
        "cat_id", "store_id", "state_id"
    ]

    sales_long = sales.melt(
        id_vars=id_vars,
        var_name="d",
        value_name="sales"
    )

    # =========================
    # 3. MERGE CALENDAR
    # =========================
    calendar = calendar[[
        "d", "date", "wm_yr_wk",
        "weekday",
        "event_name_1", "event_type_1",
        "event_name_2", "event_type_2",
        "snap_CA", "snap_TX", "snap_WI"
    ]]

    df = sales_long.merge(calendar, on="d", how="left")

    # =========================
    # 4. CREATE DAY COLUMN
    # =========================
    df["day"] = df["d"].str.replace("d_", "").astype(int)

    # =========================
    # 5. MERGE SELL PRICES
    # =========================
    prices = prices[[
        "store_id", "item_id", "wm_yr_wk", "sell_price"
    ]]

    df = df.merge(
        prices,
        on=["store_id", "item_id", "wm_yr_wk"],
        how="left"
    )

    # =========================
    # 6. SORT (IMPORTANT for lags)
    # =========================
    df = df.sort_values(["item_id", "store_id", "day"])

    # =========================
    # 7. OPTIONAL MEMORY REDUCTION
    # =========================
    df["sales"] = df["sales"].astype("int16")
    df["sell_price"] = df["sell_price"].astype("float32")

    # =========================
    # 8. DROP USELESS COLUMNS
    # =========================
    df.drop(columns=["d"], inplace=True)

    return df