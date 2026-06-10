class DomainError(Exception):
    """Base exception for domain errors."""

class NotFoundError(DomainError):
    def __init__(self, entity: str, entity_id: object):
        self.entity = entity
        self.entity_id = entity_id
        super().__init__(f"{entity} con ID {entity_id} no encontrado")

class MedicationNotFoundError(NotFoundError):
    def __init__(self, medication_id: int):
        super().__init__("Medicamento", medication_id)

class OrderNotFoundError(NotFoundError):
    def __init__(self, order_id: int):
        super().__init__("Orden", order_id)

class ReportNotFoundError(NotFoundError):
    def __init__(self, report_id: int):
        super().__init__("Reporte", report_id)

class NotificationNotFoundError(NotFoundError):
    def __init__(self, notification_id: int):
        super().__init__("Notificación", notification_id)

class CategoryNotFoundError(NotFoundError):
    def __init__(self, category_id: int):
        super().__init__("Categoría", category_id)

class IntakeTypeNotFoundError(NotFoundError):
    def __init__(self, intake_type_id: int):
        super().__init__("Tipo de ingesta", intake_type_id)

class SupplierNotFoundError(NotFoundError):
    def __init__(self, supplier_id: int):
        super().__init__("Proveedor", supplier_id)

class LotNotFoundError(NotFoundError):
    def __init__(self, lot_id: int):
        super().__init__("Lote", lot_id)

class AuditNotFoundError(NotFoundError):
    def __init__(self, audit_id: int):
        super().__init__("Auditoría", audit_id)

class DeliveryNotFoundError(NotFoundError):
    def __init__(self, delivery_id: int):
        super().__init__("Entrega", delivery_id)

class ConditionNotFoundError(DomainError):
    def __init__(self, condition_id: int):
        self.condition_id = condition_id
        super().__init__(f"Condición con ID {condition_id} no encontrada")

class ForbiddenError(DomainError):
    def __init__(self, message: str = "No tiene permisos para realizar esta acción"):
        self.message = message
        super().__init__(message)

class ValidationError(DomainError):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
