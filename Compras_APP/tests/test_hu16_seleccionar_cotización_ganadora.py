import pytest
from django.urls import reverse
from Compras_APP.models import (
    SolicitudCompra,
    SolicitudCotizacion,
    Cotizacion,
)


# Sprint 4 HU-16: Seleccionar cotización ganadora
@pytest.mark.django_db
class TestHU16SeleccionarCotizacionGanadora:

    @pytest.fixture
    def cotizacion(self):
        """Fixture para crear la cotización de prueba."""
        solicitud_compra = SolicitudCompra.objects.create(
            cantidad_solicitada=1,
            # Agrega campos obligatorios si el modelo los requiere
        )
        solicitud_cotizacion = SolicitudCotizacion.objects.create(
            solicitud_compra=solicitud_compra
        )
        return Cotizacion.objects.create(
            solicitud_cotizacion=solicitud_cotizacion,
            precio_unitario=100.00,
        )

    def test_hu16_seleccionar_cotizacion_ganadora_exitoso(self, client, cotizacion):
        """HU-16: Verifica que la petición para seleccionar la cotización ganadora responda correctamente."""
        url = reverse("seleccionar_ganadora", kwargs={"pk": cotizacion.pk})
        
        # Ejecutamos la petición
        response = client.get(url)  # Usa client.post(url) si tu vista requiere POST

        # Verifica que la acción no falle y procese la redirección esperada
        assert response.status_code == 302

    def test_hu16_seleccionar_cotizacion_no_existente_retorna_404(self, client):
        """HU-16: Verifica que si la cotización no existe devuelva error 404."""
        url = reverse("seleccionar_ganadora", kwargs={"pk": 9999})
        response = client.get(url)

        assert response.status_code == 404