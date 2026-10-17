# ShopSafe: Intelligent Phishing Website Detection

**ShopSafe** is a machine-learning-powered Google Chrome extension designed to assess website URLs and identify potential phishing threats in real time. It combines domain-aware feature extraction, a LightGBM classification model, and a Flask REST API to classify websites into three risk levels: **Legitimate, Caution, and Phishing**.

The extension automatically scans the currently active website when opened and displays the predicted trust score through an animated circular gauge with color-coded visual feedback.

## Features

- **Real-time URL analysis:** Automatically scans the active browser tab when the extension opens.
- **Machine learning classification:** Uses a trained LightGBM model to estimate phishing probability.
- **Three-level risk assessment:** Categorizes websites as Legitimate, Caution, or Phishing.
- **Trust score calculation:** Converts the predicted phishing probability into a percentage score.
- **Interactive user interface:** Displays an animated circular trust-score gauge.
- **Dynamic visual feedback:** Uses green for legitimate websites, yellow for caution, red for phishing, and a pulsing blue glow during analysis.
- **Domain-aware feature extraction:** Extracts URL-related characteristics for model inference.
- **Calibration monitoring:** Maintains calibration statistics and provides a dashboard for monitoring them.
- **Modular architecture:** Separates the Chrome extension, backend API, feature extraction, and trained model artifacts.

## Technology Stack

| Component | Technology |
|---|---|
| Browser extension | HTML, CSS, JavaScript |
| Browser integration | Chrome Extensions API |
| Backend | Python, Flask |
| Machine learning | LightGBM |
| Data preprocessing | NumPy, scikit-learn |
| Model serialization | Python Pickle |
| Calibration storage | JSON |
| User interface | SVG, CSS animations, JavaScript |

## System Architecture

```text
┌──────────────────────────────┐
│      Google Chrome           │
│                              │
│  Active Website URL          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       popup.js               │
│                              │
│  Automatic URL Detection     │
│  API Request                 │
│  Score Animation             │
└──────────────┬───────────────┘
               │ HTTP GET
               ▼
┌──────────────────────────────┐
│       Flask API              │
│                              │
│  URL Validation              │
│  Feature Extraction          │
│  Feature Preprocessing       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       LightGBM Model         │
│                              │
│  Phishing Probability        │
│  Trust Score                 │
│  Risk Classification         │
└──────────────┬───────────────┘
               │ JSON Response
               ▼
┌──────────────────────────────┐
│      ShopSafe Popup          │
│                              │
│  Circular Trust Gauge        │
│  Risk Label                  │
│  Dynamic Colors              │
└──────────────────────────────┘
```

## Machine Learning Algorithm

### LightGBM Classifier

ShopSafe uses **LightGBM (Light Gradient Boosting Machine)**, a gradient-boosting framework based on decision trees.

LightGBM constructs trees sequentially. Each new tree contributes to improving the model's predictions by learning from the current ensemble's errors, according to the training objective.

Key characteristics include:

- Efficient training using histogram-based feature discretization.
- Leaf-wise tree growth, which can improve predictive performance when appropriately regularized.
- Ability to model nonlinear relationships and interactions between URL features.
- Probability predictions through `predict_proba()`.
- Support for feature-importance analysis.

### Why LightGBM Instead of Random Forest?

Random Forest is a strong alternative, but it uses a different ensemble strategy.

| Criterion | Random Forest | LightGBM |
|---|---|---|
| Ensemble strategy | Bagging | Gradient boosting |
| Tree construction | Trees trained independently | Trees added sequentially |
| Main learning objective | Reduce variance through averaging | Improve predictions through boosting |
| Training efficiency | Depends on dataset and tree configuration | Histogram-based optimizations can make training efficient |
| Feature interactions | Learns nonlinear relationships | Learns nonlinear relationships |
| Explainability | Feature importance available | Feature importance and SHAP explanations available |
| Project suitability | Valid alternative or baseline | Selected for this project's tabular classification pipeline |

**Selection rationale:** LightGBM offers an efficient, flexible approach to tabular classification and supports fast prediction through a backend API. However, it is not universally more accurate than Random Forest. The best algorithm should be established through evaluation on the same held-out dataset.

## How ShopSafe Works

### Step 1: Capture the Current Website

When the user opens the ShopSafe popup, `popup.js` uses the Chrome Extensions API to obtain the active tab's URL.

The URL is displayed in the input field, and the extension initiates a scan automatically.

### Step 2: Send the URL to the Backend

The extension sends an HTTP GET request to the Flask API:

```text
http://127.0.0.1:5000/api?url=<encoded_url>
```

The URL is encoded before being included in the request.

The backend must be running locally for this request to succeed.

### Step 3: Extract URL Features

The `FeatureExtractor` class processes the supplied URL and generates the features expected by the model.

These features form the numerical input vector used for prediction. Their exact definitions depend on the implementation in `featureExtractor.py` and must remain consistent with the features used during training.

### Step 4: Preprocess the Features

The backend arranges the extracted values in the order specified by `features.pkl` and applies the saved scaler:

```python
X = np.array(
    [features[name] for name in feature_names]
).reshape(1, -1)

X_scaled = scaler.transform(X)
```

Using the same preprocessing procedure as training is essential for consistent predictions.

### Step 5: Predict Phishing Probability

The trained model generates class probabilities:

```python
probs = clf.predict_proba(X_scaled)[0]
```

The backend selects a probability using the model's class ordering. For correct phishing detection, the selected class index must correspond to the actual phishing label in `clf.classes_`.

The resulting probability is interpreted as the estimated phishing probability.

### Step 6: Calculate the Trust Score

ShopSafe converts the estimated phishing probability into a trust score:

\[
\text{Trust Score}=(1-P_{\text{phishing}})\times100
\]

For example, if the model estimates a phishing probability of 0.20:

\[
(1-0.20)\times100=80
\]

The resulting trust score is 80%.

**Important:** The trust score is derived from the model's probability output. It is not a guarantee that a website is safe.

### Step 7: Classify the Website

The current API uses the following thresholds:

| Trust score | Classification | Interpretation |
|---|---|---|
| TS > 65 | Legitimate | Lower estimated risk |
| 50 ≤ TS ≤ 65 | Caution | Moderate estimated risk; review advised |
| TS < 50 | Phishing | Higher estimated risk |

These are application-defined decision thresholds, not universal security standards.

### Step 8: Update the Interface

The API returns a JSON response containing the URL, extracted features, phishing probability, classification, and trust score.

The popup then updates its interface:

- The circular gauge animates progressively to the predicted trust score.
- The classification label displays the result.
- The gauge and result text adopt the corresponding risk color.
- A subtle blue pulsing glow indicates that scanning is in progress.
- After a successful scan, the background changes to a light shade corresponding to the classification.

The interface is designed to make the result easy to understand without requiring users to interpret raw model probabilities.

## Installation and Setup

### Prerequisites

- Python 3.10 or a compatible version for the installed dependencies.
- Google Chrome.
- The trained model and preprocessing artifacts.
- The project source files.
- A virtual environment is recommended.

### 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ShopSafe
```

Replace the placeholder with your actual repository URL.

### 2. Create a Virtual Environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

If `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

Otherwise, install the packages required by your implementation, for example:

```bash
pip install flask numpy scikit-learn lightgbm
```

Use compatible package versions for the versions used to train and serialize the model.

### 4. Verify the Required Files

Ensure that the following files exist in the expected working directory:

```text
api.py
featureExtractor.py
lightgbm_model.pkl
scaler.pkl
features.pkl
```

The backend also needs permission to create or update `calibration.json`.

### 5. Start the Flask Backend

Run:

```bash
python api.py
```

The current API configuration uses port `5000`.

Wait until Flask reports that the development server is running before testing the extension.

### 6. Test the API

Open this URL in your browser:

```text
http://127.0.0.1:5000/api?url=https%3A%2F%2Fexample.com
```

A successful response should contain fields such as:

```json
{
  "URL": "https://example.com",
  "Phishing_Probability": 0.2,
  "Result": "Legitimate",
  "Trust_Score": 80.0
}
```

This is an illustrative response showing the expected structure, not a guaranteed prediction for `example.com`.

### 7. Load the Chrome Extension

1. Open `chrome://extensions/`.
2. Enable **Developer mode**.
3. Select **Load unpacked**.
4. Choose the directory containing `manifest.json`.
5. Open a normal website in a Chrome tab.
6. Click the ShopSafe extension icon.

The extension should populate the current URL and automatically begin scanning.

The extension manifest must declare the permissions required by the actual implementation, including access to the active tab and the local backend origin. Review the Chrome extension manifest documentation if you need to adjust these permissions.

## Project Objective

ShopSafe aims to make phishing risk assessment more accessible by combining machine learning with an intuitive browser interface. By presenting a trust score and a clear risk category, the project helps users recognize potentially dangerous websites before interacting with them.

### ShopSafe | Machine Learning for a Safer Browsing Experience
