# Guía de Despliegue — AlquiSearch España

Este documento describe cómo desplegar la aplicación en distintas plataformas cloud.

---

## Requisitos previos

| Requisito | Versión mínima |
|-----------|---------------|
| Docker    | 24.x          |
| Docker Compose | v2.x     |
| Python (sin Docker) | 3.11 |

---

## Variables de entorno

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `DB_DIR` | Directorio donde se guardan las bases de datos SQLite | Directorio del backend |
| `PORT`   | Puerto en que escucha uvicorn | `8000` |

---

## 1. Ejecución local (sin Docker)

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Abre el navegador en `http://localhost:8000`.

---

## 2. Docker — build y run local

```bash
# Construir imagen
docker build -t alquisearch .

# Ejecutar (con volumen para persistencia de BBDDs)
docker run -d \
  --name alquisearch \
  -p 8000:8000 \
  -v alquisearch_data:/app/data \
  -e DB_DIR=/app/data \
  alquisearch
```

---

## 3. Docker Compose (recomendado)

```bash
# Levantar en segundo plano
docker compose up -d

# Ver logs en tiempo real
docker compose logs -f

# Parar
docker compose down

# Parar y eliminar volumen de datos (¡borra las BBDDs!)
docker compose down -v
```

Para actualizar a una nueva versión:

```bash
git pull
docker compose down
docker compose up -d --build
```

---

## 4. DigitalOcean — Droplet VPS

### 4.1 Crear el Droplet

1. Inicia sesión en [DigitalOcean](https://cloud.digitalocean.com).
2. **Create → Droplet** → elige **Ubuntu 24.04 LTS**.
3. Plan recomendado: **Basic / Regular / 2 GB RAM** (~12 USD/mes).
4. Añade tu clave SSH o crea una contraseña.
5. Activa **Monitoring** (opcional pero recomendado).

### 4.2 Instalar Docker en el Droplet

```bash
ssh root@<IP_DROPLET>

# Actualizar paquetes
apt-get update && apt-get upgrade -y

# Instalar Docker oficial
curl -fsSL https://get.docker.com | sh

# Verificar
docker --version
docker compose version
```

### 4.3 Subir el código

**Opción A — Git (recomendado):**

```bash
git clone https://github.com/TU_USUARIO/alquisearch.git /opt/alquisearch
cd /opt/alquisearch
```

**Opción B — scp desde tu máquina local:**

```bash
scp -r /ruta/local/al/proyecto root@<IP_DROPLET>:/opt/alquisearch
```

### 4.4 Arrancar la aplicación

```bash
cd /opt/alquisearch
docker compose up -d --build
```

Accede en `http://<IP_DROPLET>:8000`.

### 4.5 Nginx como proxy inverso + puerto 80 (opcional)

```bash
apt-get install -y nginx

# /etc/nginx/sites-available/alquisearch
cat <<'EOF' > /etc/nginx/sites-available/alquisearch
server {
    listen 80;
    server_name TU_DOMINIO_O_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

ln -s /etc/nginx/sites-available/alquisearch /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 4.6 HTTPS con Let's Encrypt

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d TU_DOMINIO
```

### 4.7 Servicio systemd para arranque automático

Docker Compose ya gestiona el reinicio (`restart: unless-stopped`).  
Para asegurarte de que Docker arranca con el sistema:

```bash
systemctl enable docker
```

---

## 5. DigitalOcean App Platform (más sencillo, sin SSH)

App Platform abstrae toda la infraestructura. Solo necesitas un repositorio GitHub.

1. **Conecta tu repositorio:** Dashboard → **Create → App** → selecciona el repo.
2. **Detección automática:** detectará el `Dockerfile` en la raíz.
3. **Variables de entorno:** añade `DB_DIR=/data`.
4. **Storage:** añade un **Persistent Storage** en `/data` (10 GB, incluido en Basic).
5. **Puerto:** App Platform usará `8000` automáticamente (detectado del `EXPOSE 8000`).
6. Click **Deploy**.

> **Nota:** El plan `Basic` (~5 USD/mes) puede ser insuficiente para los scrapers simultáneos. Se recomienda `Professional` (12 USD/mes) o el Droplet VPS del punto 4.

---

## 6. Microsoft Azure — App Service con Docker

### 6.1 Prerequisitos

```bash
# Instalar Azure CLI
brew install azure-cli      # macOS
# o: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash   (Ubuntu)

az login
```

### 6.2 Crear un Azure Container Registry (ACR) y subir la imagen

```bash
RESOURCE_GROUP=alquisearch-rg
ACR_NAME=alquisearchacr$RANDOM   # debe ser único globalmente
LOCATION=westeurope

# Crear grupo de recursos
az group create --name $RESOURCE_GROUP --location $LOCATION

# Crear registro de contenedores
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Autenticarse en el ACR
az acr login --name $ACR_NAME

# Construir y subir imagen
docker build -t $ACR_NAME.azurecr.io/alquisearch:latest .
docker push $ACR_NAME.azurecr.io/alquisearch:latest
```

### 6.3 Crear App Service Plan y Web App

```bash
APP_NAME=alquisearch-app-$RANDOM

# Plan (B1 = ~13 USD/mes, Linux)
az appservice plan create \
  --name alquisearch-plan \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Web App con imagen del ACR
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan alquisearch-plan \
  --name $APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/alquisearch:latest \
  --docker-registry-server-user $ACR_NAME \
  --docker-registry-server-password $ACR_PASSWORD

# Variables de entorno
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings DB_DIR=/home/data WEBSITES_PORT=8000
```

### 6.4 Persistencia de datos (Azure Files)

Azure App Service usa `/home` como almacenamiento persistente por defecto.  
Apunta `DB_DIR=/home/data` y los archivos `.db` sobrevivirán reinicios.

```bash
# Crear directorio de datos en el contenedor (primera vez)
az webapp ssh --resource-group $RESOURCE_GROUP --name $APP_NAME
# Dentro del contenedor:
mkdir -p /home/data
```

### 6.5 Ver la aplicación

```bash
echo "https://$APP_NAME.azurewebsites.net"
```

---

## 7. Actualizar en producción

### DigitalOcean Droplet

```bash
cd /opt/alquisearch
git pull
docker compose down
docker compose up -d --build
```

### Azure App Service

```bash
docker build -t $ACR_NAME.azurecr.io/alquisearch:latest .
docker push $ACR_NAME.azurecr.io/alquisearch:latest

# Forzar reinicio con la nueva imagen
az webapp restart --resource-group $RESOURCE_GROUP --name $APP_NAME
```

---

## 8. Gestión de la cuenta administrador

Al arrancarse por primera vez, el sistema crea automáticamente un usuario admin:

| Campo    | Valor      |
|----------|------------|
| Usuario  | `admin`    |
| Contraseña | `Admin1234!` |

**Cambia la contraseña inmediatamente** desde el panel de administración (`/admin`).

---

## 9. Consideraciones de seguridad en producción

- Usa siempre HTTPS (Certbot / Azure managed cert).
- Cambia la contraseña del admin en el primer acceso.
- Limita el acceso al panel `/admin` por IP con Nginx si es posible.
- Configura backups periódicos del volumen de datos (archivos `.db`).
- El endpoint `/api/admin/*` requiere token de administrador — no lo expongas sin HTTPS.

---

## 10. Backup de bases de datos

```bash
# Copiar DBs desde volumen Docker a local
docker compose exec app sh -c "ls /app/data/"
docker cp alquisearch:/app/data/. ./backup_$(date +%Y%m%d)/

# O desde un Droplet
scp root@<IP>:/var/lib/docker/volumes/alquisearch_data/_data/*.db ./backups/
```
