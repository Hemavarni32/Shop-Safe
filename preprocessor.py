import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

FEATURE_ORDER = [
    'activeduration','domain_reg_len','domainlen','havedash','is@','isip',
    'isredirect','isvalid','longurl','nosofsubdomain','rank','ranking',
    'subdomain','tinyurl','urllen','valid'
]

def load_and_clean_data(filepaths):
    dfs = []
    for p in filepaths:
        try:
            df = pd.read_csv(p)
            df.columns = [c.strip().lower() for c in df.columns]
            dfs.append(df)
            print(f"✅ Loaded {p} -> {df.shape}")
        except Exception as e:
            print(f"⚠️ Could not load {p}: {e}")
    if not dfs:
        raise ValueError("No CSVs loaded.")
    df = pd.concat(dfs, axis=0, ignore_index=True)
    df = df.loc[:, ~df.columns.duplicated()]
    df = df.dropna(how='all')
    df.reset_index(drop=True, inplace=True)
    print(f"✅ Combined dataset shape: {df.shape}")
    return df

def preprocess_features(df, training=True):
    # Ensure lowercase
    df.columns = [c.strip().lower() for c in df.columns]
    # Add any missing expected columns with neutral default
    for col in FEATURE_ORDER:
        if col not in df.columns:
            df[col] = 0
    # Keep only expected columns
    X = df[FEATURE_ORDER].copy()
    # Convert numeric
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
    # Target (label)
    label_col = next((c for c in df.columns if c in ("label","target","is_phishing")), None)
    if label_col is None:
        raise ValueError("Label column not found in CSVs.")
    y = df[label_col].astype(int)
    # Fit scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    if training:
        with open("scaler.pkl","wb") as f:
            pickle.dump(scaler, f)
        with open("features.pkl","wb") as f:
            pickle.dump(FEATURE_ORDER, f)
        print("✅ Saved scaler.pkl and features.pkl")
    return X_scaled, y, FEATURE_ORDER
