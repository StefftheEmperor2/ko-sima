class ComplexFilter:
    OPERATOR_AND = 'and'
    OPERATOR_OR = 'or'
    def __init__(self):
        self.operator = 'and'
        self.compounds = []

    def set_operator_and(self):
        self.operator = self.OPERATOR_AND
        return self

    def set_operator_or(self):
        self.operator = self.OPERATOR_OR
        return self

    def add_compound(self, compound):
        self.compounds.append(compound)
        return self

    def get_payload(self):
        compounds = []
        for compound in self.compounds:
            compounds.append(compound.get_payload())
        return {
            self.operator: compounds
        }

    def has_filter(self):
        if len(self.compounds) == 0:
            return False
        for compound in self.compounds:
            if isinstance(compound, SimpleFilter):
                return True
            if isinstance(compound, ComplexFilter):
                return compound.has_filter()
        return False

    def __len__(self):
        return len(self.compounds)


class SimpleFilter:
    OPERATOR_IS = 'is'
    OPERATOR_IS_NOT = 'isnot'
    OPERATOR_CONTAINS = 'contains'

    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value

    def get_payload(self):
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value
        }
