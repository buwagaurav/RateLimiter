from flask import Flask, request, jsonify
import redis
import time

app = Flask(__name__)
redis_conn = redis.StrictRedis(host='localhost', port=6379, db=0)

class RateLimiter:
    def __init__(self, max_requests, interval):
        self.max_requests = max_requests
        self.interval = interval

    def allow_request(self, user_ip):
        current_minute = self._get_current_minute()
        key = f"rate_limit:{user_ip}:{current_minute}"
        current_requests = redis_conn.hget(key, 'requests')
        if current_requests is None:
            current_requests = 0
        else:
            current_requests = int(current_requests)

        remaining_requests = self.max_requests - current_requests
        if remaining_requests > 0:
            redis_conn.hincrby(key, 'requests', 1)
            redis_conn.expire(key, self.interval)
            redis_conn.hset(key, 'remaining', remaining_requests - 1)
            return True
        else:
            return False

    def _get_current_minute(self):
        return int(time.time() // 60)

limiter = RateLimiter(max_requests=10, interval=60)  # Allowing 10 requests per minute per user IP

@app.route('/api', methods=['GET'])
def api():
    user_ip = request.remote_addr
    if limiter.allow_request(user_ip):
        return jsonify({'status': 'success', 'message': 'Request allowed'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 429

if __name__ == '__main__':
    app.run(debug=True)
