from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Producto
from .services import InventoryService


class InventoryServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester", password="12345")

    def test_registrar_entrada_actualiza_stock(self):
        producto = Producto.objects.create(codigo="P001", nombre="Arroz", stock_bodega=5, stock_minimo=2, usuario_registro=self.user)
        InventoryService.registrar_recepcion(None, producto, 3, self.user)
        producto.refresh_from_db()
        self.assertEqual(producto.stock_bodega, 8)

    def test_movimiento_salida_bloquea_stock_negativo(self):
        producto = Producto.objects.create(codigo="P002", nombre="Azucar", stock_bodega=2, stock_minimo=1, usuario_registro=self.user)
        with self.assertRaises(Exception):
            InventoryService.registrar_movimiento(producto, 3, "SALIDA", self.user, motivo="Prueba")


class InventoryAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="tester_api", password="12345")
        self.producto = Producto.objects.create(
            codigo="P999",
            nombre="Galletas de Chocolate",
            stock_bodega=15,
            stock_percha=5,
            stock_minimo=5,
            usuario_registro=self.user
        )

    def test_api_consultar_existencias_by_code(self):
        response = self.client.get("/api/existencias/", {"producto": "P999"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["producto"]["codigo"], "P999")
        self.assertEqual(data["producto"]["nombre"], "Galletas de Chocolate")
        self.assertEqual(data["producto"]["stock_bodega"], 15)
        self.assertEqual(data["producto"]["stock_percha"], 5)
        self.assertEqual(data["producto"]["stock_total"], 20)

    def test_api_consultar_existencias_by_name(self):
        # Case insensitive check
        response = self.client.get("/api/existencias/", {"producto": "galletas de chocolate"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["producto"]["codigo"], "P999")

    def test_api_consultar_existencias_missing_param(self):
        response = self.client.get("/api/existencias/")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["status"], "error")

    def test_api_consultar_existencias_not_found(self):
        response = self.client.get("/api/existencias/", {"producto": "NON_EXISTENT"})
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data["status"], "not_found")
