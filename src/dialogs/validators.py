from PyQt6.QtGui import QIntValidator, QValidator
from PyQt6.QtCore import Qt

class NameValidator(QValidator):
    """Validator for template/capsule names"""
    def validate(self, input_str: str, pos: int) -> tuple[QValidator.State, str, int]:
        if not input_str:
            return QValidator.State.Intermediate, input_str, pos
        if ' ' in input_str:
            return QValidator.State.Invalid, input_str, pos
        return QValidator.State.Acceptable, input_str, pos

class PortValidator(QIntValidator):
    """Custom validator for port numbers"""
    def validate(self, input_str: str, pos: int) -> tuple[QValidator.State, str, int]:
        state, text, pos = super().validate(input_str, pos)
        if state == QValidator.State.Acceptable:
            try:
                if int(input_str) < self.bottom():
                    return QValidator.State.Invalid, input_str, pos
            except ValueError:
                return QValidator.State.Invalid, input_str, pos
        return state, text, pos

class HostPortValidator(PortValidator):
    """Validator for host ports (must be > 1024)"""
    def validate(self, input_str: str, pos: int) -> tuple[QValidator.State, str, int]:
        state, text, pos = super().validate(input_str, pos)
        if state == QValidator.State.Acceptable:
            try:
                if int(input_str) <= 1024:
                    return QValidator.State.Invalid, input_str, pos
            except ValueError:
                return QValidator.State.Invalid, input_str, pos
        return state, text, pos

class ContainerPortValidator(PortValidator):
    """Validator for container ports (can be any valid port)"""
    pass  # Uses default QIntValidator behavior