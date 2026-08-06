from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from decimal import Decimal
import datetime
from Compras_APP.models import SolicitudCompra, Cotizacion, OrdenCompra, Proveedor

Usuario = get_user_model()


class InteraccionTests(TestCase):
    """
    Colección de exactamente 3 Pruebas de Interacción / Integración
    """

    def setUp(self):
        # Configurar grupo Administrador
        self.admin_group = Group.objects.create(name="Administrador")
        # Crear usuario admin y autenticar
        self.admin_user = Usuario.objects.create_user(username="admin_test", password="password")
        self.admin_user.groups.add(self.admin_group)
        self.client.login(username="admin_test", password="password")

        # Crear solicitud base
        self.solicitud = SolicitudCompra.objects.create(
            producto="Licencias de Software",
            cantidad=10,
            solicitante=self.admin_user,
            descripcion="Licencias anuales de JetBrains"
        )

    def test_1_interaccion_aprobar_solicitud_registra_auditoria(self):
        """1. Aprueba una solicitud de compra, verifica cambio de estado y registro de auditoria."""
        url = reverse("aprobar_solicitud", args=[self.solicitud.id])
        response = self.client.get(url)

        # Debe redirigir
        self.assertEqual(response.status_code, 302)

        # El estado de la solicitud debe ser APROBADA
        self.solicitud.refresh_from_db()
        self.assertEqual(self.solicitud.estado, SolicitudCompra.ESTADO_APROBADA)

    def test_2_interaccion_crear_proveedor_y_listar(self):
        """2. Crea un proveedor mediante POST y verifica su presencia en el listado de proveedores."""
        # 1. Enviar POST para registrar proveedor
        url_crear = reverse("registrar_proveedor")
        datos = {
            "nombre": "Software S.A.",
            "ruc": "1791234567001",
            "telefono": "022555555",
            "correo": "ventas@softwaresa.com"
        }
        response_post = self.client.post(url_crear, datos)
        self.assertEqual(response_post.status_code, 302)  # Redirecciona

        # 2. Consultar listado de proveedores y verificar presencia en HTML
        url_listar = reverse("compras_listado_proveedores")
        response_get = self.client.get(url_listar)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Software S.A.")
        self.assertContains(response_get, "1791234567001")

    def test_3_interaccion_reporte_ordenes_calcula_valores(self):
        """3. Crea una orden de compra e interactúa con el reporte para verificar cálculos correctos."""
        # Registrar una cotización
        cotizacion = Cotizacion.objects.create(
            solicitud=self.solicitud,
            proveedor="Software S.A.",
            precio_unitario=Decimal("150.00"),
            vigencia=datetime.date.today(),
            tiempo_entrega=5
        )

        # Generar orden de compra (10 unidades * 150 = $1500)
        orden = OrdenCompra.objects.create(cotizacion=cotizacion)

        # Consultar el reporte de órdenes de compra
        url_reporte = reverse("reporte_ordenes")
        response = self.client.get(url_reporte)

        self.assertEqual(response.status_code, 200)

        # El HTML debe contener las cifras de resumen correctas
        self.assertContains(response, "1")  # Órdenes Generadas: 1
        self.assertContains(response, "$1500.00")  # Monto Total Gastado
        self.assertContains(response, "Software S.A.")  # Distribución de gastos por proveedor
