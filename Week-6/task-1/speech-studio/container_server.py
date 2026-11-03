"""Local classroom demo: one process, threaded HTTP and Flask-Sock handling."""
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)
