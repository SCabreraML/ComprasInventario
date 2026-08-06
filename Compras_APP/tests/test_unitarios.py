from django.test import TestCase
from decimal import Decimal
import datetime
from django.contrib.auth import get_user_model
from Compras_APP.models import SolicitudCompra, Cotizacion, OrdenCompra, Proveedor
from Compras_APP.forms import SolicitudCompraForm, CotizacionForm, ProveedorForm

Usuario = get_user_model()


class UnitariosTests(TestCase):
    """
    Colección de exactamente 12 Pruebas Unitarias para Modelos y Formularios
    """

    def setUp(self):
        self.user = Usuario.objects.create_user(username="user_test", password="password")

    # --- PRUEBAS UNITARIAS DE MODELOS (6 PRUEBAS) ---

    def test_1_solicitud_compra_codigo_automatico(self):
        """1. Verifica que SolicitudCompra genere un código automáticamente en el save."""
        solicitud = SolicitudCompra.objects.create(
            producto="Monitor UltraWide 34",
            cantidad=2,
            solicitante=self.user,
            descripcion="Monitor para diseño"
        )
        self.assertTrue(solicitud.codigo.startswith("SOL-"))
        self.assertEqual(len(solicitud.codigo), 12)  # SOL- + 8 hex chars

    def test_2_solicitud_compra_str(self):
        """2. Verifica que SolicitudCompra.__str__ devuelva el código generado."""
        solicitud = SolicitudCompra.objects.create(
            producto="Monitor UltraWide 34",
            cantidad=2,
            solicitante=self.user
        )
        self.assertEqual(str(solicitud), solicitud.codigo)

    def test_3_cotizacion_str(self):
        """3. Verifica que Cotizacion.__str__ contenga el proveedor y el código de solicitud."""
        solicitud = SolicitudCompra.objects.create(
            producto="Impresora Láser",
            cantidad=1,
            solicitante=self.user
        )
        cotizacion = Cotizacion.objects.create(
            solicitud=solicitud,
            proveedor="Epson Inc",
            precio_unitario=Decimal("250.00"),
            vigencia=datetime.date.today(),
            tiempo_entrega=3
        )
        self.assertIn("Epson Inc", str(cotizacion))
        self.assertIn(solicitud.codigo, str(cotizacion))

    def test_4_orden_compra_calcula_costo_total(self):
        """4. Verifica que OrdenCompra calcule automáticamente costo_total = cantidad * precio_unitario."""
        solicitud = SolicitudCompra.objects.create(
            producto="Teclado Mecánico",
            cantidad=5,
            solicitante=self.user
        )
        cotizacion = Cotizacion.objects.create(
            solicitud=solicitud,
            proveedor="Logitech",
            precio_unitario=Decimal("80.00"),
            vigencia=datetime.date.today(),
            tiempo_entrega=2
        )
        orden = OrdenCompra.objects.create(cotizacion=cotizacion)
        self.assertEqual(orden.costo_total, Decimal("400.00"))  # 5 * 80.00

    def test_5_orden_compra_str(self):
        """5. Verifica que OrdenCompra.__str__ devuelva el formato 'OC-<id>'."""
        solicitud = SolicitudCompra.objects.create(
            producto="Mouse Gamer",
            cantidad=1,
            solicitante=self.user
        )
        cotizacion = Cotizacion.objects.create(
            solicitud=solicitud,
            proveedor="Razer",
            precio_unitario=Decimal("50.00"),
            vigencia=datetime.date.today(),
            tiempo_entrega=1
        )
        orden = OrdenCompra.objects.create(cotizacion=cotizacion)
        self.assertEqual(str(orden), f"OC-{orden.id}")

    def test_6_proveedor_str(self):
        """6. Verifica que Proveedor.__str__ devuelva el nombre del proveedor."""
        proveedor = Proveedor.objects.create(
            nombre="Intel Corporation",
            ruc="1791122334001",
            telefono="0999999999",
            correo="info@intel.com"
        )
        self.assertEqual(str(proveedor), "Intel Corporation")

    # --- PRUEBAS UNITARIAS DE FORMULARIOS (6 PRUEBAS) ---

    def test_7_solicitud_compra_form_valida(self):
        """7. Verifica que SolicitudCompraForm sea válido con datos correctos."""
        form = SolicitudCompraForm(data={
            "producto": "Escritorio de Madera",
            "cantidad": 3,
            "descripcion": "Escritorios para la oficina"
        })
        self.assertTrue(form.is_valid())

    def test_8_solicitud_compra_form_invalida_cantidad(self):
        """8. Verifica que SolicitudCompraForm invalide cantidades menores o iguales a cero."""
        form = SolicitudCompraForm(data={
            "producto": "Escritorio de Madera",
            "cantidad": 0
        })
        self.assertFalse(form.is_valid())
        self.assertIn("La cantidad debe ser mayor a cero.", form.errors["cantidad"])

    def test_9_solicitud_compra_form_invalida_producto(self):
        """9. Invalida producto vacío en SolicitudCompraForm."""
        form = SolicitudCompraForm(data={
            "producto": "",
            "cantidad": 5
        })
        self.assertFalse(form.is_valid())
        self.assertIn("producto", form.errors)

    def test_10_proveedor_form_valida(self):
        """10. Verifica que ProveedorForm sea válido con datos correctos."""
        form = ProveedorForm(data={
            "nombre": "Distribuidora Dell",
            "ruc": "1792345678001",
            "telefono": "022345678",
            "correo": "ventas@dell.ec"
        })
        self.assertTrue(form.is_valid())

    def test_11_proveedor_form_invalido_ruc(self):
        """11. Verifica que ProveedorForm requiera exactamente 13 dígitos para el RUC."""
        form = ProveedorForm(data={
            "nombre": "Distribuidora Dell",
            "ruc": "12345",  # RUC muy corto
            "telefono": "022345678",
            "correo": "ventas@dell.ec"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("ruc", form.errors)
        self.assertIn("El RUC debe tener exactamente 13 dígitos.", form.errors["ruc"])

    def test_12_cotizacion_form_invalido_precio(self):
        """12. Verifica que CotizacionForm requiera un precio unitario mayor a cero."""
        form = CotizacionForm(data={
            "proveedor": "Proveedor S.A.",
            "precio_unitario": "0.00",
            "vigencia": "2026-12-31",
            "tiempo_entrega": 5
        })
        self.assertFalse(form.is_valid())
        self.assertIn("precio_unitario", form.errors)
        self.assertIn("El precio unitario debe ser mayor a cero.", form.errors["precio_unitario"])
