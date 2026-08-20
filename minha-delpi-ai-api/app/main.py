from app.create_app import create_app

app = create_app()


if __name__ == "__main__":
    # threaded: SSE + heartbeat OCR (worker) não bloqueiam outras requests em dev.
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
