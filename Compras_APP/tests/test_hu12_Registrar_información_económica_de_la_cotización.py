# ============================================================
# COMINV-67 - HU-12: Registrar información económica de la cotización
# Integrante encargado: Luis Valarezo
# ============================================================
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from Compras_APP.models import Cotizacion, Proveedor, SolicitudCompra, SolicitudCotizacion


class RegistrarCotizacionTest(TestCase):
    """COMINV-67 - HU-12: Registrar información económica de la cotización."""

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
        self.url = reverse("compras_ver_cotizaciones", args=[self.solicitud_cotizacion.pk])

    def test_registrar_cotizacion_valida(self):
        response = self.client.post(self.url, {
            "proveedor": self.proveedor.pk,
            "precio_unitario": "2.75",
            "tiempo_entrega_dias": "7",
            "vigencia": (date.today() + timedelta(days=15)).isoformat(),
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Cotizacion.objects.count(), 1)

        cotizacion = Cotizacion.objects.first()
        self.assertEqual(cotizacion.proveedor, self.proveedor)
        self.assertEqual(str(cotizacion.precio_unitario), "2.75")
        self.assertEqual(cotizacion.tiempo_entrega_dias, 7)
        self.assertEqual(cotizacion.estado, Cotizacion.ESTADO_PENDIENTE)

    def test_no_registra_sin_tiempo_de_entrega(self):
        response = self.client.post(self.url, {
            "proveedor": self.proveedor.pk,
            "precio_unitario": "2.75",
            "tiempo_entrega_dias": "",
            "vigencia": (date.today() + timedelta(days=15)).isoformat(),
        })
        self.assertEqual(Cotizacion.objects.count(), 0)
        self.assertContains(response, "El tiempo de entrega es obligatorio")

    def test_no_registra_sin_vigencia(self):
        response = self.client.post(self.url, {
            "proveedor": self.proveedor.pk,
            "precio_unitario": "2.75",
            "tiempo_entrega_dias": "7",
            "vigencia": "",
        })
        self.assertEqual(Cotizacion.objects.count(), 0)
        self.assertContains(response, "La vigencia es obligatoria")

    def test_no_registra_sin_proveedor(self):
        response = self.client.post(self.url, {
            "proveedor": "",
            "precio_unitario": "2.75",
            "tiempo_entrega_dias": "7",
            "vigencia": (date.today() + timedelta(days=15)).isoformat(),
        })
        self.assertEqual(Cotizacion.objects.count(), 0)

    def test_registrar_varias_cotizaciones_del_mismo_proveedor(self):
        self.client.post(self.url, {
            "proveedor": self.proveedor.pk, "precio_unitario": "2.75",
            "tiempo_entrega_dias": "7", "vigencia": (date.today() + timedelta(days=15)).isoformat(),
        })
        self.client.post(self.url, {
            "proveedor": self.proveedor.pk, "precio_unitario": "3.00",
            "tiempo_entrega_dias": "10", "vigencia": (date.today() + timedelta(days=20)).isoformat(),
        })
        self.assertEqual(Cotizacion.objects.filter(proveedor=self.proveedor).count(), 2)