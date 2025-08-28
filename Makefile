.PHONY: dev backend frontend install-backend install-frontend

dev: install-backend install-frontend
	cd backend && python run.py & \
	cd frontend && npm run dev

install-backend:
	cd backend && pip install -r app/requirements.txt

install-frontend:
	cd frontend && npm install

backend:
	cd backend && python run.py

frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest

clean:
	rm -rf backend/app.db
	rm -rf backend/logs
	rm -rf frontend/node_modules