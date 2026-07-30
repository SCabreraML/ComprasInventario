from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from Compras_APP.models import SolicitudCompra
import unittest
from unittest.mock import patch

Usuario = get_user_model()


class ComprasAPPTests(TestCase):
    def setUp(self):
        # Create groups
        self.admin_group = Group.objects.create(name="Administrador")
        self.compras_group = Group.objects.create(name="Encargado de Compras")

        # Create users
        self.admin_user = Usuario.objects.create_user(username="admin", password="password")
        self.admin_user.groups.add(self.admin_group)

        self.compras_user = Usuario.objects.create_user(username="compras", password="password")
        self.compras_user.groups.add(self.compras_group)

        self.solicitante_user = Usuario.objects.create_user(username="solicitante", password="password")

        # Create some test requests
        self.sol1 = SolicitudCompra.objects.create(
            producto="P-101",
            cantidad=10,
            solicitante=self.solicitante_user,
            descripcion="Falta stock en bodega"
        )
        self.sol2 = SolicitudCompra.objects.create(
            producto="P-102",
            cantidad=50,
            solicitante=self.solicitante_user,
            descripcion="Para perchas"
        )

    def test_crear_solicitud(self):
        self.client.login(username="solicitante", password="password")
        response = self.client.post(reverse("crear_solicitud"), {
            "producto": "P-103",
            "cantidad": 5,
            "descripcion": "Nueva solicitud de prueba"
        })
        self.assertEqual(response.status_code, 302) # Redirects to list
        solicitudes = SolicitudCompra.objects.filter(producto="P-103")
        self.assertTrue(solicitudes.exists())
        self.assertEqual(solicitudes.first().solicitante, self.solicitante_user)

    def test_crear_solicitud_invalid_cantidad(self):
        self.client.login(username="solicitante", password="password")
        response = self.client.post(reverse("crear_solicitud"), {
            "producto": "P-103",
            "cantidad": 0,
            "descripcion": "Nueva solicitud de prueba"
        })
        self.assertEqual(response.status_code, 200) # Form errors
        self.assertFalse(SolicitudCompra.objects.filter(producto="P-103").exists())

    @patch("Compras_APP.utils.consultar_existencias_api")
    def test_lista_solicitudes_disponibilidad_suficiente(self, mock_consultar):
        # Mock product stock to be 20 for product P-101 (sol1 requests 10, which is <= 20, so "Suficiente")
        # Mock product stock to be 30 for product P-102 (sol2 requests 50, which is > 30, so "Insuficiente")
        def side_effect(producto_identificador):
            if producto_identificador == "P-101":
                return {"stock_total": 20, "stock_bodega": 10, "stock_percha": 10}
            if producto_identificador == "P-102":
                return {"stock_total": 30, "stock_bodega": 20, "stock_percha": 10}
            return None
        mock_consultar.side_effect = side_effect

        self.client.login(username="admin", password="password")
        response = self.client.get(reverse("lista_solicitudes"))
        self.assertEqual(response.status_code, 200)

        # Verify from view logic context
        solicitudes_list = response.context["solicitudes"]
        sol1_fetched = next(s for s in solicitudes_list if s.id == self.sol1.id)
        sol2_fetched = next(s for s in solicitudes_list if s.id == self.sol2.id)

        self.assertEqual(sol1_fetched.stock_logistica, 20)
        self.assertEqual(sol1_fetched.disponibilidad, "Suficiente")
        self.assertTrue(sol1_fetched.producto_existe)

        self.assertEqual(sol2_fetched.stock_logistica, 30)
        self.assertEqual(sol2_fetched.disponibilidad, "Insuficiente")
        self.assertTrue(sol2_fetched.producto_existe)

    @patch("Compras_APP.utils.consultar_existencias_api")
    def test_lista_solicitudes_disponibilidad_no_encontrado(self, mock_consultar):
        mock_consultar.return_value = None

        self.client.login(username="admin", password="password")
        response = self.client.get(reverse("lista_solicitudes"))
        self.assertEqual(response.status_code, 200)

        solicitudes_list = response.context["solicitudes"]
        sol1_fetched = next(s for s in solicitudes_list if s.id == self.sol1.id)

        self.assertEqual(sol1_fetched.stock_logistica, 0)
        self.assertEqual(sol1_fetched.disponibilidad, "No encontrado en Logística")
        self.assertFalse(sol1_fetched.producto_existe)

    def test_aprobar_solicitud(self):
        self.client.login(username="admin", password="password")
        response = self.client.get(reverse("aprobar_solicitud", args=[self.sol1.id]))
        self.assertEqual(response.status_code, 302) # Redirects to list
        self.sol1.refresh_from_db()
        self.assertEqual(self.sol1.estado, SolicitudCompra.ESTADO_APROBADA)

    def test_rechazar_solicitud_con_justificacion(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(reverse("rechazar_solicitud", args=[self.sol1.id]), {
            "justificacion": "No hay presupuesto para este producto en este trimestre."
        })
        self.assertEqual(response.status_code, 302) # Redirects to list
        self.sol1.refresh_from_db()
        self.assertEqual(self.sol1.estado, SolicitudCompra.ESTADO_RECHAZADA)
        self.assertEqual(self.sol1.justificacion, "No hay presupuesto para este producto en este trimestre.")

    def test_rechazar_solicitud_sin_justificacion(self):
        self.client.login(username="admin", password="password")
        response = self.client.post(reverse("rechazar_solicitud", args=[self.sol1.id]), {
            "justificacion": ""
        })
        self.assertEqual(response.status_code, 200) # Returns to page showing error
        self.sol1.refresh_from_db()
        self.assertEqual(self.sol1.estado, SolicitudCompra.ESTADO_PENDIENTE)
        self.assertEqual(self.sol1.justificacion, "")


class CotizacionesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="test_user", password="password")
        self.solicitud = SolicitudCompra.objects.create(
            producto="P-101",
            cantidad=10,
            solicitante=self.user,
            descripcion="Falta stock en bodega"
        )

    def test_registrar_cotizacion_valido(self):
        # HU-13: Registrar tiempo de entrega (tiempo_entrega = 5)
        # HU-14: Asociar proveedor con la cotización (proveedor = "Proveedor S.A.")
        # HU-12: Registrar información económica (precio_unitario, vigencia)
        self.client.login(username="test_user", password="password")
        response = self.client.post(reverse("registrar_cotizacion", args=[self.solicitud.id]), {
            "proveedor": "Proveedor S.A.",
            "precio_unitario": "15.50",
            "vigencia": "2026-12-31",
            "tiempo_entrega": 5
        })
        self.assertEqual(response.status_code, 302) # Redirects to cotizaciones list

        # Verify the database contains the registered quote
        from Compras_APP.models import Cotizacion
        cotizaciones = Cotizacion.objects.filter(solicitud=self.solicitud)
        self.assertEqual(cotizaciones.count(), 1)
        cot = cotizaciones.first()
        self.assertEqual(cot.proveedor, "Proveedor S.A.") # HU-14: Asociar proveedor
        self.assertEqual(cot.tiempo_entrega, 5) # HU-13: Registrar tiempo de entrega

    def test_registrar_cotizacion_tiempo_entrega_obligatorio(self):
        # HU-13: El tiempo de entrega es obligatorio y debe validarse en el formulario.
        self.client.login(username="test_user", password="password")
        response = self.client.post(reverse("registrar_cotizacion", args=[self.solicitud.id]), {
            "proveedor": "Proveedor S.A.",
            "precio_unitario": "15.50",
            "vigencia": "2026-12-31",
            "tiempo_entrega": "" # Missing delivery time
        })
        self.assertEqual(response.status_code, 200) # Form returns invalid

        from Compras_APP.models import Cotizacion
        self.assertFalse(Cotizacion.objects.filter(solicitud=self.solicitud).exists())

    def test_registrar_cotizacion_proveedor_obligatorio(self):
        # HU-14: El proveedor es obligatorio para asociarlo.
        self.client.login(username="test_user", password="password")
        response = self.client.post(reverse("registrar_cotizacion", args=[self.solicitud.id]), {
            "proveedor": "", # Missing proveedor
            "precio_unitario": "15.50",
            "vigencia": "2026-12-31",
            "tiempo_entrega": 5
        })
        self.assertEqual(response.status_code, 200) # Form returns invalid

        from Compras_APP.models import Cotizacion
        self.assertFalse(Cotizacion.objects.filter(solicitud=self.solicitud).exists())

    def test_lista_cotizaciones_consultar(self):
        # HU-11: Consultar cotizaciones registradas
        from Compras_APP.models import Cotizacion
        cot1 = Cotizacion.objects.create(
            solicitud=self.solicitud,
            proveedor="Proveedor A",
            precio_unitario="10.00",
            vigencia="2026-12-31",
            tiempo_entrega=3
        )
        cot2 = Cotizacion.objects.create(
            solicitud=self.solicitud,
            proveedor="Proveedor B",
            precio_unitario="12.00",
            vigencia="2026-12-31",
            tiempo_entrega=5
        )

        self.client.login(username="test_user", password="password")
        response = self.client.get(reverse("lista_cotizaciones", args=[self.solicitud.id]))
        self.assertEqual(response.status_code, 200)

        # Verify the context has the list of registered quotes
        cots_list = list(response.context["cotizaciones"])
        self.assertEqual(len(cots_list), 2)
        self.assertIn(cot1, cots_list)
        self.assertIn(cot2, cots_list)