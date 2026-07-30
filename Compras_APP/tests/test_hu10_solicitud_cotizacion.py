from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from Compras_APP.models import SolicitudCompra, SolicitudCotizacion, Proveedor
from Compras_APP.forms import SolicitudCotizacionForm

Usuario = get_user_model()


class SolicitudCotizacionTests(TestCase):

    def setUp(self):
        # 1. Crear usuario de prueba y autenticarlo
        self.user = Usuario.objects.create_user(
            username="compras_user", 
            password="password123"
        )
        self.client.login(username="compras_user", password="password123")

        # 2. Crear solicitud de compra base
        self.solicitud_compra = SolicitudCompra.objects.create(
            solicitante=self.user,
            producto="Laptops corporativas",
            cantidad=5,
            justificacion="Renovación de equipos",
            estado="PENDIENTE"
        )

        # 3. Crear proveedor de prueba
        self.proveedor = Proveedor.objects.create(
            nombre="Proveedor Tech Ecuador",
            ruc="1790011223001",
            telefono="0998765432",
            correo="ventas@proveedortech.com"
        )

    def test_crear_solicitud_cotizacion_get(self):
        """Verifica que el formulario de solicitud de cotización cargue correctamente."""
        url = reverse("crear_solicitud_cotizacion", kwargs={"pk": self.solicitud_compra.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "compras/crear_solicitud_cotizacion.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], SolicitudCotizacionForm)

    def test_crear_solicitud_cotizacion_post_exitoso(self):
        """Verifica que se cree la solicitud de cotización asociándola a la compra."""
        url = reverse("crear_solicitud_cotizacion", kwargs={"pk": self.solicitud_compra.pk})
        
        datos = {
            "proveedores": [self.proveedor.pk],
            "observaciones": "Solicitud urgente de precios"
        }

        response = self.client.post(url, datos)

        # Debe redirigir a ver cotizaciones
        cotizacion_creada = SolicitudCotizacion.objects.filter(solicitud_compra=self.solicitud_compra).first()
        self.assertIsNotNone(cotizacion_creada)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("compras_ver_cotizaciones", kwargs={"pk": cotizacion_creada.pk}))

    def test_redireccion_si_ya_existe_solicitud_cotizacion(self):
        """Si ya existe una solicitud de cotización asociada, debe redirigir directamente."""
        cotizacion_existente = SolicitudCotizacion.objects.create(
            solicitud_compra=self.solicitud_compra,
            observaciones="Cotización previa"
        )

        url = reverse("crear_solicitud_cotizacion", kwargs={"pk": self.solicitud_compra.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("compras_ver_cotizaciones", kwargs={"pk": cotizacion_existente.pk}))