from django import forms
from .models import SolicitudCompra


class SolicitudCompraForm(forms.ModelForm):

    # ================================
    # Dev 1 - ST-2.1
    # Formulario de solicitud
    # ================================

    class Meta:

        model = SolicitudCompra

        fields = [
            "producto",
            "descripcion",
            "cantidad"
        ]

    # ================================
    # Dev 2 - ST-2.3
    # Validación de cantidad
    # ================================
    def clean_cantidad(self):

        cantidad = self.cleaned_data["cantidad"]

        if cantidad <= 0:
            raise forms.ValidationError(
                "La cantidad debe ser mayor a cero."
            )

        return cantidad

    # ================================
    # Dev 2 - ST-2.3
    # Validación de producto
    # ================================
    def clean_producto(self):

        producto = self.cleaned_data["producto"]

        if not producto.strip():
            raise forms.ValidationError(
                "Ingrese un producto."
            )

        return producto