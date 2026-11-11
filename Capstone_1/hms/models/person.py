"""The abstract :class:`Person` base class used by every person in the hospital."""

from abc import ABC, abstractmethod


class Person(ABC):
    """Common identity and contact details for hospital people.

    ``age`` and ``phone`` are sensitive values. They are stored in the private
    attributes ``__age`` and ``__phone`` and can only be reached through
    properties, so every new value is validated before it is stored.

    ``Person`` is an abstract base class: it declares the contract
    (:meth:`get_details` and :meth:`get_role`) and cannot be instantiated.
    """

    #: Prefix used to build ids, e.g. ``P001``, ``D001``, ``N001``.
    _id_prefix = "X"
    #: One running counter per id prefix, shared by ``Person`` and all of its
    #: subclasses, so ``OutPatient`` and ``InPatient`` continue the same ``P``
    #: series (``P001``, ``P002``, ...) instead of restarting it.
    _id_counters = {}

    MIN_AGE = 0
    MAX_AGE = 120
    PHONE_LENGTH = 10

    def __init__(self, name, age, gender, phone):
        self._person_id = self._generate_id()
        self.name = name
        self.age = age
        self.gender = gender
        self.phone = phone

    # ------------------------------------------------------------ identifiers
    @classmethod
    def _generate_id(cls):
        """Return the next id for this class, e.g. ``P001`` for a patient."""
        prefix = cls._id_prefix
        cls._id_counters[prefix] = cls._id_counters.get(prefix, 0) + 1
        return f"{prefix}{cls._id_counters[prefix]:03d}"

    @classmethod
    def reset_id_counters(cls):
        """Reset every id counter (used by tests and by the sample data)."""
        cls._id_counters.clear()

    @property
    def person_id(self):
        """Read only id that was assigned when the person was created."""
        return self._person_id

    # ------------------------------------------------------- protected fields
    @property
    def age(self):
        """Age in years, always between :attr:`MIN_AGE` and :attr:`MAX_AGE`."""
        return self.__age

    @age.setter
    def age(self, value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("Age must be a whole number of years.")
        if not self.MIN_AGE <= value <= self.MAX_AGE:
            raise ValueError(f"Age must be between {self.MIN_AGE} and {self.MAX_AGE}.")
        self.__age = value

    @property
    def phone(self):
        """Contact number, always exactly :attr:`PHONE_LENGTH` digits."""
        return self.__phone

    @phone.setter
    def phone(self, value):
        text = str(value).strip()
        if len(text) != self.PHONE_LENGTH or not text.isdigit():
            raise ValueError("Phone number must be exactly 10 digits.")
        self.__phone = text

    # ------------------------------------------------------------------ traits
    @property
    def display_name(self):
        """Name as it should appear in messages."""
        return self.name

    # ---------------------------------------------------------------- contract
    @abstractmethod
    def get_details(self):
        """Return a human readable one line description of this person."""

    @abstractmethod
    def get_role(self):
        """Return the role name of this person, for example ``"Doctor"``."""

    # -------------------------------------------------------- object usability
    def __eq__(self, other):
        """Two people are equal when they share the same id (Module 8)."""
        if isinstance(other, Person):
            return self.person_id == other.person_id
        return NotImplemented

    def __hash__(self):
        """People are hashed by id, so equal people land in the same bucket."""
        return hash(self.person_id)

    def __str__(self):
        """Readable output for menus and reports, built on ``get_details()``."""
        return self.get_details()

    def __repr__(self):
        """Developer friendly output: enough to rebuild the object on paper."""
        return (
            f"{type(self).__name__}(person_id={self.person_id!r}, "
            f"name={self.name!r})"
        )


def print_all(items):
    """Print a mixed list of hospital objects.

    ``print_all`` only requires each object to answer ``get_details()``. That
    single protocol is enough to print patients, doctors, nurses,
    receptionists and vehicles (the ``Ambulance`` class, which is not a person)
    together, without a single ``isinstance`` check or type dispatch.
    """
    for item in items:
        print(item.get_details())

