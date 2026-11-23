"""Small task-tracker API used to demonstrate containerisation."""
import os
import platform
import socket
import time

from flask import Flask, jsonify, request

from app.db import connect, init_db

START_TIME = time.time()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["APP_ENV"] = os.environ.get("APP_ENV", "development")
    init_db()

    @app.get("/")
    def index():
        return (
            "<h1>Dockerized Web Application</h1>"
            f"<p>Environment: {app.config['APP_ENV']}</p>"
            "<p>Try <code>/api/tasks</code> or <code>/health</code>.</p>"
        )

    @app.get("/health")
    def health():
        try:
            with connect() as conn:
                conn.execute("SELECT 1")
            db_ok = True
        except Exception:  # noqa: BLE001 - report any DB failure as unhealthy
            db_ok = False
        status = 200 if db_ok else 503
        return jsonify(
            status="ok" if db_ok else "degraded",
            database=db_ok,
            hostname=socket.gethostname(),
            python=platform.python_version(),
            uptime_seconds=round(time.time() - START_TIME, 1),
            environment=app.config["APP_ENV"],
        ), status

    @app.get("/api/tasks")
    def list_tasks():
        with connect() as conn:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
        return jsonify([_row(r) for r in rows])

    @app.post("/api/tasks")
    def create_task():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify(error="title is required"), 400
        with connect() as conn:
            cur = conn.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(_row(row)), 201

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id: int):
        data = request.get_json(silent=True) or {}
        with connect() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                return jsonify(error="not found"), 404
            title = str(data.get("title", row["title"])).strip() or row["title"]
            done = int(bool(data.get("done", row["done"])))
            conn.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (title, done, task_id))
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return jsonify(_row(row))

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id: int):
        with connect() as conn:
            cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cur.rowcount == 0:
            return jsonify(error="not found"), 404
        return "", 204

    return app


def _row(row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"]), "created_at": row["created_at"]}


app = create_app() if os.environ.get("CREATE_APP_ON_IMPORT", "1") == "1" else None
