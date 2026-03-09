from prometheus_client import Counter

REQUEST_COUNTER = Counter(
    "healthcare_requests_total",
    "Total Healthcare API Requests"
)