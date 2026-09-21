from django.core.management.base import BaseCommand, CommandError

from rag.local_rag import ingest


class Command(BaseCommand):
    help = "Embed PDF and text files into the local ChromaDB knowledge base."

    def add_arguments(self, parser):
        parser.add_argument("folder", help="Folder containing .pdf or .txt files")

    def handle(self, *args, **options):
        try:
            count = ingest(options["folder"])
        except (FileNotFoundError, NotADirectoryError, RuntimeError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Ingested {count} chunks."))
