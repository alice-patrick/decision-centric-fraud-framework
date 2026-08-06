class SuppressionEngine:
    def __init__(self):
        self.seen_entities = set()

    def apply(self, entity_id, decision):
        if not decision:
            return decision, False

        if entity_id in self.seen_entities:
            return False, True

        self.seen_entities.add(entity_id)
        return True, False