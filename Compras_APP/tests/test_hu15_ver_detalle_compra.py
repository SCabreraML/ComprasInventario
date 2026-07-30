import pytest
from django.urls import reverse
from Compras_APP.models import OrdenCompra


# HU-15: Visualización de Detalle de Orden de Compra
@pytest.mark.django_db
class TestHU15VisualizacionDetalleOrdenCompra:

    @pytest.fixture
    def orden_compra(self):
        """Fixture para crear una orden de compra de prueba."""
        return OrdenCompra.objects.create(
            # se agrega aquí los campos obligatorios de tu modelo OrdenCompra
        )

    def test_hu15_ver_orden_exitosa(self, client, orden_compra):
        """HU-15: Verifica que la vista retorne la orden y el template correcto."""
        url = reverse("ver_orden", kwargs={"pk": orden_compra.pk})
        response = client.get(url)

        assert response.status_code == 200
        assert "compras/ver_orden.html" in [t.name for t in response.templates]
        assert "orden" in response.context
        assert response.context["orden"] == orden_compra

    def test_hu15_ver_orden_no_existente_retorna_404(self, client):
        """HU-15: Verifica que si la orden no existe retorne un error 404."""
        url = reverse("ver_orden", kwargs={"pk": 9999})  # ID inexistente
        response = client.get(url)

        assert response.status_code == 404