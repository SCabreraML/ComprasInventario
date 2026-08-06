# ============================================================
# COMINV-72 - HU-17: Actualizar estado de las cotizaciones
# Integrante encargado: ______
# ============================================================
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from Compras_APP.models import Cotizacion, Proveedor, SolicitudCompra, SolicitudCotizacion


class ActualizarEstadoCotizacionesTest(TestCase):
    """COMINV-72 - HU-17: Actualizar estado de las cotizaciones."""

    def setUp(self):
        self.solicitud_compra = SolicitudCompra.objects.create(
            producto_codigo="789012", producto_nombre="Arroz",
            cantidad_solicitada=20, estado=SolicitudCompra.ESTADO_SIN_STOCK,
        )
        self.solicitud_cotizacion = SolicitudCotizacion.objects.create(
            solicitud_compra=self.solicitud_compra
        )
        self.proveedor_a = Proveedor.objects.create(nombre="Proveedor A")
        self.proveedor_b = Proveedor.objects.create(nombre="Proveedor B")
        self.solicitud_cotizacion.proveedores.add(self.proveedor_a, self.proveedor_b)

        self.cotizacion_a = Cotizacion.objects.create(
            solicitud_cotizacion=self.solicitud_cotizacion, proveedor=self.proveedor_a,
            precio_unitario=1.50, tiempo_entrega_dias=5, vigencia=date.today() + timedelta(days=30),
        )
        self.cotizacion_b = Cotizacion.objects.create(
            solicitud_cotizacion=self.solicitud_cotizacion, proveedor=self.proveedor_b,
            precio_unitario=1.80, tiempo_entrega_dias=3, vigencia=date.today() + timedelta(days=30),
        )

    def test_cotizacion_seleccionada_queda_aceptada(self):
        url = reverse("compras_seleccionar_ganadora", args=[self.cotizacion_a.pk])
        self.client.get(url)
        self.cotizacion_a.refresh_from_db()
        self.assertEqual(self.cotizacion_a.estado, Cotizacion.ESTADO_ACEPTADA)

    def test_las_demas_cotizaciones_quedan_rechazadas(self):
        url = reverse("compras_seleccionar_ganadora", args=[self.cotizacion_a.pk])
        self.client.get(url)
        self.cotizacion_b.refresh_from_db()
        self.assertEqual(self.cotizacion_b.estado, Cotizacion.ESTADO_RECHAZADA)

    def test_cotizacion_inexistente_da_404(self):
        url = reverse("compras_seleccionar_ganadora", args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)