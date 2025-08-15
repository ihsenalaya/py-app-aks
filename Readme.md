### Local (Docker Compose)
# Lancer
`docker compose up -d --build`

# Tester la santé
`curl http://localhost:8000/healthz`

# Créer une tâche
`curl -X POST http://localhost:8000/todos -H 'Content-Type: application/json' -d '{"title":"Test"}'`

# Lister les tâches
`curl http://localhost:8000/todos`

# Accès Adminer :
Ouvrez [http://localhost:8080](http://localhost:8080) et connectez-vous sur PostgreSQL avec :
- Système : PostgreSQL
- Serveur : db
- Utilisateur : appuser
- Mot de passe : apppass
- Base : appdb

### Kubernetes (AKS)
`kubectl apply -f k8s/namespace.yaml`
`kubectl apply -f k8s/secret-db.yaml`
`kubectl apply -f k8s/configmap-app.yaml`
`kubectl apply -f k8s/postgres-statefulset.yaml`
`kubectl apply -f k8s/app-deployment.yaml`
`kubectl apply -f k8s/app-service.yaml`

# (Optionnel) Ingress
`kubectl apply -f k8s/ingress.yaml`

# Vérifier
`kubectl -n aks-pg-demo get pods,svc,ingress,cm,secret,pvc`