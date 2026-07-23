# ============================================================
# COMINV-66 - HU-11: Consultar cotizaciones registradas
# Integrante encargado: Luis Valarezo
# ============================================================
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from Compras_APP.models import Cotizacion, Proveedor, SolicitudCompra, SolicitudCotizacion


class ConsultarCotizacionesTest(TestCase):
    """COMINV-66 - HU-11: Consultar cotizaciones registradas."""

    def setUp(self):
        self.solicitud_compra = SolicitudCompra.objects.create(
            producto_codigo="789012",
            producto_nombre="Arroz",
            cantidad_solicitada=20,
            estado=SolicitudCompra.ESTADO_SIN_STOCK,
        )
        self.solicitud_cotizacion = SolicitudCotizacion.objects.create(
            solicitud_compra=self.solicitud_compra
        )
        self.proveedor = Proveedor.objects.create(nombre="Proveedor Uno")
        self.solicitud_cotizacion.proveedores.add(self.proveedor)

        self.cotizacion = Cotizacion.objects.create(
            solicitud_cotizacion=self.solicitud_cotizacion,
            proveedor=self.proveedor,
            precio_unitario=1.50,
            tiempo_entrega_dias=5,
            vigencia=date.today() + timedelta(days=30),
        )

    def test_ver_cotizaciones_responde_200(self):
        url = reverse("compras_ver_cotizaciones", args=[self.solicitud_cotizacion.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_usa_el_template_correcto(self):
        url = reverse("compras_ver_cotizaciones", args=[self.solicitud_cotizacion.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "compras/ver_cotizaciones.html")

    def test_muestra_las_cotizaciones_registradas(self):
        url = reverse("compras_ver_cotizaciones", args=[self.solicitud_cotizacion.pk])
        response = self.client.get(url)
        cotizaciones = response.context["cotizaciones"]
        self.assertEqual(cotizaciones.count(), 1)
        self.assertEqual(cotizaciones.first(), self.cotizacion)

    def test_lista_vacia_cuando_no_hay_cotizaciones(self):
        otra_solicitud = SolicitudCompra.objects.create(
            producto_codigo="123456", producto_nombre="Atun",
            cantidad_solicitada=10, estado=SolicitudCompra.ESTADO_SIN_STOCK,
        )
        otra_cotizacion_sol = SolicitudCotizacion.objects.create(solicitud_compra=otra_solicitud)
        url = reverse("compras_ver_cotizaciones", args=[otra_cotizacion_sol.pk])
        response = self.client.get(url)
        self.assertEqual(response.context["cotizaciones"].count(), 0)
        self.assertContains(response, "Todavía no hay cotizaciones registradas")

    def test_solicitud_cotizacion_inexistente_da_404(self):
        url = reverse("compras_ver_cotizaciones", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)