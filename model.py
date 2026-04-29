def model(data):
    
    import lightgbm as lgm
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from data_transformation import DataTransformer

    transformer = DataTransformer()

    # ✅ Split
    data = transformer.transform(data)
    train_data = data[data['day'] <= 1659]
    test_data = data[data['day'] > 1659]

    X_train = train_data.drop(columns=['sales'])
    y_train = train_data['sales']

    X_test = test_data.drop(columns=['sales'])
    y_test = test_data['sales']

    # ❌ DO NOT call transform again

    # ✅ Encoding only
    X_train = transformer.fit_encoder(X_train)
    X_test = transformer.transform_encoder(X_test)

    # ✅ Model (start small to avoid freeze)
    model = lgm.LGBMRegressor(
        objective='regression',
        n_estimators=100,
        learning_rate=0.05,
        num_leaves=64,
        max_depth=6
    )

    model.fit(X_train, y_train, categorical_feature=[
        'state_id',
        'store_id',
        'item_id',
        'event_name_1',
        'event_type_1',
        'event_name_2',
        'event_type_2',
        'weekday'
    ])

    pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, pred)
    mse = mean_squared_error(y_test, pred)

    return mae, mse