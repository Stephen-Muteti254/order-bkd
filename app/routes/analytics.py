from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from dateutil.parser import isoparse

from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.models import db

analytics_bp = Blueprint(
    "analytics",
    __name__,
    url_prefix="/api/v1/analytics"
)

# -------------------------
# Timezone helpers
# -------------------------

EAT = timezone(timedelta(hours=3))

def eat_now():
    return datetime.now(EAT)

def eat_to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=EAT)
    return dt.astimezone(timezone.utc)

def utc_to_eat_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(EAT).isoformat()

# -------------------------
# Period helpers (EAT-based)
# -------------------------

def resolve_period(period: str):
    now_eat = eat_now()

    if period == "week":
        start = now_eat - timedelta(days=7)
        prev_start = start - timedelta(days=7)
        prev_end = start
        label = "This Week"

    elif period == "month":
        start = now_eat.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        prev_start = (start - relativedelta(months=1)).replace(day=1)
        prev_end = start

        label = "This Month"

    elif period == "quarter":
        month = ((now_eat.month - 1) // 3) * 3 + 1
        start = now_eat.replace(month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

        prev_start = start - relativedelta(months=3)
        prev_end = start

        label = "This Quarter"

    elif period == "year":
        start = now_eat.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        prev_start = start.replace(year=start.year - 1)
        prev_end = start

        label = "This Year"

    else:
        raise ValueError("Invalid period")

    return {
        "current": (eat_to_utc(start), eat_to_utc(now_eat)),
        "previous": (eat_to_utc(prev_start), eat_to_utc(prev_end)),
        "label": label,
        "eat_current": (start, now_eat),
        "eat_previous": (prev_start, prev_end),
    }


def resolve_trend_period(period: str, start_date=None, end_date=None):
    now_eat = eat_now()

    mapping = {
        "1week": 7,
        "1month": 30,
        "3months": 90,
        "6months": 180
    }

    if period == "custom":
        start = isoparse(start_date)
        end = isoparse(end_date)

        if start.tzinfo is None:
            start = start.replace(tzinfo=EAT)
        if end.tzinfo is None:
            end = end.replace(tzinfo=EAT)

        return eat_to_utc(start), eat_to_utc(end), start, end

    days = mapping.get(period)
    if not days:
        raise ValueError("Invalid period")

    start = now_eat - timedelta(days=days)
    return eat_to_utc(start), eat_to_utc(now_eat), start, now_eat

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
            "startDate": ranges["eat_current"][0].isoformat(),
            "endDate": ranges["eat_current"][1].isoformat(),
        },
        "previousPeriod": {
            "label": f"Last {ranges['label'].split()[-1]}",
            "revenue": prev_rev,
            "orders": prev_orders,
            "startDate": ranges["eat_previous"][0].isoformat(),
            "endDate": ranges["eat_previous"][1].isoformat(),
        },
        "percentageChange": percentage(cur_rev, prev_rev),
        "ordersPercentageChange": percentage(cur_orders, prev_orders),
    })

@analytics_bp.get("/revenue/trend")
def revenue_trend():
    period = request.args.get("period", "1month")

    start_utc, end_utc, start_eat, end_eat = resolve_trend_period(
        period,
        request.args.get("startDate"),
        request.args.get("endDate")
    )

    rows = db.session.execute(
        text("""
            SELECT
              DATE("createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'Africa/Nairobi') AS date,
              SUM("totalCost") AS revenue,
              COUNT(*) AS orders
            FROM orders
            WHERE "createdAt" >= :start
              AND "createdAt" < :end
            GROUP BY 1
            ORDER BY 1
        """),
        {"start": start_utc, "end": end_utc}
    ).fetchall()

    data = [{
        "date": datetime.combine(r.date, datetime.min.time(), tzinfo=EAT).isoformat(),
        "revenue": float(r.revenue),
        "orders": r.orders,
    } for r in rows]

    total = sum(d["revenue"] for d in data)
    days = max((end_eat - start_eat).days, 1)

    return jsonify({
        "data": data,
        "total": round(total, 2),
        "averagePerDay": round(total / days, 2),
        "period": period,
    })

@analytics_bp.get("/orders/trend")
def orders_trend():
    period = request.args.get("period", "1month")

    start_utc, end_utc, start_eat, end_eat = resolve_trend_period(
        period,
        request.args.get("startDate"),
        request.args.get("endDate")
    )

    rows = db.session.execute(
        text("""
            SELECT
              DATE("createdAt" AT TIME ZONE 'UTC' AT TIME ZONE 'Africa/Nairobi') AS date,
              COUNT(*) AS count
            FROM orders
            WHERE "createdAt" >= :start
              AND "createdAt" < :end
            GROUP BY 1
            ORDER BY 1
        """),
        {"start": start_utc, "end": end_utc}
    ).fetchall()

    data = [{
        "date": datetime.combine(r.date, datetime.min.time(), tzinfo=EAT).isoformat(),
        "count": r.count,
    } for r in rows]

    total = sum(d["count"] for d in data)
    days = max((end_eat - start_eat).days, 1)

    return jsonify({
        "data": data,
        "total": total,
        "averagePerDay": round(total / days, 2),
        "period": period,
    })

@analytics_bp.get("/clients/earnings")
def client_rankings():
    period = request.args.get("period", "1month")
    start_utc, end_utc, start_eat, end_eat = resolve_trend_period(
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

    params = {"start": start_utc, "end": end_utc}

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
            "averageOrderValue": round(float(r.revenue) / r.orders, 2) if r.orders else 0,
        } for r in rows],
        "total": len(rows),
        "period": {
            "startDate": start_eat.isoformat(),
            "endDate": end_eat.isoformat(),
            "label": human_label(period),
        },
    })
