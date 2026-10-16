"""
InsightReport API Server
Flask REST API 版本 - 可部署为微服务，按调用量计费。
"""
from flask import Flask, request, jsonify, send_file
import pandas as pd
import numpy as np
import json
import io
import base64
import datetime
import os
import uuid
from pathlib import Path

app = Flask(__name__)

# Simple API key validation (in production, use proper auth)
API_KEYS = {"test_key": {"plan": "free", "usage": 0, "limit": 100}}

def require_api_key():
    key = request.headers.get("X-API-Key")
    if not key or key not in API_KEYS:
        return False
    API_KEYS[key]["usage"] += 1
    return True

@app.route("/")
def index():
    return jsonify({
        "service": "InsightReport API",
        "version": "1.0",
        "endpoints": {
            "POST /analyze": "Upload file and get analysis",
            "GET /report/<id>": "Get report by ID",
            "GET /pricing": "Pricing info",
        }
    })

@app.route("/pricing")
def pricing():
    return jsonify({
        "free": {"price": 0, "max_rows": 5000, "max_cols": 20},
        "pro": {"price": 99, "max_rows": 100000, "max_cols": 200, "unit": "¥/月"},
        "enterprise": {"price": 499, "max_rows": "unlimited", "max_cols": "unlimited", "unit": "¥/月"},
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    """Upload a CSV/Excel file and get analysis results."""
    if not require_api_key():
        return jsonify({"error": "Invalid or missing API key"}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        ext = Path(file.filename).suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(file)
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file)
        elif ext == ".json":
            df = pd.read_json(file)
        else:
            return jsonify({"error": f"Unsupported format: {ext}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to read file: {str(e)}"}), 400

    # Generate analysis
    result = analyze_dataframe(df)
    return jsonify(result)

def analyze_dataframe(df: pd.DataFrame) -> dict:
    """Core analysis function - returns structured analysis."""
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Basic stats
    overview = {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicated_rows": int(df.duplicated().sum()),
        "numeric_columns": len(num_cols),
        "categorical_columns": len(cat_cols),
    }

    # Column details
    columns = []
    for c in df.columns:
        col_info = {
            "name": c,
            "dtype": str(df[c].dtype),
            "non_null": int(df[c].count()),
            "null_count": int(df[c].isna().sum()),
            "null_pct": round(float(df[c].isna().mean() * 100), 2),
            "unique_values": int(df[c].nunique()),
        }
        if c in num_cols:
            col_info.update({
                "min": float(df[c].min()) if df[c].count() > 0 else None,
                "max": float(df[c].max()) if df[c].count() > 0 else None,
                "mean": float(df[c].mean()) if df[c].count() > 0 else None,
                "std": float(df[c].std()) if df[c].count() > 0 else None,
                "skewness": float(df[c].skew()) if df[c].count() > 0 else None,
            })
        columns.append(col_info)

    # Correlations
    correlations = []
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                v = corr.iloc[i, j]
                if abs(v) > 0.5:
                    correlations.append({
                        "col1": num_cols[i],
                        "col2": num_cols[j],
                        "correlation": round(float(v), 4),
                        "strength": "strong" if abs(v) > 0.7 else "moderate",
                        "direction": "positive" if v > 0 else "negative",
                    })

    # Insights
    insights = []
    if correlations:
        insights.append({
            "type": "correlation",
            "message": f"Found {len(correlations)} significant correlations",
            "details": [f"{c['col1']} ↔ {c['col2']}: {c['correlation']}" for c in correlations[:5]],
        })

    # Skewness
    for col in num_cols[:5]:
        skew = df[col].skew()
        if abs(skew) > 1:
            insights.append({
                "type": "skewness",
                "column": col,
                "message": f"'{col}' is skewed ({skew:.2f})",
                "direction": "right" if skew > 0 else "left",
            })

    # Outliers
    outlier_count = 0
    for col in num_cols:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        outliers = df[(df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)]
        outlier_count += len(outliers)

    if outlier_count > 0:
        insights.append({
            "type": "outliers",
            "message": f"Detected {outlier_count} potential outliers",
        })

    # Quality score
    completeness = 1 - df.isna().sum().sum() / (df.shape[0] * df.shape[1])
    quality_score = int(completeness * 100)

    return {
        "report_id": str(uuid.uuid4())[:8],
        "generated_at": datetime.datetime.now().isoformat(),
        "overview": overview,
        "columns": columns,
        "correlations": correlations,
        "insights": insights,
        "quality_score": quality_score,
        "recommendations": generate_recommendations(df, num_cols, cat_cols),
    }

def generate_recommendations(df, num_cols, cat_cols):
    recs = []
    if df.isna().any().any():
        recs.append("Handle missing values in columns: " +
                    ", ".join(df.columns[df.isna().sum() > 0].tolist()[:5]))
    if len(num_cols) >= 2:
        corr = df[num_cols].corr()
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                if abs(corr.iloc[i, j]) > 0.85:
                    recs.append(f"Consider dimensionality reduction - '{num_cols[i]}' and '{num_cols[j]}' are highly correlated")
                    break
            if any("highly correlated" in r for r in recs):
                break
    if df.shape[1] > 10:
        recs.append("Dataset has many features - consider PCA or feature selection")
    return recs

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"InsightReport API running on http://localhost:{port}")
    print(f"Test with: curl -X POST -F 'file=@data.csv' -H 'X-API-Key: test_key' http://localhost:{port}/analyze")
    app.run(host="0.0.0.0", port=port, debug=True)
