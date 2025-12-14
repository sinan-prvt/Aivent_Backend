from django.apps import AppConfig
import threading

class VendorAppConfig(AppConfig):
    name = "vendor_app"

    def ready(self):
        from vendor_app.consumers.vendor_events import start_consumer
        threading.Thread(target=start_consumer, daemon=True).start()
