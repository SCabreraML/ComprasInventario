from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from Compras_APP.models import Proveedor
from Compras_APP.forms import ProveedorForm

Usuario = get_user_model()


class RegistrarProveedorTests(TestCase):

    def setUp(self):
        # Usuario de prueba con permisos de administrador o compras
        self.user = Usuario.objects.create_user(
            username="admin", 
            password="password"
        )

    def test_registrar_proveedor_get(self):
        """Verifica que la página de registro cargue el formulario en blanco."""
        self.client.login(username="admin", password="password")
        response = self.client.get(reverse("registrar_proveedor"))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "compras/registrar_proveedor.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], ProveedorForm)

    def test_registrar_proveedor_post_exitoso(self):
        """Verifica que con datos válidos el proveedor se guarde y redirija."""
        self.client.login(username="admin", password="password")
        
        datos_proveedor = {
            "nombre": "Distribuidora Tech S.A.",
            "ruc": "1792345678001",
            "telefono": "0991234567",
            "correo": "contacto@distribuidoratech.com"
        }
        
        response = self.client.post(reverse("registrar_proveedor"), datos_proveedor)
        
        # Redirección tras guardado exitoso
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("compras_listado_proveedores"))
        
        # Confirmación en base de datos
        proveedor_creado = Proveedor.objects.filter(ruc="1792345678001").first()
        self.assertIsNotNone(proveedor_creado)
        self.assertEqual(proveedor_creado.nombre, "Distribuidora Tech S.A.")

    def test_registrar_proveedor_post_invalido(self):
        """Verifica que si faltan datos requeridos, el formulario re-renderice con errores."""
        self.client.login(username="admin", password="password")
        
        # Formulario enviado vacío o incompleto
        datos_invalidos = {
            "nombre": "",
            "ruc": ""
        }
        
        response = self.client.post(reverse("registrar_proveedor"), datos_invalidos)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)