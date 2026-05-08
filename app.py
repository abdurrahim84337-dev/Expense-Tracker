from flask import Flask, render_template, request, jsonify
import json
import os
from datetime import datetime, date
from collections import defaultdict

app = Flask(__name__)
DATA_FILE = "expenses.json"

CATEGORIES = [
    {"name": "Food & Dining", "icon": "🍽️", "color": "#FF6B6B"},
    {"name": "Transportation", "icon": "🚗", "color": "#4ECDC4"},
    {"name": "Shopping", "icon": "🛍️", "color": "#45B7D1"},
    {"name": "Entertainment", "icon": "🎬", "color": "#96CEB4"},
    {"name": "Healthcare", "icon": "🏥", "color": "#FFEAA7"},
    {"name": "Utilities", "icon": "💡", "color": "#DDA0DD"},
    {"name": "Education", "icon": "📚", "color": "#98D8C8"},
    {"name": "Travel", "icon": "✈️", "color": "#F7DC6F"},
    {"name": "Personal Care", "icon": "💆", "color": "#BB8FCE"},
    {"name": "Other", "icon": "📦", "color": "#AEB6BF"},
]

CURRENCIES = [
    {"code": "USD", "symbol": "$", "label": "US Dollar"},
    {"code": "EUR", "symbol": "€", "label": "Euro"},
    {"code": "GBP", "symbol": "£", "label": "British Pound"},
    {"code": "INR", "symbol": "₹", "label": "Indian Rupee"},
    {"code": "PKR", "symbol": "₨", "label": "Pakistani Rupee"},
    {"code": "JPY", "symbol": "¥", "label": "Japanese Yen"},
    {"code": "CAD", "symbol": "C$", "label": "Canadian Dollar"},
    {"code": "AUD", "symbol": "A$", "label": "Australian Dollar"},
]

def load_expenses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_expenses(expenses):
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2)

@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES, currencies=CURRENCIES)

@app.route("/api/expenses", methods=["GET"])
def get_expenses():
    expenses = load_expenses()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    category = request.args.get("category")
    search = request.args.get("search", "").lower()

    filtered = expenses
    if start_date:
        filtered = [e for e in filtered if e["date"] >= start_date]
    if end_date:
        filtered = [e for e in filtered if e["date"] <= end_date]
    if category and category != "All":
        filtered = [e for e in filtered if e["category"] == category]
    if search:
        filtered = [e for e in filtered if search in e["description"].lower() or search in e["category"].lower()]

    filtered.sort(key=lambda x: x["date"], reverse=True)
    return jsonify(filtered)

@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.json
    expenses = load_expenses()
    expense = {
        "id": int(datetime.now().timestamp() * 1000),
        "description": data["description"],
        "amount": float(data["amount"]),
        "currency": data.get("currency", "USD"),
        "category": data["category"],
        "date": data["date"],
        "note": data.get("note", ""),
    }
    expenses.append(expense)
    save_expenses(expenses)
    return jsonify(expense), 201

@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def update_expense(expense_id):
    data = request.json
    expenses = load_expenses()
    for i, e in enumerate(expenses):
        if e["id"] == expense_id:
            expenses[i].update({
                "description": data["description"],
                "amount": float(data["amount"]),
                "currency": data.get("currency", "USD"),
                "category": data["category"],
                "date": data["date"],
                "note": data.get("note", ""),
            })
            save_expenses(expenses)
            return jsonify(expenses[i])
    return jsonify({"error": "Not found"}), 404

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expenses = load_expenses()
    expenses = [e for e in expenses if e["id"] != expense_id]
    save_expenses(expenses)
    return jsonify({"success": True})

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    expenses = load_expenses()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    filtered = expenses
    if start_date:
        filtered = [e for e in filtered if e["date"] >= start_date]
    if end_date:
        filtered = [e for e in filtered if e["date"] <= end_date]

    total = sum(e["amount"] for e in filtered)
    by_category = defaultdict(float)
    by_date = defaultdict(float)
    by_month = defaultdict(float)

    for e in filtered:
        by_category[e["category"]] += e["amount"]
        by_date[e["date"]] += e["amount"]
        month_key = e["date"][:7]
        by_month[month_key] += e["amount"]

    cat_colors = {c["name"]: c["color"] for c in CATEGORIES}
    pie_data = [
        {"category": cat, "amount": round(amt, 2), "color": cat_colors.get(cat, "#AEB6BF"), "pct": round(amt / total * 100, 1) if total else 0}
        for cat, amt in sorted(by_category.items(), key=lambda x: -x[1])
    ]

    sorted_dates = sorted(by_date.items())
    sorted_months = sorted(by_month.items())

    return jsonify({
        "total": round(total, 2),
        "count": len(filtered),
        "avg": round(total / len(filtered), 2) if filtered else 0,
        "pie_data": pie_data,
        "daily_trend": [{"date": d, "amount": round(a, 2)} for d, a in sorted_dates[-30:]],
        "monthly_trend": [{"month": m, "amount": round(a, 2)} for m, a in sorted_months[-12:]],
        "top_category": max(by_category, key=by_category.get) if by_category else "—",
    })

@app.route("/api/categories", methods=["GET"])
def get_categories():
    return jsonify(CATEGORIES)

if __name__ == "__main__":
    app.run(debug=True, port=5000)