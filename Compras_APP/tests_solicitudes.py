from django.test import TestCase
from django.contrib.auth.models import User, Group
from .models import SolicitudCompra
from django.urls import reverse

class SolicitudCompraTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')

    def test_creacion_solicitud_y_codigo_automatico(self):
        solicitud1 = SolicitudCompra.objects.create(
            producto="Teclado",
            cantidad=5,
            usuario=self.user
        )
        self.assertEqual(solicitud1.codigo, "SOL-0001")

        solicitud2 = SolicitudCompra.objects.create(
            producto="Mouse",
            cantidad=10,
            usuario=self.user
        )
        self.assertEqual(solicitud2.codigo, "SOL-0002")

    def test_validacion_cantidad_mayor_a_cero(self):
        response = self.client.post(reverse('crear_solicitud'), {
            'producto': 'Monitor',
            'cantidad': 0,
            'descripcion': 'Test'
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('cantidad', form.errors)

    def test_registro_exitoso(self):
        response = self.client.post(reverse('crear_solicitud'), {
            'producto': 'Monitor',
            'cantidad': 2,
            'descripcion': 'Test'
        })
        self.assertRedirects(response, reverse('lista_solicitudes'))
        self.assertEqual(SolicitudCompra.objects.count(), 1)
        solicitud = SolicitudCompra.objects.first()
        self.assertEqual(solicitud.producto, 'Monitor')
        self.assertEqual(solicitud.cantidad, 2)
        self.assertEqual(solicitud.usuario, self.user)
        self.assertEqual(solicitud.estado, 'Pendiente')

    def test_edicion_solicitud_pendiente(self):
        solicitud = SolicitudCompra.objects.create(
            producto="Teclado",
            cantidad=5,
            usuario=self.user
        )
        response = self.client.post(reverse('editar_solicitud', args=[solicitud.id]), {
            'producto': 'Teclado Mecanico',
            'cantidad': 3,
            'descripcion': 'Updated'
        })
        self.assertRedirects(response, reverse('lista_solicitudes'))
        solicitud.refresh_from_db()
        self.assertEqual(solicitud.producto, 'Teclado Mecanico')
        self.assertEqual(solicitud.cantidad, 3)

    def test_no_editar_solicitud_aprobada(self):
        solicitud = SolicitudCompra.objects.create(
            producto="Teclado",
            cantidad=5,
            usuario=self.user,
            estado='Aprobada'
        )
        response = self.client.post(reverse('editar_solicitud', args=[solicitud.id]), {
            'producto': 'Teclado Mecanico',
            'cantidad': 3,
            'descripcion': 'Updated'
        })
        self.assertEqual(response.status_code, 403)
