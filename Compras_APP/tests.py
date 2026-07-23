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
