# Dagger Full-Stack Demo

Ez a projekt egy egyszerű **backend + frontend** alkalmazást mutat be, amelyet **Dagger** segítségével:

1. **Build-eli** és **push-olja** a Docker-image-eket (backend, frontend)
2. **Deploy-olja** őket egy lokális K3s klaszterbe
3. **Megvárja** a Deployment-ek beállását (rollout)
4. **Teszteli** külön a backend API-t, a frontend statikus HTML-t és egy proxyzott end-to-end (`/api`) kérést

---

## Követelmények

- **Dagger CLI** telepítve és beállítva
- **Python 3.10+**
- Internet hozzáférés a **ttl.sh** publikus registry-hez
- (Opcionális) `kubectl` a lokális debughoz


---

## Főbb Dagger pipeline függvények

- `build_and_push_images(src)`
  - **Input**: a projekt gyökérkönyvtára
  - **Kimenet**: Image-referenciák (`ttl.sh/my-backend-app:latest`, `ttl.sh/my-frontend-app:latest`)

- `server(src)`
  - Build & push után elindít egy K3s klasztert, majd `kubectl apply -f manifests/`
  - Elmenti az objektumban a klaszterpéldányt és a kubeconfig-et

- `wait_rollout()`
  - Várja, hogy mindkét Deployment (`backend-app`, `frontend-app`) **rollout status**-a kész legyen

- `test_backend()`
  - Lekéri a `/api` végpontot egy rövid-életű `curl` pod segítségével

- `test_frontend()`
  - Lekéri a gyökér `index.html` statikus fájlt ugyanígy

- `test_e2e()`
  - End-to-end teszt: a frontend proxy-n (`/api`) keresztül hívja a backend-et

- `deploy_full_stack(src)`
  - Sorban meghívja a fenti lépéseket, és visszaadja a **Backend**, **Frontend** és **E2E** tesztek eredményeit

---

## Használat

A pipeline-t a Dagger CLI `call` parancsával indíthatod el:

```bash
# Full pipeline futtatása (build → deploy → wait → tesztek)
dagger call deploy-full-stack --src=app
```

Ha külön szeretnéd futtatni az egyes lépéseket:

```bash
dagger call build-and-push-images --src=app
dagger call server              --src=app
dagger call wait-ready
dagger call test-backend
dagger call test-frontend
dagger call test-e2e
```

- A `--src` paraméter mindig arra a könyvtárra mutat, ami tartalmazza a `backend/`, `frontend/` alkönyvtárakat.

---

## Takarítás

A K3s klaszter és a szolgáltatások törléséhez egyszerűen állítsd le vagy távolítsd el a Dagger objektumot.

---