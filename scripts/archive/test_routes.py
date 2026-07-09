import app

# Look at FastAPI routes
routes = []
if hasattr(app, 'app') and hasattr(app.app, 'routes'):
    for r in app.app.routes:
        if hasattr(r, 'methods') and hasattr(r, 'endpoint'):
            routes.append(f"{r.path} -> {r.endpoint.__name__}")

routes.sort()
for r in routes:
    print(r)
