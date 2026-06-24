import unittest

from rag.source_formatter import extract_source_name, format_reference_sources


class RagSourcesTest(unittest.TestCase):
    def test_extract_source_name_supports_absolute_and_missing_sources(self):
        self.assertEqual(extract_source_name({"source": "/tmp/data/故障排除.txt"}), "故障排除.txt")
        self.assertEqual(extract_source_name({"source": "data/维护保养.txt"}), "维护保养.txt")
        self.assertEqual(extract_source_name({}), "未知来源")

    def test_format_reference_sources_deduplicates_in_order(self):
        metadata_list = [
            {"source": "/tmp/data/故障排除.txt"},
            {"source": "/tmp/data/维护保养.txt"},
            {"source": "/tmp/data/故障排除.txt"},
        ]

        self.assertEqual(format_reference_sources(metadata_list), "参考来源：故障排除.txt、维护保养.txt")


if __name__ == "__main__":
    unittest.main()
