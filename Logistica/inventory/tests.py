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
