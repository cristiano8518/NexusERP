# NexusERP — Troubleshooting

## localhost:3000 — ERR_EMPTY_RESPONSE / Connection reset

### Most likely cause
Next.js inside Docker was listening only on `127.0.0.1` inside the container, not on `0.0.0.0`, so the host browser gets an empty response.

**Fix applied:** `package.json` → `"dev": "next dev -H 0.0.0.0 -p 3000"`

Rebuild frontend:
```powershell
cd C:\Users\user\NexusERP
docker compose build --no-cache frontend
docker compose up -d frontend
```

> Ескерту: бұл қадамдар development үшін. Production ортада толық `docker compose down` қолданбаңыз.

### Fast checks (in order)

1. **Docker Desktop is running**

2. **Containers status**
   ```powershell
   docker compose ps
   ```
   `nexuserp-frontend` must be **Up**.

3. **Frontend logs**
   ```powershell
   docker compose logs frontend --tail 80
   ```
   Look for: `Ready` or `Local: http://0.0.0.0:3000`

4. **Port in use**
   ```powershell
   netstat -ano | findstr :3000
   ```

5. **Restart only frontend**
   ```powershell
   docker compose restart frontend
   ```

### If frontend keeps crashing
```powershell
docker compose build --no-cache frontend
docker compose up frontend
```

### Backend check (compare)
- http://localhost:8000/api/v1/health/ — if this works but 3000 does not, problem is frontend-only.
