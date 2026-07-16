from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Devolucion, InspeccionPercha, MovimientoInventario


@receiver(post_save, sender=MovimientoInventario)
def movimiento_post_save(sender, instance, created, **kwargs):
    if created:
        print(f"[SEÑAL] Movimiento registrado: {instance.tipo} {instance.cantidad} {instance.producto.codigo}")


@receiver(post_save, sender=Devolucion)
def devolucion_post_save(sender, instance, created, **kwargs):
    if created:
        print(f"[SEÑAL] Devolución registrada: {instance.producto.codigo} cantidad {instance.cantidad}")


@receiver(post_save, sender=InspeccionPercha)
def inspeccion_post_save(sender, instance, created, **kwargs):
    if created:
        print(f"[SEÑAL] Inspección de percha registrada para {instance.producto.codigo}")
