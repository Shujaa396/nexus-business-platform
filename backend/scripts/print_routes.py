from app.main import app

paths = sorted({r.path for r in app.routes})
for p in paths:
    print(p)
