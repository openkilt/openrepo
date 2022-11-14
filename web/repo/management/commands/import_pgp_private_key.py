from django.core.management.base import BaseCommand, CommandError
from repo.models import PGPSigningKey
import gnupg
import os

class Command(BaseCommand):
    help = 'Ensures that all PGP keys in database are added to local keychain'

    def add_arguments(self, parser):
        parser.add_argument('private_key_path', type=str, help='Path to GPG private key stored in PEM format')

    def handle(self, *args, **options):

        if not os.path.isfile(options['private_key_path']):
            self.stdout.write(f"Cannot find file {options['private_key_path']}")
            return

        gpg = gnupg.GPG()
        gpg.encoding = 'utf-8'

        import_result = gpg.import_keys_file(options['private_key_path'])

        self.stdout.write(self.style.SUCCESS('Successfully imported key'))
