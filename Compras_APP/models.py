from django.db import models
from django.contrib.auth.models import User

class SolicitudCompra(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('Aprobada', 'Aprobada'),
        ('Rechazada', 'Rechazada'),
    ]

    codigo = models.CharField(max_length=10, unique=True, editable=False)
    producto = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()
    descripcion = models.TextField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo_id = SolicitudCompra.objects.all().order_by('id').last()
            if not ultimo_id:
                self.codigo = 'SOL-0001'
            else:
                nuevo_id = ultimo_id.id + 1
                self.codigo = f'SOL-{nuevo_id:04d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.producto}"
