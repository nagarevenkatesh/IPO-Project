from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os, joblib, datetime, json
from passlib.context import CryptContext
from jose import jwt, JWTError


SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-for-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="IPO Predictor ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USERS_DB = os.path.join(os.path.dirname(__file__), "..", "users_store.json")
PRED_HISTORY = os.path.join(os.path.dirname(__file__), "..", "pred_history.json")

def load_users():
    if os.path.exists(USERS_DB):
        with open(USERS_DB, "r") as f:
            return json.load(f)
    return {}

def save_users(u):
    with open(USERS_DB, "w") as f:
        json.dump(u, f, indent=2)

def load_history():
    if os.path.exists(PRED_HISTORY):
        with open(PRED_HISTORY, "r") as f:
            return json.load(f)
    return []

def save_history(h):
    with open(PRED_HISTORY, "w") as f:
        json.dump(h, f, indent=2)

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResp(BaseModel):
    access_token: str
    token_type: str

class PredictItem(BaseModel):
    ticker: str
    issue_price: float
    listing_date: str
    exchange: Optional[str] = ""
    sector: Optional[str] = ""

class PredictReq(BaseModel):
    items: List[PredictItem]

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire.isoformat()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

@app.post("/auth/register", status_code=201)
def register(u: UserRegister):
    users = load_users()
    if u.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    hashed = pwd_context.hash(u.password)
    users[u.username] = {"password": hashed, "created": datetime.datetime.utcnow().isoformat()}
    save_users(users)
    return {"ok": True}

@app.post("/auth/login", response_model=TokenResp)
def login(req: UserLogin):
    users = load_users()
    if req.username not in users or not pwd_context.verify(req.password, users[req.username]["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": req.username})
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    token = authorization.split(" ", 1)[1]
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return payload["sub"]

# Load model artifact once
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "model_artifact.pkl")
ARTIFACT = None
MODEL = None

def load_artifact():
    global ARTIFACT, MODEL
    if ARTIFACT is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError("Model artifact not found; run train_model.py to create models/model_artifact.pkl")
        ARTIFACT = joblib.load(MODEL_PATH)
        MODEL = ARTIFACT.get("model")
    return ARTIFACT

@app.post("/predict")
def predict(req: PredictReq, user=Depends(get_current_user)):
    art = load_artifact()
    model = art.get("model")
    cols = art.get("feature_columns", [])
    category_maps = art.get("category_maps", {})
    import pandas as pd
    results = []
    history = load_history()
    for it in req.items:
        df = pd.DataFrame([{
            "issue_price": it.issue_price,
            "exchange": it.exchange or "",
            "sector": it.sector or "",
            "listing_date": pd.to_datetime(it.listing_date)
        }])
        X = pd.DataFrame()
        X["issue_price"] = df["issue_price"]
        def enc(name, series):
            if name in category_maps:
                cats = category_maps[name]
                return pd.Categorical(series, categories=cats).codes
            return series.astype("category").cat.codes
        X["exchange_code"] = enc("exchange", df["exchange"])
        X["sector_code"] = enc("sector", df["sector"])
        X["listing_month"] = df["listing_date"].dt.month
        X["listing_day"] = df["listing_date"].dt.day
        X = X.reindex(columns=cols, fill_value=0)
        try:
            pred = float(MODEL.predict(X)[0])
        except Exception:
            pred = 0.0
        res = {"ticker": it.ticker, "predicted_firstday_pct": pred, "inputs": X.iloc[0].to_dict()}
        results.append(res)
        history.append({"user": user, "time": datetime.datetime.utcnow().isoformat(), "result": res})
    save_history(history)
    return {"results": results}

@app.post("/explain")
def explain(req: PredictReq, user=Depends(get_current_user)):
    art = load_artifact()
    model = art.get("model")
    cols = art.get("feature_columns", [])
    category_maps = art.get("category_maps", {})
    import pandas as pd
    try:
        import shap
        shap_available = True
    except Exception:
        shap_available = False

    explanations = []
    for it in req.items:
        df = pd.DataFrame([{
            "issue_price": it.issue_price,
            "exchange": it.exchange or "",
            "sector": it.sector or "",
            "listing_date": pd.to_datetime(it.listing_date)
        }])
        X = pd.DataFrame()
        X["issue_price"] = df["issue_price"]
        def enc(name, series):
            if name in category_maps:
                cats = category_maps[name]
                return pd.Categorical(series, categories=cats).codes
            return series.astype("category").cat.codes
        X["exchange_code"] = enc("exchange", df["exchange"])
        X["sector_code"] = enc("sector", df["sector"])
        X["listing_month"] = df["listing_date"].dt.month
        X["listing_day"] = df["listing_date"].dt.day
        X = X.reindex(columns=cols, fill_value=0)
        if shap_available:
            try:
                explainer = shap.TreeExplainer(model)
                sv = explainer.shap_values(X)
                raw = sv[0] if isinstance(sv, list) else sv
                vals = raw[0].tolist() if len(raw) > 0 else []
                explanations.append(dict(zip(cols, [float(v) for v in vals])))
                continue
            except Exception:
                pass
        fi = getattr(model, 'feature_importances_', None)
        if fi is not None:
            explanations.append(dict(zip(cols, [float(x) for x in fi])))
        else:
            explanations.append({c: 0.0 for c in cols})
    return {"explanations": explanations}

@app.get("/history")
def history(user=Depends(get_current_user)):
    return {"history": load_history()}

@app.get("/health")
def health():
    return {"ok": True}
