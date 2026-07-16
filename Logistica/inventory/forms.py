from django import forms

from .models import Lote, OrderCompra, Producto


class ProductoSearchForm(forms.Form):
    q = forms.CharField(label="Buscar", required=False)
    categoria = forms.CharField(label="Categoría", required=False)


class RecepcionForm(forms.Form):
    order_compra = forms.ModelChoiceField(queryset=OrderCompra.objects.all(), required=False, label="Orden de compra")
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), label="Producto")
    cantidad = forms.IntegerField(min_value=1, label="Cantidad")
    lote_numero = forms.CharField(required=False, label="Número de lote")
    ubicacion = forms.ModelChoiceField(queryset=Lote.objects.none(), required=False, label="Ubicación")
    documento = forms.CharField(required=False, label="Documento de recepción")
    conformidad = forms.BooleanField(required=False, initial=True, label="Productos conformes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import UbicacionBodega
        self.fields["ubicacion"].queryset = UbicacionBodega.objects.all()


class MovimientoForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), label="Producto")
    tipo = forms.ChoiceField(choices=[("ENTRADA", "Entrada"), ("SALIDA", "Salida")], label="Tipo de movimiento")
    cantidad = forms.IntegerField(min_value=1, label="Cantidad")
    motivo = forms.CharField(required=True, label="Motivo")
    referencia = forms.CharField(required=False, label="Referencia")
    lote = forms.ModelChoiceField(queryset=Lote.objects.all(), required=False, label="Lote")


class DevolucionForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), label="Producto")
    cantidad = forms.IntegerField(min_value=1, label="Cantidad")
    motivo = forms.CharField(required=True, label="Novedad detectada")
    evidencia = forms.URLField(required=False, label="Evidencia (URL)")
    lote = forms.ModelChoiceField(queryset=Lote.objects.all(), required=False, label="Lote")


class InspeccionPerchaForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), label="Producto")
    observaciones = forms.CharField(widget=forms.Textarea, required=False, label="Observaciones")
    sin_novedades = forms.BooleanField(required=False, initial=True, label="Sin novedades")


class ReponerPerchaForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.filter(activo=True), label="Producto")
    cantidad = forms.IntegerField(min_value=1, label="Cantidad a reponer")
