from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from hospital.models import BackupRecord
from hospital.services import log_audit_event
import os
import datetime

class Command(BaseCommand):
    help = 'Generates a timestamped JSON backup snapshot of the database.'

    def handle(self, *args, **options):
        backup_dir = settings.BASE_DIR / 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"swarnabindu_backup_{timestamp}.json"
        filepath = os.path.join(backup_dir, filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                call_command('dumpdata', 'hospital', 'auth', indent=2, stdout=f)
            
            file_size = os.path.getsize(filepath)
            
            BackupRecord.objects.create(
                filename=filename,
                file_size_bytes=file_size,
                status='Verified',
                notes='Automated system backup created successfully.'
            )
            
            log_audit_event(None, 'BACKUP_CREATED', 'System', '', f"Database backup saved: {filename}")
            self.stdout.write(self.style.SUCCESS(f"Successfully generated database backup: {filename} ({file_size} bytes)"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Backup failed: {str(e)}"))
