from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class OrderCompra(TimeStampedModel):
    numero = models.CharField(max_length=50, unique=True)
    proveedor = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, choices=[("PENDIENTE", "Pendiente"), ("RECIBIDA", "Recibida"), ("CANCELADA", "Cancelada")], default="PENDIENTE")
    fecha_esperada = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return self.numero


class Producto(TimeStampedModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(max_length=100, blank=True)
    descripcion = models.TextField(blank=True)
    stock_bodega = models.PositiveIntegerField(default=0)
    stock_percha = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    usuario_registro = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="productos_registrados")

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def stock_total(self):
        return self.stock_bodega + self.stock_percha


class Lote(TimeStampedModel):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="lotes")
    numero_lote = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField(default=0)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    ubicacion = models.ForeignKey("inventory.UbicacionBodega", on_delete=models.SET_NULL, null=True, blank=True, related_name="lotes")
    estado = models.CharField(max_length=20, choices=[("DISPONIBLE", "Disponible"), ("VENCIDO", "Vencido"), ("DEVUELTO", "Devuelto"), ("CONSUMIDO", "Consumido")], default="DISPONIBLE")

    class Meta:
        unique_together = ("producto", "numero_lote")

    def __str__(self):
        return f"{self.producto.codigo} - Lote {self.numero_lote}"


class UbicacionBodega(TimeStampedModel):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    capacidad = models.PositiveIntegerField(default=0)
    ocupada = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.nombre


class MovimientoInventario(TimeStampedModel):
    TIPO_ENTRADA = "ENTRADA"
    TIPO_SALIDA = "SALIDA"
    TIPO_CHOICES = [(TIPO_ENTRADA, "Entrada"), (TIPO_SALIDA, "Salida")]

    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos")
    cantidad = models.PositiveIntegerField()
    motivo = models.CharField(max_length=200, blank=True)
    referencia = models.CharField(max_length=200, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="movimientos_registrados")
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.codigo} - {self.cantidad}"


class Devolucion(TimeStampedModel):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="devoluciones")
    lote = models.ForeignKey(Lote, on_delete=models.SET_NULL, null=True, blank=True, related_name="devoluciones")
    cantidad = models.PositiveIntegerField()
    motivo = models.CharField(max_length=200)
    evidencia = models.URLField(blank=True)
    estado = models.CharField(max_length=20, choices=[("PENDIENTE", "Pendiente"), ("PROCESADA", "Procesada"), ("RECHAZADA", "Rechazada")], default="PENDIENTE")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="devoluciones_registradas")
    fecha_devolucion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Devolución {self.id} - {self.producto.codigo}"


class InspeccionPercha(TimeStampedModel):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="inspecciones_percha")
    observaciones = models.TextField(blank=True)
    sin_novedades = models.BooleanField(default=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="inspecciones_realizadas")
    fecha_inspeccion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Inspección {self.id} - {self.producto.codigo}"
