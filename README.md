# Skilly - Plataforma de Marketplace y Custodia de Servicios (MVP)

Plataforma web disenada para conectar Profesionales Independientes con Organizaciones, incorporando gestion de agenda horaria, contratacion agil (Guest Checkout) y procesamiento de pagos en garantia (Escrow) mediante Webpay Plus (Transbank).

---

## Caracteristicas Principales

### 1. Gestion de Usuarios y Perfiles (users)
- Roles diferenciados: Profesional Independiente, Organizacion y Administrador Skilly.
- Validacion de Identidad: Carga de documentos de acreditacion profesional y verificacion desde el Back-office.
- Perfil SaaS Directo: Generacion de URL amigable (/pro/<slug>) para agendamiento directo.

### 2. Catalogo y Disponibilidad (services & availability)
- Publicacion de paquetes de servicios con descripcion, entregables y tarifas.
- Configuracion de agenda semanal en bloques de tiempo (tramos de 20 minutos).
- Bloqueo temporal preventivo para evitar colisiones en reservas concurrentes.

### 3. Agendamiento y Flujo de Reserva (bookings)
- Guest Checkout: Permite a clientes externos u organizaciones agendar sin necesidad de iniciar sesion previa.
- Estados trazables de la reserva: PENDIENTE, PRE_RESERVADA, ACEPTADA, PAGADO_EN_CUSTODIA, EN_EJECUCION, FINALIZADO, EN_DISPUTA, CANCELADO.
- Mensajeria interna privada y segura asociada a la reserva confirmada.

### 4. Pagos en Custodia / Escrow (escrow_payments)
- Integracion con Webpay Plus (Transbank SDK) en ambiente de integracion.
- Retencion temporal de fondos en garantia hasta la conformidad del servicio ejecutado.
- Calculo automatico de comisiones operativas (Take Rate).

### 5. Control de Calidad y Resolucion de Conflictos (reviews, disputes, backoffice)
- Evaluacion interna: Asignacion de insignias cualitativas visibles exclusivamente en el Back-office para control de calidad interna.
- Modulo de Disputas: Congelamiento de fondos y herramientas de arbitraje para el Administrador.
- Panel administrativo para metricas financieras, validacion de antecedentes y transacciones.

---

## Stack Tecnologico

- Backend: Python 3.11+ / Django 5+
- Pasarela de Pago: transbank-sdk (Webpay Plus REST)
- Base de Datos: SQLite3 (entorno de desarrollo) / Compatible con PostgreSQL
- Frontend: Django Templates + CSS / Bootstrap / Tailwind

---


## Instalacion y Puesta en Marcha

### 1. Clonar el repositorio
git clone <URL_DEL_REPOSITORIO>
cd Skilly

### 2. Crear y activar el entorno virtual

- En Windows (PowerShell):
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  python -m venv venv
  .\venv\Scripts\Activate.ps1

- En Linux / macOS:
  python3 -m venv venv
  source venv/bin/activate

### 3. Instalar dependencias
pip install -r requirements.txt

(En caso de no contar con el archivo de requerimientos, las librerias base son: pip install django pillow transbank-sdk)

### 4. Aplicar migraciones
python manage.py makemigrations
python manage.py migrate

### 5. Cargar datos de prueba (Seed Data)
python manage.py seed_data

### 6. Ejecutar el servidor
python manage.py runserver

Acceso local disponible en: http://127.0.0.1:8000/

---

## Pruebas de Pago con Webpay Plus

Datos para simular transacciones aprobadas en el ambiente de integracion de Transbank:
- Tarjeta de Credito / Redcompra de prueba: 4051 8856 0044 6623
- Vencimiento: Cualquier fecha futura (ejemplo: 12/28)
- CVV: 123
- RUT: 11.111.111-1
- Clave: 123****
