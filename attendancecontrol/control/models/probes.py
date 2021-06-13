# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from macaddress.fields import MACAddressField

from .users import WifiInfo


class ProbeRequest(models.Model):      # pragma: no cover
    # id = models.IntegerField(primary_key=True)
    time = models.DateTimeField(blank=True, null=True)
    mac_addr = models.ForeignKey(WifiInfo, on_delete=models.PROTECT, null=True)
    mac = MACAddressField(null=True, blank=True, integer=False)
    vendor = models.CharField(max_length=200, blank=True, null=True)
    ssid = models.CharField(max_length=200, blank=True, null=True)
    rssi = models.IntegerField(blank=True, null=True)
    raw = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'probe_requests'

    def __str__(self):
        return (
            f"{self.time.isoformat()}: "
            f"mac: {self.mac}, "
        )
