# My Kubernetes App

Ez egy egyszerű Python Flask alkalmazás, amit Kubernetes Kind segítségével futtatunk.

## 🚀 Telepítés és futtatás

1️⃣ **Kind klaszter létrehozása**  
```sh
kind create cluster --config kind-cluster.yaml
```

2️⃣ **Docker image építése**  
```sh
docker build -t my-k8s-app:latest .
```

3️⃣ **Image betöltése Kind klaszterbe**  
```sh
kind load docker-image my-k8s-app:latest
```

4️⃣ **Kubernetes Deployment és Service létrehozása**  
```sh
kubectl apply -f manifests/
```

5️⃣ **Elérés böngészőből**  
```sh
curl http://localhost:30000
```
Várható válasz:  
```
Hello, Kubernetes!
```
