from django import forms
from .models import SolicitudCompra


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


from .models import Cotizacion

class CotizacionForm(forms.ModelForm):
    # HU-13: Registrar tiempo de entrega
    # HU-14: Asociar proveedor con la cotización
    class Meta:
        model = Cotizacion
        fields = [
            "proveedor",
            "precio_unitario",
            "vigencia",
            "tiempo_entrega"
        ]
        widgets = {
            "vigencia": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "proveedor": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del proveedor"}),
            "precio_unitario": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "0.00"}),
            "tiempo_entrega": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Tiempo estimado en días"}),
        }

    # HU-14: Asociar proveedor con la cotización
    def clean_proveedor(self):
        proveedor = self.cleaned_data.get("proveedor")
        if not proveedor or not proveedor.strip():
            raise forms.ValidationError("El proveedor es obligatorio.")
        return proveedor

    # HU-13: Registrar tiempo de entrega (el dato es obligatorio)
    def clean_tiempo_entrega(self):
        tiempo = self.cleaned_data.get("tiempo_entrega")
        if tiempo is None or tiempo <= 0:
            raise forms.ValidationError("El tiempo de entrega es obligatorio y debe ser mayor a cero.")
        return tiempo

    def clean_precio_unitario(self):
        precio = self.cleaned_data.get("precio_unitario")
        if precio is None or precio <= 0:
            raise forms.ValidationError("El precio unitario debe ser mayor a cero.")
        return precio


from .models import Proveedor

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ["nombre", "ruc", "telefono", "correo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del Proveedor"}),
            "ruc": forms.TextInput(attrs={"class": "form-control", "placeholder": "RUC (13 dígitos)"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono de contacto"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
        }

    def clean_ruc(self):
        ruc = self.cleaned_data.get("ruc")
        if len(ruc) != 13:
            raise forms.ValidationError("El RUC debe tener exactamente 13 dígitos.")
        return ruc


class SolicitudCotizacionForm(forms.Form):
    proveedores = forms.ModelMultipleChoiceField(
        queryset=Proveedor.objects.all(),
        widget=forms.CheckboxSelectMultiple
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3, "class": "form-control"})
    )