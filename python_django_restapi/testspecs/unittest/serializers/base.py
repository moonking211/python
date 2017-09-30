class SerializerValidationTextMixin(object):
    def set_callee(self, callee):
        self.callee = callee

    def call(self, data):
        serializer = self.serializer()
        serializer._validated_data = {}
        self.errors = {}
        serializer.validated_data.update(data)
        method = getattr(serializer, self.callee)
        method(self.errors)
        return self.errors
