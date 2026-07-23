def test_main_imports():
    """Catches import errors in the entry point, which no other test touches."""
    import main

    assert callable(main.main)
