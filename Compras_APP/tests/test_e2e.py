from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from decimal import Decimal
import datetime
from Compras_APP.models import SolicitudCompra, Cotizacion, OrdenCompra

Usuario = get_user_model()


class ComprasE2ETest(TestCase):
    """
    Prueba End-to-End (E2E) completa del Flujo de Adquisiciones de Compras
    """

    def setUp(self):
        # Crear grupos de permisos
        self.admin_group = Group.objects.create(name="Administrador")

        # Crear usuarios con diferentes roles
        self.solicitante = Usuario.objects.create_user(username="solicitante_e2e", password="password")
        self.admin = Usuario.objects.create_user(username="admin_e2e", password="password")
        self.admin.groups.add(self.admin_group)

    def test_flujo_completo_adquisiciones_e2e(self):
        """
        Simula el ciclo de vida completo de una adquisición de principio a fin:
        1. Registro de Solicitud de Compra (Solicitante)
        2. Aprobación de la Solicitud (Administrador)
        3. Registro de Cotización (Encargado)
        4. Generación de Orden de Compra
        5. Visualización e Impresión de la Orden de Compra (HU-21)
        6. Descarga y Exportación en formato PDF (HU-22)
        """
        # --- PASO 1: Solicitante registra una nueva solicitud ---
        self.client.login(username="solicitante_e2e", password="password")
        url_crear = reverse("crear_solicitud")
        datos_solicitud = {
            "producto": "Sillas Ergonómicas Ejecutivas",
            "cantidad": 12,
            "descripcion": "Renovación de sillería de gerencia"
        }
        response_crear = self.client.post(url_crear, datos_solicitud)
        self.assertEqual(response_crear.status_code, 302)  # Redirige a listado

        # Validar en base de datos
        solicitud = SolicitudCompra.objects.filter(producto="Sillas Ergonómicas Ejecutivas").first()
        self.assertIsNotNone(solicitud)
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.client.logout()

        # --- PASO 2: Administrador aprueba la solicitud ---
        self.client.login(username="admin_e2e", password="password")
        url_aprobar = reverse("aprobar_solicitud", args=[solicitud.id])
        response_aprobar = self.client.get(url_aprobar)
        self.assertEqual(response_aprobar.status_code, 302)  # Redirige a listado

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.estado, "APROBADA")

        # --- PASO 3: Encargado de compras registra cotización ---
        url_cotizar = reverse("registrar_cotizacion", args=[solicitud.id])
        datos_cotizacion = {
            "proveedor": "ErgoOffice Ecuador",
            "precio_unitario": Decimal("110.00"),
            "vigencia": "2026-12-31",
            "tiempo_entrega": 6
        }
        response_cotizar = self.client.post(url_cotizar, datos_cotizacion)
        self.assertEqual(response_cotizar.status_code, 302)  # Redirige al listado de cotizaciones

        # Validar en base de datos
        cotizacion = Cotizacion.objects.filter(solicitud=solicitud).first()
        self.assertIsNotNone(cotizacion)
        self.assertEqual(cotizacion.proveedor, "ErgoOffice Ecuador")

        # --- PASO 4: Generación de la Orden de Compra ---
        url_generar_orden = reverse("generar_orden", args=[cotizacion.id])
        response_generar = self.client.get(url_generar_orden)
        self.assertEqual(response_generar.status_code, 302)  # Redirige a ver detalle de orden

        # Validar que la orden se haya creado
        orden = OrdenCompra.objects.filter(cotizacion=cotizacion).first()
        self.assertIsNotNone(orden)
        # Costo total esperado: 12 unidades * 110.00 = $1320.00
        self.assertEqual(orden.costo_total, Decimal("1320.00"))

        # --- PASO 5: Visualización de Orden Imprimible (HU-21) ---
        url_ver_orden = reverse("ver_orden", args=[orden.id])
        response_ver = self.client.get(url_ver_orden)
        self.assertEqual(response_ver.status_code, 200)

        # Verificar detalles de orden y triggers de impresión
        html_ver = response_ver.content.decode("utf-8")
        self.assertIn("Sillas Ergonómicas Ejecutivas", html_ver)
        self.assertIn("ErgoOffice Ecuador", html_ver)
        self.assertIn("$1320.00", html_ver)
        self.assertIn("window.print();", html_ver)  # HU-21 print script trigger

        # --- PASO 6: Exportación de la Orden a PDF (HU-22) ---
        url_pdf = reverse("exportar_orden_pdf", args=[orden.id])
        response_pdf = self.client.get(url_pdf)
        self.assertEqual(response_pdf.status_code, 200)
        self.assertEqual(response_pdf.headers["Content-Type"], "application/pdf")
        self.assertTrue(response_pdf.content.startswith(b"%PDF"))  # Formato PDF válido
