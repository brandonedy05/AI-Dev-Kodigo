#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "==> [1/3] Verificando sintaxis Python (backend + frontend)..."
python3 -m compileall -q backend/app backend/tests frontend/app

echo "==> [2/3] Ejecutando pruebas del backend (pytest)..."
if [[ -x "backend/.venv/bin/pytest" ]]; then
  (cd backend && .venv/bin/pytest -v)
else
  echo "ERROR: No se encontró backend/.venv/bin/pytest" >&2
  exit 1
fi

echo "==> [3/3] Verificando vistas del frontend (Flet 1.1.2)..."
if [[ -x "frontend/.venv/bin/python" ]]; then
  (
    cd frontend
    .venv/bin/python -c "
from app.main import main
from app.services.api_client import POSApiClient
from app.views.pos_terminal_view import POSTerminalView
from app.views.cash_register_view import CashRegisterView
from app.views.login_view import LoginView
from app.views.users_view import UsersView
from app.views.secondary_views import ProductsView, CustomersView, ReportsView

api = POSApiClient(base_url='http://127.0.0.1:59999/api/v1')
login_v = LoginView(api, lambda u: None)
users_v = UsersView(api, lambda m, c: None)
pos = POSTerminalView(api, lambda m, c: None)
assert isinstance(pos.payment_selector.selected, list), 'SegmentedButton.selected debe ser list'
cash = CashRegisterView(api, lambda m, c: None, lambda: None)
prods = ProductsView(api)
custs = CustomersView(api)
reps = ReportsView(api)
for view in (login_v, users_v, cash, prods, custs, reps):
    try:
        view.refresh()
    except Exception as exc:
        if 'Control must be added to the page first' in str(exc):
            raise
print('FRONTEND SMOKE CHECK OK')
"
  )
else
  echo "ERROR: No se encontró frontend/.venv/bin/python" >&2
  exit 1
fi

echo "==> QUALITY GATE COMPLETADO SIN ERRORES"

