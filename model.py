import joblib
def model(data):
    
    import lightgbm as lgm
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from data_transformations import DataTransformer

    transformer = DataTransformer()

    # transform ONCE only here
    data = transformer.transform(data)

    train_data = data[data['day'] <= 1659]
    test_data = data[data['day'] > 1659]

    X_train = train_data.drop(columns=['sales'])
    y_train = train_data['sales']
    X_train = transformer.fit_encoder(X_train)
    X_test = test_data.drop(columns=['sales'])
    y_test = test_data['sales']
    X_test = transformer.transform_encoder(X_test)
    #  FIX categorical feature typo
    cat_cols = transformer.cat_cols

    model = lgm.LGBMRegressor(
        objective='regression',
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=64,
        max_depth=6
    )

    model.fit(
        X_train,
        y_train,
        categorical_feature=cat_cols
    )

    joblib.dump(model, "lightgbm_model.pkl")
    joblib.dump(transformer, "transformer.pkl")
    print("Successfully saved 'lightgbm_model.pkl' and 'transformer.pkl'!")

    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    print(f"Evaluation Metrics -> MAE: {mae:.4f}, MSE: {mse:.4f}")

    return predictions
