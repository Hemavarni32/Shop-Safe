# import pickle
# from flask import Flask, request, jsonify, render_template_string
# from featureExtractor import FeatureExtractor
# import numpy as np
# import json
# import os

# app = Flask(__name__)

# # -----------------------------
# # Load model and preprocessing
# # -----------------------------
# with open("lightgbm_model.pkl", "rb") as f:
#     clf = pickle.load(f)
# with open("scaler.pkl", "rb") as f:
#     scaler = pickle.load(f)
# with open("features.pkl", "rb") as f:
#     feature_names = pickle.load(f)

# print("Model loaded successfully.")
# print("Model classes:", clf.classes_)

# CALIBRATION_FILE = "calibration.json"
# ALPHA = 0.2
# RESET_THRESHOLD = 0.15


# def default_calibration():
#     return {
#         "legit_mean": 0.15,
#         "caution_mean": 0.65,
#         "phish_mean": 0.85,
#         "count": 0
#     }


# def load_calibration():
#     if os.path.exists(CALIBRATION_FILE):
#         with open(CALIBRATION_FILE, "r") as f:
#             data = json.load(f)
#     else:
#         data = default_calibration()
#     return data


# def save_calibration(data):
#     with open(CALIBRATION_FILE, "w") as f:
#         json.dump(data, f, indent=4)


# def update_calibration(data, phishing_prob, label):
#     if label == "Legitimate":
#         key = "legit_mean"
#     elif label == "Caution":
#         key = "caution_mean"
#     else:
#         key = "phish_mean"

#     old_value = data[key]
#     new_value = ALPHA * phishing_prob + (1 - ALPHA) * old_value
#     data[key] = round(new_value, 5)
#     data["count"] += 1

#     save_calibration(data)


# def validate_calibration(data):
#     legit, caution, phish = data["legit_mean"], data["caution_mean"], data["phish_mean"]
#     if not (0 <= legit < caution < phish <= 1):
#         print("[AUTO-RESET] Invalid calibration detected, restoring defaults.")
#         data = default_calibration()
#         save_calibration(data)
#         return data
#     if (caution - legit) < RESET_THRESHOLD or (phish - caution) < RESET_THRESHOLD:
#         print("[AUTO-RESET] Calibration drift detected, rebalancing.")
#         data = default_calibration()
#         save_calibration(data)
#     return data

# @app.route("/api", methods=["GET"])
# def detect_phishing():
#     url = request.args.get("url", "").strip()
#     if not url:
#         return jsonify({"error": "Missing 'url' parameter"}), 400

#     try:
#         fe = FeatureExtractor()
#         features = fe.extract_features(url)
#         X = np.array([features[f] for f in feature_names]).reshape(1, -1)
#         X_scaled = scaler.transform(X)

#         probs = clf.predict_proba(X_scaled)[0]
#         phishing_idx = int(np.argmax(clf.classes_))
#         phishing_prob = probs[phishing_idx]

#         cal = validate_calibration(load_calibration())

#         lower_thresh = (cal["legit_mean"] + cal["caution_mean"]) / 2
#         upper_thresh = (cal["caution_mean"] + cal["phish_mean"]) / 2

#         if phishing_prob < lower_thresh:
#             result = "Legitimate"
#         elif phishing_prob < upper_thresh:
#             result = "Caution"
#         else:
#             result = "Phishing"

#         update_calibration(cal, phishing_prob, result)
#         trust_score = round((1 - phishing_prob) * 100, 2)

#         print(f"\n[DEBUG] URL: {url}")
#         print(f"Raw Probabilities: {probs}")
#         print(f"Phishing Probability: {phishing_prob:.4f}")
#         print(f"→ Thresholds: Low={lower_thresh:.3f}, High={upper_thresh:.3f}")
#         print(f"→ Result: {result}")
#         print(f"→ Trust Score: {trust_score}")
#         print(f"→ Calibration: {cal}")

#         return jsonify({
#             "URL": url,
#             "Extracted_Features": features,
#             "Phishing_Probability": float(phishing_prob),
#             "Result": result,
#             "Trust_Score": trust_score,
#             "Thresholds": {
#                 "Lower": round(lower_thresh, 3),
#                 "Upper": round(upper_thresh, 3)
#             },
#             "Calibration": cal
#         })

#     except Exception as e:
#         import traceback
#         print("❌ BACKEND ERROR:", str(e))
#         traceback.print_exc()
#         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

# # ---------------------------------------------
# # 📊 NEW: Calibration Visualization Dashboard
# # ---------------------------------------------
# @app.route("/calibration")
# def show_calibration():
#     cal = load_calibration()

#     html = """
#     <!DOCTYPE html>
#     <html lang="en">
#     <head>
#         <meta charset="UTF-8" />
#         <title>Calibration Dashboard</title>
#         <style>
#             body { font-family: 'Segoe UI', sans-serif; background: #f4f6f8; color: #222; padding: 30px; }
#             h1 { color: #0078ff; }
#             .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 3px 8px rgba(0,0,0,0.1); width: 400px; margin-bottom: 20px; }
#             .bar { height: 20px; border-radius: 5px; margin-top: 8px; }
#             .legit { background: #00b35a; width: {{legit*100}}%; }
#             .caution { background: #ffc107; width: {{caution*100}}%; }
#             .phish { background: #dc3545; width: {{phish*100}}%; }
#         </style>
#     </head>
#     <body>
#         <h1>Calibration Monitor</h1>
#         <div class="card">
#             <h3>Current Means</h3>
#             <p>Legitimate Mean: {{legit}}<div class="bar legit"></div></p>
#             <p>Caution Mean: {{caution}}<div class="bar caution"></div></p>
#             <p>Phishing Mean: {{phish}}<div class="bar phish"></div></p>
#             <p><b>Entries Processed:</b> {{count}}</p>
#         </div>
#         <p style="font-size: 13px; color: #555;">Auto-updates dynamically as new URLs are analyzed.</p>
#     </body>
#     </html>
#     """

#     return render_template_string(
#         html,
#         legit=cal["legit_mean"],
#         caution=cal["caution_mean"],
#         phish=cal["phish_mean"],
#         count=cal["count"]
#     )


# if __name__ == "__main__":
#     app.run(debug=True)

# import pickle
# import warnings
# from flask import Flask, request, jsonify, render_template_string
# from featureExtractor import FeatureExtractor
# import numpy as np
# import json
# import os

# # Suppress sklearn feature name warning
# warnings.filterwarnings("ignore", category=UserWarning)

# app = Flask(__name__)

# # -----------------------------
# # Load model and preprocessing
# # -----------------------------
# with open("lightgbm_model.pkl", "rb") as f:
#     clf = pickle.load(f)
# with open("scaler.pkl", "rb") as f:
#     scaler = pickle.load(f)
# with open("features.pkl", "rb") as f:
#     feature_names = pickle.load(f)

# print("✅ Model loaded successfully.")
# print("Model classes:", clf.classes_)

# CALIBRATION_FILE = "calibration.json"
# ALPHA = 0.2
# RESET_THRESHOLD = 0.15


# def default_calibration():
#     return {"legit_mean": 0.15, "caution_mean": 0.65, "phish_mean": 0.85, "count": 0}


# def load_calibration():
#     if os.path.exists(CALIBRATION_FILE):
#         with open(CALIBRATION_FILE, "r") as f:
#             data = json.load(f)
#     else:
#         data = default_calibration()
#     return data


# def save_calibration(data):
#     with open(CALIBRATION_FILE, "w") as f:
#         json.dump(data, f, indent=4)


# def update_calibration(data, phishing_prob, label):
#     if label == "Safe":
#         key = "legit_mean"
#     elif label == "Caution":
#         key = "caution_mean"
#     else:
#         key = "phish_mean"

#     old_value = data[key]
#     new_value = ALPHA * phishing_prob + (1 - ALPHA) * old_value
#     data[key] = round(new_value, 5)
#     data["count"] += 1
#     save_calibration(data)


# def validate_calibration(data):
#     legit, caution, phish = data["legit_mean"], data["caution_mean"], data["phish_mean"]
#     if not (0 <= legit < caution < phish <= 1):
#         print("[AUTO-RESET] Invalid calibration detected, restoring defaults.")
#         data = default_calibration()
#         save_calibration(data)
#         return data
#     if (caution - legit) < RESET_THRESHOLD or (phish - caution) < RESET_THRESHOLD:
#         print("[AUTO-RESET] Calibration drift detected, rebalancing.")
#         data = default_calibration()
#         save_calibration(data)
#     return data


# @app.route("/api", methods=["GET"])
# def detect_phishing():
#     url = request.args.get("url", "").strip()
#     if not url:
#         return jsonify({"error": "Missing 'url' parameter"}), 400

#     try:
#         fe = FeatureExtractor()
#         features = fe.extract_features(url)
#         X = np.array([features[f] for f in feature_names]).reshape(1, -1)
#         X_scaled = scaler.transform(X)

#         probs = clf.predict_proba(X_scaled)[0]
#         phishing_idx = int(np.argmax(clf.classes_))
#         phishing_prob = probs[phishing_idx]

#         cal = validate_calibration(load_calibration())

#         trust_score = round((1 - phishing_prob) * 100, 2)
#         if trust_score > 65:
#             result = "Safe"
#         elif trust_score >= 50:
#             result = "Caution"
#         else:
#             result = "Unsafe"

#         update_calibration(cal, phishing_prob, result)

#         print(f"\n[DEBUG] URL: {url}")
#         print(f"Phishing Probability: {phishing_prob:.4f}")
#         print(f"→ Result: {result}, Trust Score: {trust_score}")
#         print(f"→ Calibration: {cal}")

#         return jsonify({
#             "URL": url,
#             "Extracted_Features": features,
#             "Phishing_Probability": float(phishing_prob),
#             "Result": result,
#             "Trust_Score": trust_score,
#             "Calibration": cal
#         })

#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


# @app.route("/calibration")
# def show_calibration():
#     cal = load_calibration()
#     html = """
#     <!DOCTYPE html>
#     <html lang="en">
#     <head>
#         <meta charset="UTF-8" />
#         <title>Calibration Dashboard</title>
#         <style>
#             body { font-family: 'Segoe UI', sans-serif; background: #f4f6f8; color: #222; padding: 30px; }
#             h1 { color: #0078ff; }
#             .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 3px 8px rgba(0,0,0,0.1); width: 400px; margin-bottom: 20px; }
#             .bar { height: 20px; border-radius: 5px; margin-top: 8px; }
#             .legit { background: #00b35a; width: {{legit*100}}%; }
#             .caution { background: #ffc107; width: {{caution*100}}%; }
#             .phish { background: #dc3545; width: {{phish*100}}%; }
#         </style>
#     </head>
#     <body>
#         <h1>Calibration Monitor</h1>
#         <div class="card">
#             <h3>Current Means</h3>
#             <p>Safe Mean: {{legit}}<div class="bar legit"></div></p>
#             <p>Caution Mean: {{caution}}<div class="bar caution"></div></p>
#             <p>Unsafe Mean: {{phish}}<div class="bar phish"></div></p>
#             <p><b>Entries Processed:</b> {{count}}</p>
#         </div>
#         <p style="font-size: 13px; color: #555;">Auto-updates dynamically as new URLs are analyzed.</p>
#     </body>
#     </html>
#     """
#     return render_template_string(
#         html,
#         legit=cal["legit_mean"],
#         caution=cal["caution_mean"],
#         phish=cal["phish_mean"],
#         count=cal["count"]
#     )


# if __name__ == "__main__":
#     app.run(debug=True, port=5000)

import pickle
import warnings
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from featureExtractor import FeatureExtractor
import numpy as np
import json
import os
import traceback

# Suppress sklearn warnings
warnings.filterwarnings("ignore", category=UserWarning)

app = Flask(__name__)
CORS(app)  # ✅ Allow Chrome Extension access

# -----------------------------
# Load model and preprocessing
# -----------------------------
with open("lightgbm_model.pkl", "rb") as f:
    clf = pickle.load(f)
with open("scaler.pkl", "rb") as f:
    scaler = pickle.load(f)
with open("features.pkl", "rb") as f:
    feature_names = pickle.load(f)

print("✅ Model loaded successfully.")
print("Model classes:", clf.classes_)

CALIBRATION_FILE = "calibration.json"
ALPHA = 0.2
RESET_THRESHOLD = 0.15


def default_calibration():
    return {"legit_mean": 0.15, "caution_mean": 0.65, "phish_mean": 0.85, "count": 0}


def load_calibration():
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE, "r") as f:
            data = json.load(f)
    else:
        data = default_calibration()
    return data


def save_calibration(data):
    with open(CALIBRATION_FILE, "w") as f:
        json.dump(data, f, indent=4)


def update_calibration(data, phishing_prob, label):
    if label == "Safe":
        key = "legit_mean"
    elif label == "Caution":
        key = "caution_mean"
    else:
        key = "phish_mean"

    old_value = data[key]
    new_value = ALPHA * phishing_prob + (1 - ALPHA) * old_value
    data[key] = round(new_value, 5)
    data["count"] += 1
    save_calibration(data)


def validate_calibration(data):
    legit, caution, phish = data["legit_mean"], data["caution_mean"], data["phish_mean"]
    if not (0 <= legit < caution < phish <= 1):
        print("[AUTO-RESET] Invalid calibration detected, restoring defaults.")
        data = default_calibration()
        save_calibration(data)
        return data
    if (caution - legit) < RESET_THRESHOLD or (phish - caution) < RESET_THRESHOLD:
        print("[AUTO-RESET] Calibration drift detected, rebalancing.")
        data = default_calibration()
        save_calibration(data)
    return data


@app.route("/api", methods=["GET"])
def detect_phishing():
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        fe = FeatureExtractor()
        features = fe.extract_features(url)
        X = np.array([features[f] for f in feature_names]).reshape(1, -1)
        X_scaled = scaler.transform(X)

        probs = clf.predict_proba(X_scaled)[0]
        phishing_idx = int(np.argmax(clf.classes_))
        phishing_prob = probs[phishing_idx]

        cal = validate_calibration(load_calibration())

        trust_score = round((1 - phishing_prob) * 100, 2)
        if trust_score > 65:
            result = "Safe"
        elif trust_score >= 50:
            result = "Caution"
        else:
            result = "Unsafe"

        update_calibration(cal, phishing_prob, result)

        print(f"\n[DEBUG] URL: {url}")
        print(f"Phishing Probability: {phishing_prob:.4f}")
        print(f"→ Result: {result}, Trust Score: {trust_score}")
        print(f"→ Calibration: {cal}")

        response = jsonify({
            "URL": url,
            "Extracted_Features": features,
            "Phishing_Probability": float(phishing_prob),
            "Result": result,
            "Trust_Score": trust_score,
            "Calibration": cal
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    except Exception as e:
        print("❌ ERROR:", traceback.format_exc())
        response = jsonify({
            "error": "Internal Server Error",
            "details": str(e)
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500


@app.route("/calibration")
def show_calibration():
    cal = load_calibration()
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Calibration Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f4f6f8; color: #222; padding: 30px; }
            h1 { color: #0078ff; }
            .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 3px 8px rgba(0,0,0,0.1); width: 400px; margin-bottom: 20px; }
            .bar { height: 20px; border-radius: 5px; margin-top: 8px; }
            .legit { background: #00b35a; width: {{legit*100}}%; }
            .caution { background: #ffc107; width: {{caution*100}}%; }
            .phish { background: #dc3545; width: {{phish*100}}%; }
        </style>
    </head>
    <body>
        <h1>Calibration Monitor</h1>
        <div class="card">
            <h3>Current Means</h3>
            <p>Safe Mean: {{legit}}<div class="bar legit"></div></p>
            <p>Caution Mean: {{caution}}<div class="bar caution"></div></p>
            <p>Unsafe Mean: {{phish}}<div class="bar phish"></div></p>
            <p><b>Entries Processed:</b> {{count}}</p>
        </div>
        <p style="font-size: 13px; color: #555;">Auto-updates dynamically as new URLs are analyzed.</p>
    </body>
    </html>
    """
    return render_template_string(
        html,
        legit=cal["legit_mean"],
        caution=cal["caution_mean"],
        phish=cal["phish_mean"],
        count=cal["count"]
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)