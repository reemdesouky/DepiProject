from sqlalchemy import Date


class DataTransformer:
    def __init__(self):
        from sklearn.preprocessing import LabelEncoder
        self.encoders = {}
        self.cat_cols = [
            "state_id", "store_id", "item_id",
            "cat_id", "dept_id",
            "event_name_1", "event_type_1",
            "event_name_2", "event_type_2",
            "weekday"
        ]

    def transform(self, data):
        import pandas as pd

        data = data.copy()

        # Clean
        data.drop(columns=["Unnamed: 0"], inplace=True, errors="ignore")

        # Date
        data["date"] = pd.to_datetime(data["date"])
        data["day"] = data["date"].dt.dayofyear

        data = data.sort_values(["item_id", "store_id", "date"])

        # Time feature
        data["week"] = data["date"].dt.isocalendar().week.astype(int)

        # ======================
        # ITEM FEATURES
        # ======================
        grp = data.groupby(["item_id", "store_id"])["sales"]

        data["lag_1"] = grp.shift(1)
        data["lag_7"] = grp.shift(7)
        data["lag_28"] = grp.shift(28)

        data["rolling_mean_7"] = grp.shift(1).rolling(7).mean()
        data["rolling_mean_28"] = grp.shift(1).rolling(28).mean()

        # ======================
        # STORE FEATURES
        # ======================


        store_daily = (
            data.groupby(['store_id', 'day'], observed=False)["sales"]
            .sum()
            .reset_index()
            .sort_values(['store_id','day'])
        )

        store_grp = store_daily.groupby('store_id', observed=False)["sales"]

        store_daily['store_lag_7'] = store_grp.shift(7)
        store_daily['store_lag_28'] = store_grp.shift(28)

        store_daily["store_rolling_mean_7"] = store_grp.shift(1).rolling(7).mean()
        store_daily["store_rolling_mean_28"] = store_grp.shift(1).rolling(28).mean()

        # ✅ Fill only numeric
        num_cols = store_daily.select_dtypes(include=['number']).columns
        store_daily[num_cols] = store_daily[num_cols].fillna(0)





        data = data.merge(
            store_daily[['store_id','day','store_lag_7','store_lag_28',
                         'store_rolling_mean_7','store_rolling_mean_28']],
            on=['store_id','day'],
            how='left'
        )

        # ======================
        # STATE FEATURES
        # ======================
        state = (
            data.groupby(['state_id', 'day'], observed=False)["sales"]
            .sum()
            .reset_index()
            .sort_values(['state_id','day'])
        )

        state_grp = state.groupby('state_id', observed=False)["sales"]

        state['state_lag_28'] = state_grp.shift(28)
        state["state_rolling_mean_28"] = state_grp.shift(1).rolling(28).mean()

        # ✅ SAFE FILL
        num_cols = state.select_dtypes(include=['number']).columns
        state[num_cols] = state[num_cols].fillna(0)

        data = data.merge(
            state[['state_id','day','state_lag_28','state_rolling_mean_28']],
            on=['state_id','day'],
            how='left'
        )

        # Fill NaNs
        lag_cols = [
            "lag_1","lag_7","lag_28",
            "rolling_mean_7","rolling_mean_28"
        ]
        data[lag_cols] = data[lag_cols].fillna(0)

        # ======================
        # CATEGORICAL
        # ======================
        data[self.cat_cols] = data[self.cat_cols].fillna("None")

        for col in self.cat_cols:
            data[col] = data[col].astype("category")

        # data = data.drop(columns=["date"])

        return data

    # ======================
    # ENCODING
    # ======================
    def fit_encoder(self, data):
        from sklearn.preprocessing import LabelEncoder

        for col in self.cat_cols:
            le = LabelEncoder()
            data[col] = le.fit_transform(data[col].astype(str))
            self.encoders[col] = le

        return data

    def transform_encoder(self, data):
        for col in self.cat_cols:
            le = self.encoders[col]
            data[col] = le.transform(data[col].astype(str))

        return data