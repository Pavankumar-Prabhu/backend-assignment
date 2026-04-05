from __future__ import annotations


def render_docs_html() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Finance API Docs</title>
    <style>
      :root {
        --bg: #f5f7fb;
        --panel: #ffffff;
        --text: #172033;
        --muted: #5f6b80;
        --accent: #0f766e;
        --border: #dbe2ef;
        --code-bg: #0f172a;
        --code-text: #e2e8f0;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: "Segoe UI", Arial, sans-serif;
        background: linear-gradient(180deg, #eef7f5 0%, var(--bg) 40%);
        color: var(--text);
      }
      .wrap {
        width: min(1100px, calc(100vw - 32px));
        margin: 0 auto;
        padding: 40px 0 80px;
      }
      .hero, .card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 28px;
        box-shadow: 0 24px 80px rgba(15, 23, 42, 0.08);
      }
      h1, h2 { margin: 0 0 12px; }
      p, li { line-height: 1.6; color: var(--muted); }
      .grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 16px;
        margin-top: 24px;
      }
      code, pre {
        font-family: "Consolas", "SFMono-Regular", monospace;
      }
      pre {
        background: var(--code-bg);
        color: var(--code-text);
        padding: 18px;
        border-radius: 14px;
        overflow-x: auto;
      }
      .endpoint {
        display: flex;
        gap: 12px;
        align-items: center;
        margin-bottom: 10px;
      }
      .method {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
      }
      .get { background: #d1fae5; color: #065f46; }
      .post { background: #dbeafe; color: #1d4ed8; }
      .patch { background: #fef3c7; color: #b45309; }
      .delete { background: #fee2e2; color: #b91c1c; }
      ul { margin-top: 0; padding-left: 20px; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <section class="hero">
        <h1>Finance Dashboard Backend API</h1>
        <p>
          Token-authenticated finance records API with role-based access control and dashboard summaries.
        </p>
        <div class="grid">
          <div class="card">
            <h2>Default Accounts</h2>
            <ul>
              <li>admin@finance.local / Admin123!</li>
              <li>analyst@finance.local / Analyst123!</li>
              <li>viewer@finance.local / Viewer123!</li>
            </ul>
          </div>
          <div class="card">
            <h2>Roles</h2>
            <ul>
              <li>Viewer: dashboard-only access</li>
              <li>Analyst: read records and dashboard</li>
              <li>Admin: full user and record management</li>
            </ul>
          </div>
          <div class="card">
            <h2>Docs</h2>
            <ul>
              <li><a href="/openapi.json">OpenAPI JSON</a></li>
              <li><a href="/health">Health Check</a></li>
            </ul>
          </div>
        </div>
      </section>

      <section class="grid">
        <div class="card">
          <h2>Auth</h2>
          <div class="endpoint"><span class="method post">POST</span><code>/api/v1/auth/login</code></div>
          <div class="endpoint"><span class="method post">POST</span><code>/api/v1/auth/logout</code></div>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/me</code></div>
        </div>
        <div class="card">
          <h2>Users</h2>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/users</code></div>
          <div class="endpoint"><span class="method post">POST</span><code>/api/v1/users</code></div>
          <div class="endpoint"><span class="method patch">PATCH</span><code>/api/v1/users/{user_id}</code></div>
          <div class="endpoint"><span class="method delete">DELETE</span><code>/api/v1/users/{user_id}</code></div>
        </div>
        <div class="card">
          <h2>Records</h2>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/records</code></div>
          <div class="endpoint"><span class="method post">POST</span><code>/api/v1/records</code></div>
          <div class="endpoint"><span class="method patch">PATCH</span><code>/api/v1/records/{record_id}</code></div>
          <div class="endpoint"><span class="method delete">DELETE</span><code>/api/v1/records/{record_id}</code></div>
        </div>
        <div class="card">
          <h2>Dashboard</h2>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/dashboard/summary</code></div>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/dashboard/category-breakdown</code></div>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/dashboard/trends</code></div>
          <div class="endpoint"><span class="method get">GET</span><code>/api/v1/dashboard/recent-activity</code></div>
        </div>
      </section>

      <section class="card" style="margin-top: 24px;">
        <h2>Example Login</h2>
        <pre>curl -X POST http://127.0.0.1:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"admin@finance.local\",\"password\":\"Admin123!\"}"</pre>
      </section>
    </div>
  </body>
</html>
"""
