# ============================================================
# COMINV-73 - HU-18: Generar Orden de Compra
# Integrante encargado: ______
# ============================================================
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from Compras_APP.models import Cotizacion, OrdenCompra, Proveedor, SolicitudCompra, SolicitudCotizacion


class GenerarOrdenCompraTest(TestCase):
    """COMINV-73 - HU-18: Generar Orden de Compra."""

    def setUp(self):
        self.solicitud_compra = SolicitudCompra.objects.create(
            producto_codigo="789012", producto_nombre="Arroz",
            cantidad_solicitada=20, estado=SolicitudCompra.ESTADO_SIN_STOCK,
        )
        self.solicitud_cotizacion = SolicitudCotizacion.objects.create(
            solicitud_compra=self.solicitud_compra
        )
        self.proveedor = Proveedor.objects.create(nombre="Proveedor Uno")
        self.solicitud_cotizacion.proveedores.add(self.proveedor)
        self.cotizacion = Cotizacion.objects.create(
            solicitud_cotizacion=self.solicitud_cotizacion, proveedor=self.proveedor,
            precio_unitario=Decimal("2.50"), tiempo_entrega_dias=5,
            vigencia=date.today() + timedelta(days=30),
        )
        self.url = reverse("compras_seleccionar_ganadora", args=[self.cotizacion.pk])

    def test_genera_una_orden_de_compra(self):
        self.client.get(self.url)
        self.assertEqual(OrdenCompra.objects.count(), 1)

    def test_orden_referencia_la_cotizacion_ganadora(self):
        self.client.get(self.url)
        orden = OrdenCompra.objects.first()
        self.assertEqual(orden.cotizacion_ganadora, self.cotizacion)

    def test_costo_total_correcto(self):
        self.client.get(self.url)
        orden = OrdenCompra.objects.first()
        # 20 unidades x $2.50 = $50.00
        self.assertEqual(orden.costo_total, Decimal("50.00"))

    def test_numero_de_orden_se_genera_automaticamente(self):
        self.client.get(self.url)
        orden = OrdenCompra.objects.first()
        self.assertTrue(orden.numero_orden.startswith("OC-"))

    def test_redirige_a_ver_orden(self):
        response = self.client.get(self.url)
        orden = OrdenCompra.objects.first()
        self.assertRedirects(response, reverse("compras_ver_orden", args=[orden.pk]))