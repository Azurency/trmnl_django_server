import logging
from enum import IntFlag, auto

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger("trmnl")


class Weekday(IntFlag):
    NONE = 0
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()
    SUNDAY = auto()

    @classmethod
    def choices(cls):
        """
        Return choices for use in forms or admin, with translations.
        """
        return [
            (cls.NONE.value, _("None")),
            (cls.MONDAY.value, _("Monday")),
            (cls.TUESDAY.value, _("Tuesday")),
            (cls.WEDNESDAY.value, _("Wednesday")),
            (cls.THURSDAY.value, _("Thursday")),
            (cls.FRIDAY.value, _("Friday")),
            (cls.SATURDAY.value, _("Saturday")),
            (cls.SUNDAY.value, _("Sunday")),
        ]

    @classmethod
    def from_bitmask(cls, bitmask):
        """
        Convert an integer bitmask to a Weekday Flag.
        """
        return cls(bitmask)

    def to_str_list(self):
        """
        Convert the Weekday Flag to a list of translated strings.
        """
        return [
            label
            for bitmask, label in WEEKDAYS_CHOICES
            if bitmask != 0 and self & bitmask
        ]

    def to_int_list(self):
        """
        Convert the Weekday Flag to a list of integers.
        """
        return [day.value for day in Weekday if self & day]

    @classmethod
    def from_int_list(cls, int_list):
        """
        Convert a list of integers to a Weekday Flag.
        """
        return cls(sum(int(x) for x in int_list))


# Define choices for weekdays
WEEKDAYS_CHOICES = [
    (0, _("None")),
    (1, _("Monday")),
    (2, _("Tuesday")),
    (4, _("Wednesday")),
    (8, _("Thursday")),
    (16, _("Friday")),
    (32, _("Saturday")),
    (64, _("Sunday")),
]

# Create a mapping for bitwise operations
WEEKDAYS_MAP = {label: bitmask for bitmask, label in WEEKDAYS_CHOICES if bitmask != 0}


class WeekdaysField(models.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs["default"] = kwargs.get("default", Weekday.NONE)
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None or value == 0:
            return Weekday.NONE
        return Weekday.from_bitmask(value)

    def to_python(self, value):
        if isinstance(value, int):
            # If it's an integer, convert to Weekday
            return Weekday.from_bitmask(value)
        elif isinstance(value, list):
            # If it's a list of int strings, convert to Weekday
            return Weekday.from_int_list(value)
        elif isinstance(value, Weekday):
            # If it's already a Weekday enum, return it
            return value
        elif value is None:
            return Weekday.NONE
        raise ValidationError(_("Invalid data type for WeekdaysField"))

    def formfield(self, **kwargs):
        defaults = {
            "form_class": WeekdaysFormField,
            "widget": forms.CheckboxSelectMultiple,
            "choices": Weekday.choices(),
        } | kwargs
        return super().formfield(**defaults)


class WeekdaysFormField(forms.MultipleChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = Weekday.choices()
        kwargs["widget"] = forms.CheckboxSelectMultiple()
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if isinstance(value, list):
            return [Weekday(int(x)) for x in value]
        if isinstance(value, Weekday):
            return value.to_int_list()
        return value
