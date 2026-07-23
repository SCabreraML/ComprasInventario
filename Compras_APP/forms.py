from django import forms
from .models import SolicitudCompra
from .models import Cotizacion, Proveedor, SolicitudCotizacion

class SolicitudCompraForm(forms.ModelForm):

    # Dev 1 - ST-2.1
    # Formulario de solicitud

    class Meta:

        model = SolicitudCompra

        fields = [
            "producto",
            "descripcion",
            "cantidad"
        ]


    # Dev 2 - ST-2.3
    # Validación de cantidad
    def clean_cantidad(self):

        cantidad = self.cleaned_data["cantidad"]

        if cantidad <= 0:
            raise forms.ValidationError(
                "La cantidad debe ser mayor a cero."
            )

        return cantidad

  
    # Dev 2 - ST-2.3
    # Validación de producto

    def clean_producto(self):

        producto = self.cleaned_data["producto"]

        if not producto.strip():
            raise forms.ValidationError(
                "Ingrese un producto."
            )

        return producto

    #sprint 4 
    # HU-09: Registrar proveedores
class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "ruc", "telefono", "correo"]

    #hu-10: Registrar solicitud de cotización
class SolicitudCotizacionForm(forms.ModelForm):
    class Meta:
        model = SolicitudCotizacion
        fields = ["proveedores"]
        widgets = {
            "proveedores": forms.CheckboxSelectMultiple(),  # ST-4.3: elegir uno o varios
        }
