import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
import os
from src.application.services import IngestFileUseCase

class CsvHandler(FileSystemEventHandler):
    def __init__(self, use_case: IngestFileUseCase):
        self.use_case = use_case

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.csv'):
            print(f" [Watcher] New CSV detected: {event.src_path}")
            # Wait briefly for file write completion to avoid lock issues/partial reads
            time.sleep(1)
            self.use_case.execute(event.src_path)

    def on_modified(self, event):
        # Optional: Handle moved/modified, but usually creation is enough for "Inbox" pattern
        pass

class FileMonitorAdapter:
    def __init__(self, folder_path: str, use_case: IngestFileUseCase):
        self.folder_path = folder_path
        self.use_case = use_case
        self.observer = Observer()

    def start(self):
        print(f" [Watcher] Monitoring directory: {self.folder_path}")
        event_handler = CsvHandler(self.use_case)
        self.observer.schedule(event_handler, self.folder_path, recursive=False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()
