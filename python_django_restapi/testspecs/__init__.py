import mockito

if not hasattr(mockito, 'stub'):
    # this is a workaround for 'sure' package that patches 'the whole world' and overwrites mockito.when
    # pylint: disable=invalid-name
    _mockito_when = mockito.when
    mockito.stub = _mockito_when
