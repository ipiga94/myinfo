__author__ = 'hhauer'

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

import cx_Oracle
from MyInfo.models import ContactInformation


class Command(BaseCommand):
    def get_iiq_url(self, udc_id):
        url = "https://{}/identityiq/rest/custom/getUUID/{}".format(settings.SAILPOINT_SERVER_URL, udc_id)
        return url

    def handle(self, *args, **options):
        # Get banner connection settings.
        banner = settings.ORACLE_MANAGEMENT['banner']

        oracle_dsn = cx_Oracle.makedsn(banner['HOST'], banner['PORT'], banner['SID'])
        oracle_connection = cx_Oracle.Connection(banner['USER'], banner['PASS'], oracle_dsn)
        oracle_cursor = oracle_connection.cursor()

        oracle_cursor.execute(settings.ORACLE_MANAGEMENT['password_reset']['SQL'])

        for record in oracle_cursor:
            # UDC_ID, Phone, Email. Phone or email can be None.
            r = requests.get(
                self.get_iiq_url(record[0]),
                auth=(settings.SAILPOINT_USERNAME, settings.SAILPOINT_PASSWORD),
                verify=False
            )

            psu_uuid = r.json()

            try:
                if psu_uuid is None or psu_uuid == "None":
                    self.stdout.write("No PSU_UUID was available for UDC_ID: " + record[0])
                else:
                    obj, created = ContactInformation.objects.update_or_create(
                        psu_uuid=psu_uuid,
                        cell_phone=record[1],
                        alternate_email=record[2],
                    )

                    obj.save()

                    update_or_create = "Updated"
                    if created:
                        update_or_create = "Created"

                    self.stdout.write(update_or_create + " record for: " + psu_uuid)
            except:
                self.stdout.write("There was an exception for: " + psu_uuid)
                if record[1] is not None:
                    self.stdout.write("Cell Phone was: " + record[1])
                if record[2] is not None:
                    self.stdout.write("Email was: " + record[2])

