---
name: issues
description: Gestiona GitHub Issues del repositorio remoto. Usa esta skill cuando el usuario pida listar, crear, editar, cerrar, comentar o consultar issues de GitHub. Keywords: issues, github, bug, feature, tarea, ticket, milestone, label.
---

# GitHub Issues Skill

## Contexto del repositorio

El repositorio remoto se detecta automáticamente con:
```bash
git remote get-url origin
```
Para este proyecto: `jonnamartiinUdemm/alquisearch`

## Autenticación

La API de GitHub requiere autenticación para repos privados y para escribir (crear/editar issues).

### Detectar token disponible
Ejecuta en terminal:
```bash
echo "${GITHUB_TOKEN:-${GH_TOKEN:-NO_TOKEN}}"
```

### Si no hay token configurado
1. Pide al usuario que cree un Personal Access Token (classic) en https://github.com/settings/tokens con scope `repo`.
2. Indícale que lo exporte:
   ```bash
   export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"
   ```
3. Alternativamente, puede instalar GitHub CLI: `brew install gh && gh auth login`

### Usar gh CLI si está disponible
Verifica con `command -v gh`. Si existe, úsalo en lugar de curl — es más simple:
```bash
gh issue list --repo OWNER/REPO
gh issue create --repo OWNER/REPO --title "..." --body "..."
```

## Operaciones con curl (API REST v3)

Todas las llamadas usan el pattern:
```bash
REPO="jonnamartiinUdemm/alquisearch"
AUTH="Authorization: Bearer $GITHUB_TOKEN"
API="https://api.github.com/repos/$REPO"
```

### Listar issues
```bash
curl -s -H "$AUTH" "$API/issues?state=open&per_page=30" | python3 -c "
import sys,json
issues = json.load(sys.stdin)
if isinstance(issues, dict) and 'message' in issues:
    print('Error:', issues['message']); sys.exit(1)
for i in issues:
    labels = ', '.join(l['name'] for l in i.get('labels',[]))
    assignee = i.get('assignee',{})
    assign_name = assignee.get('login','') if assignee else ''
    print(f'#{i[\"number\"]} [{i[\"state\"]}] {i[\"title\"]}')
    if labels: print(f'   Labels: {labels}')
    if assign_name: print(f'   Assignee: {assign_name}')
"
```
Parámetros útiles: `state=open|closed|all`, `labels=bug,enhancement`, `milestone=1`, `per_page=100`, `page=2`

### Ver un issue específico
```bash
curl -s -H "$AUTH" "$API/issues/{NUMBER}" | python3 -c "
import sys,json; i=json.load(sys.stdin)
print(f'#{i[\"number\"]} {i[\"title\"]}')
print(f'State: {i[\"state\"]} | Created: {i[\"created_at\"][:10]}')
print(f'Author: {i[\"user\"][\"login\"]}')
if i.get('body'): print(f'\n{i[\"body\"]}')
"
```

### Ver comentarios de un issue
```bash
curl -s -H "$AUTH" "$API/issues/{NUMBER}/comments" | python3 -c "
import sys,json
for c in json.load(sys.stdin):
    print(f'--- {c[\"user\"][\"login\"]} ({c[\"created_at\"][:10]}) ---')
    print(c['body']); print()
"
```

### Crear un issue
```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$API/issues" \
  -d '{
    "title": "Título del issue",
    "body": "Descripción con **markdown**",
    "labels": ["bug"],
    "assignees": ["jonnamartiinUdemm"]
  }' | python3 -c "import sys,json; i=json.load(sys.stdin); print(f'Created: #{i[\"number\"]} — {i[\"html_url\"]}')"
```

### Editar un issue
```bash
curl -s -X PATCH -H "$AUTH" -H "Content-Type: application/json" \
  "$API/issues/{NUMBER}" \
  -d '{"title": "Nuevo título", "body": "Nuevo body", "state": "open", "labels": ["enhancement"]}'
```

### Cerrar un issue
```bash
curl -s -X PATCH -H "$AUTH" -H "Content-Type: application/json" \
  "$API/issues/{NUMBER}" \
  -d '{"state": "closed", "state_reason": "completed"}'
```
`state_reason` puede ser: `completed`, `not_planned`

### Comentar un issue
```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$API/issues/{NUMBER}/comments" \
  -d '{"body": "Comentario con **markdown**"}'
```

### Listar labels disponibles
```bash
curl -s -H "$AUTH" "$API/labels" | python3 -c "
import sys,json
for l in json.load(sys.stdin): print(f'  {l[\"name\"]} — {l.get(\"description\",\"\")}')"
```

### Crear un label
```bash
curl -s -X POST -H "$AUTH" -H "Content-Type: application/json" \
  "$API/labels" \
  -d '{"name": "nombre", "color": "0e8a16", "description": "Descripción"}'
```

### Listar milestones
```bash
curl -s -H "$AUTH" "$API/milestones" | python3 -c "
import sys,json
for m in json.load(sys.stdin): print(f'  #{m[\"number\"]} {m[\"title\"]} (open:{m[\"open_issues\"]} closed:{m[\"closed_issues\"]})')"
```

## Flujo recomendado

1. **Siempre** verificar primero si hay token: `echo "${GITHUB_TOKEN:-${GH_TOKEN:-NO_TOKEN}}"`
2. Si no hay token y la operación lo requiere, pedir al usuario que lo configure.
3. Para operaciones de lectura en repos **públicos**, no se necesita token (pero este repo es privado).
4. Escapa correctamente el JSON en los bodies — usa `python3 -c "import json; print(json.dumps(...))"` si el contenido tiene caracteres especiales.
5. Parsea siempre la respuesta con Python para presentar la info de forma legible.
6. Ante un error 401, indica que el token es inválido o ha expirado.
7. Ante un error 404, puede ser repo privado sin token o issue inexistente.

## Formato de respuesta al usuario

Al listar issues, presenta una tabla o lista clara:
```
| #   | Título                        | Labels      | Estado |
|-----|-------------------------------|-------------|--------|
| #12 | Bug: login no funciona        | bug         | open   |
| #11 | Feature: filtro por barrio    | enhancement | open   |
```

Al crear/editar, confirma con el número y el enlace directo.
