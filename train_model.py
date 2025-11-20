import numpy as np
import pandas as pd
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OrdinalEncoder

OUT = "models"
os.makedirs(OUT, exist_ok=True)
MODEL_PATH = os.path.join(OUT, "model_artifact.pkl")

n = 5000
rng = np.random.default_rng(42)
issue_price = rng.uniform(10, 1000, size=n)
exchange = rng.choice(["NSE", "BSE", "OTH"], n)
sector = rng.choice(["TECH", "FIN", "HEALTH", "CONS"], n)

listing_dates = pd.to_datetime("2023-01-01") + pd.to_timedelta(
    rng.integers(0, 365, n), unit="D"
)
listing_month = listing_dates.month
listing_day = listing_dates.day


y = (issue_price % 10) * 0.7 + (listing_month - 6) * 0.2 + rng.normal(0, 2, n)

X = pd.DataFrame(
    {
        "issue_price": issue_price,
        "exchange": exchange,
        "sector": sector,
        "listing_month": listing_month,
        "listing_day": listing_day,
    }
)

cat_cols = ["exchange", "sector"]
num_cols = ["issue_price", "listing_month", "listing_day"]

enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
enc.fit(X[cat_cols])

X_model = np.hstack([X[num_cols], enc.transform(X[cat_cols])])

feature_columns = [
    "issue_price",
    "listing_month",
    "listing_day",
    "exchange_code",
    "sector_code",
]

model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_model, y)

artifact = {
    "model": model,
    "feature_columns": feature_columns,
    "category_maps": {
        "exchange": list(enc.categories_[0]),
        "sector": list(enc.categories_[1]),
    },
}

joblib.dump(artifact, MODEL_PATH)
print("Model saved to", MODEL_PATH)
