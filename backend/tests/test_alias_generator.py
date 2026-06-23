from app.services.alias_generator import generate_dataset_aliases, normalize_text


def test_generate_aliases_for_huggingface_name():
    aliases = generate_dataset_aliases("m-a-p/MAP-CC")

    normalized = [normalize_text(a) for a in aliases]

    assert "map cc" in normalized
    assert "m a p map cc" in normalized


def test_generate_aliases_for_simple_name():
    aliases = generate_dataset_aliases("SST-2")

    normalized = [normalize_text(a) for a in aliases]

    assert "sst 2" in normalized