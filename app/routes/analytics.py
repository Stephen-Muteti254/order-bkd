from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.models import db

analytics_bp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/api/v1/analytics"
)

# -------------------------
# Helpers
# -------------------------

def resolve_period(period: str):
    now = datetime.now(timezone.utc)

    if period == "week":
        start = now - timedelta(days=7)
        prev_start = start - timedelta(days=7)
        prev_end = start
        label = "This Week"

    elif period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start - relativedelta(months=1)
        prev_end = start
        label = "This Month"

    elif period == "quarter":
        month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start - relativedelta(months=3)
        prev_end = start
        label = "This Quarter"

    elif period == "year":
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_start = start.replace(year=start.year - 1)
        prev_end = start
        label = "This Year"

    else:
        raise ValueError("Invalid period")

    return {
        "current": (start, now),
        "previous": (prev_start, prev_end),
        "label": label
    }


from dateutil.parser import isoparse

def resolve_trend_period(period: str, start_date=None, end_date=None):
    now = datetime.now(timezone.utc)

    mapping = {
        "1week": 7,
        "1month": 30,
        "3months": 90,
        "6months": 180
    }

    if period == "custom":
        if not start_date or not end_date:
            raise ValueError("Custom period requires startDate and endDate")

        start = isoparse(start_date)
        end = isoparse(end_date)

        if start >= end:
            raise ValueError("startDate must be before endDate")

        return start, end

    if period not in mapping:
        raise ValueError("Invalid period")

    return now - timedelta(days=mapping[period]), now



def human_label(period: str):
    return {
        "1week": "Last 7 Days",
        "1month": "Last 30 Days",
        "3months": "Last 3 Months",
        "6months": "Last 6 Months"
    }.get(period, "Last 30 Days")


def percentage(current, previous):
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)

# -------------------------
# Endpoints
# -------------------------

@analytics_bp.get("/earnings/comparison")
def earnings_comparison():
    period = request.args.get("period", "month")
    ranges = resolve_period(period)

    def aggregate(start, end):
        row = db.session.execute(
            text("""
                SELECT
                  COALESCE(SUM("totalCost"), 0) AS revenue,
                  COUNT(*) AS orders
                FROM orders
                WHERE "createdAt" >= :start
                  AND "createdAt" < :end
            """),
            {"start": start, "end": end}
        ).one()

        return float(row.revenue), row.orders

    cur_rev, cur_orders = aggregate(*ranges["current"])
    prev_rev, prev_orders = aggregate(*ranges["previous"])

    return jsonify({
        "currentPeriod": {
            "label": ranges["label"],
            "revenue": cur_rev,
            "orders": cur_orders,
            "startDate": ranges["current"][0].isoformat(),
            "endDate": ranges["current"][1].isoformat()
        },
        "previousPeriod": {
            "label": f"Last {ranges['label'].split()[-1]}",
            "revenue": prev_rev,
            "orders": prev_orders,
            "startDate": ranges["previous"][0].isoformat(),
            "endDate": ranges["previous"][1].isoformat()
        },
        "percentageChange": percentage(cur_rev, prev_rev),
        "ordersPercentageChange": percentage(cur_orders, prev_orders)
    })


@analytics_bp.get("/revenue/trend")
def revenue_trend():
    period = request.args.get("period", "1month")

    start, end = resolve_trend_period(
        period,
        request.args.get("startDate"),
        request.args.get("endDate")
    )

    rows = db.session.execute(
        text("""
            SELECT
              DATE("createdAt") AS date,
              SUM("totalCost") AS revenue,
              COUNT(*) AS orders
            FROM orders
            WHERE "createdAt" >= :start
              AND "createdAt" < :end
            GROUP BY DATE("createdAt")
            ORDER BY date
        """),
        {"start": start, "end": end}
    ).fetchall()

    data = [{
        "date": r.date.isoformat(),
        "revenue": float(r.revenue),
        "orders": r.orders
    } for r in rows]

    total = sum(d["revenue"] for d in data)
    days = max((end - start).days, 1)

    return jsonify({
        "data": data,
        "total": round(total, 2),
        "averagePerDay": round(total / days, 2),
        "period": period
    })


@analytics_bp.get("/orders/trend")
def orders_trend():
    period = request.args.get("period", "1month")

    start, end = resolve_trend_period(
        period,
        request.args.get("startDate"),
        request.args.get("endDate")
    )

    rows = db.session.execute(
        text("""
            SELECT
              DATE("createdAt") AS date,
              COUNT(*) AS count
            FROM orders
            WHERE "createdAt" >= :start
              AND "createdAt" < :end
            GROUP BY DATE("createdAt")
            ORDER BY date
        """),
        {"start": start, "end": end}
    ).fetchall()

    total = sum(r.count for r in rows)
    days = max((end - start).days, 1)

    return jsonify({
        "data": [{"date": r.date.isoformat(), "count": r.count} for r in rows],
        "total": total,
        "averagePerDay": round(total / days, 2),
        "period": period
    })


@analytics_bp.get("/clients/earnings")
def client_rankings():
    period = request.args.get("period", "1month")

    start, end = resolve_trend_period(
        period,
        request.args.get("startDate"),
        request.args.get("endDate")
    )
    client_id = request.args.get("clientId")
    limit = int(request.args.get("limit", 10))

    sql = """
        SELECT
          c.id AS client_id,
          c."clientName",
          c.institution,
          SUM(o."totalCost") AS revenue,
          COUNT(o.id) AS orders
        FROM orders o
        JOIN clients c ON c.id = o."clientId"
        WHERE o."createdAt" >= :start
          AND o."createdAt" < :end
    """

    params = {"start": start, "end": end}

    if client_id:
        sql += " AND c.id = :client_id"
        params["client_id"] = client_id

    sql += """
        GROUP BY c.id, c."clientName", c.institution
        ORDER BY revenue DESC
        LIMIT :limit
    """

    params["limit"] = limit

    rows = db.session.execute(text(sql), params).fetchall()

    return jsonify({
        "data": [{
            "clientId": r.client_id,
            "clientName": r.clientName,
            "institution": r.institution,
            "totalRevenue": float(r.revenue),
            "orderCount": r.orders,
            "averageOrderValue": round(float(r.revenue) / r.orders, 2) if r.orders else 0
        } for r in rows],
        "total": len(rows),
        "period": {
            "startDate": start.isoformat(),
            "endDate": end.isoformat(),
            "label": human_label(period)
        }
    })
