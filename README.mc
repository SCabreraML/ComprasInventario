```bash
git clone git@gitlab.com:BCPU/compras-inventario.git
cd compras-inventario
```

---

## 2. Crear un entorno virtual

```bash
python -m venv venv
```

---

## 3. Activar el entorno virtual

### En CMD

```cmd
venv\Scripts\activate
```

### En PowerShell

Si es la primera vez que utilizas un entorno virtual en PowerShell, ejecuta:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Confirma escribiendo:

```text
Y
```

Luego activa el entorno:

```powershell
venv\Scripts\Activate.ps1
```

---

## 4. Instalar las dependencias

```bash
pip install -r requirements.txt
```

---

## 5. Aplicar las migraciones

```bash
python manage.py migrate
```

---

## 6. Crear los roles del sistema

```bash
python manage.py crear_roles
```

Este comando creará automáticamente los siguientes grupos:

- Administrador
- Encargado de Compras

---

## 7. Crear un superusuario

```bash
python manage.py createsuperuser
```

Completa los datos solicitados:

- Nombre de usuario
- Correo electrónico (opcional)
- Contraseña

---

## 8. Ejecutar el servidor

```bash
python manage.py runserver
```

Abre el proyecto en:

```
http://127.0.0.1:8000/
```

Panel de administración:

```
http://127.0.0.1:8000/admin/
```