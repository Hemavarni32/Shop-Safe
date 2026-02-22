import pickle
import warnings
warnings.filterwarnings("ignore")

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, brier_score_loss
from lightgbm import LGBMClassifier

from preprocessor import load_and_clean_data, preprocess_features

FILEPATHS = ["Main_dataset.csv", "phishing_feature_engg.csv"]
RANDOM_STATE = 42
TEST_SIZE = 0.2

def main():
    print("🔁 Loading CSVs...")
    df = load_and_clean_data(FILEPATHS)
    print("🔁 Preprocessing...")
    X_scaled, y, feature_names = preprocess_features(df, training=True)
    print(f"🧩 Feature count: {len(feature_names)}")

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y if len(np.unique(y))>1 else None
    )
    print(f"🔁 Train shape: {X_train.shape}, Test shape: {X_test.shape}")

    print("⚙️ Training LightGBM base model...")
    base = LGBMClassifier(
        n_estimators=500,
        max_depth=12,
        random_state=RANDOM_STATE,
        class_weight='balanced'
    )
    base.fit(X_train, y_train)
    pred = base.predict(X_test)
    print("Base accuracy:", accuracy_score(y_test, pred))
    print(classification_report(y_test, pred))

    print("⚙️ Calibrating probabilities (Platt / sigmoid)...")
    calibrated = CalibratedClassifierCV(base, method="sigmoid", cv=5)
    calibrated.fit(X_train, y_train)

    pred_cal = calibrated.predict(X_test)
    proba_cal = calibrated.predict_proba(X_test)[:, 1]  # class 1 = phishing
    print("Calibrated accuracy:", accuracy_score(y_test, pred_cal))
    print("Brier score (phish prob):", brier_score_loss(y_test, proba_cal))
    print(classification_report(y_test, pred_cal))

    # Save artifacts
    with open("lightgbm_model.pkl", "wb") as f:
        pickle.dump(calibrated, f)
    print("✅ Saved lightgbm_model.pkl (calibrated classifier)")
    # scaler and features already saved in preprocess_features when training=True

if __name__ == "__main__":
    main()
