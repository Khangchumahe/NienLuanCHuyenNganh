import unittest

from services.rag_engine import RAGEngine


class RAGEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = RAGEngine.__new__(RAGEngine)
        self.engine.knowledge_base = []
        self.engine.document_frequency = {}
        self.engine.sync_knowledge_base = lambda: 0
        self.engine.knowledge_base = [
            {
                'product_id': 1,
                'product_name': 'Áo Sơ Mi Oxford',
                'category': 'Áo Nam',
                'price': 349000,
                'image_url': None,
                'material': 'Cotton Oxford',
                'style': 'Công sở, dự tiệc',
                'size_guide': (
                    'Size S: 1m55-1m64 (50-57kg) | '
                    'Size M: 1m65-1m72 (58-65kg) | '
                    'Size L: 1m70-1m78 (66-74kg)'
                ),
                'variants': [
                    {'color': 'Trắng', 'size': 'M', 'stock_quantity': 3},
                    {'color': 'Xanh', 'size': 'L', 'stock_quantity': 0},
                ],
                'total_stock': 3,
                'content': 'Áo Sơ Mi Oxford Áo Nam Cotton Công sở dự tiệc',
                'term_weights': {
                    'ao': 6.0, 'so': 3.0, 'mi': 3.0, 'oxford': 3.0,
                    'nam': 2.0, 'cotton': 1.5, 'cong': 1.5, 'so': 4.5,
                    'tiec': 1.5,
                },
                'tokens': ['ao', 'so', 'mi', 'oxford'],
                'size_ranges': RAGEngine._parse_size_ranges(
                    'Size S: 1m55-1m64 (50-57kg) | '
                    'Size M: 1m65-1m72 (58-65kg) | '
                    'Size L: 1m70-1m78 (66-74kg)'
                ),
            },
            {
                'product_id': 2,
                'product_name': 'Áo Khoác Gió',
                'category': 'Áo Khoác',
                'price': 360000,
                'image_url': None,
                'material': 'Polyester',
                'style': 'Đi phượt',
                'size_guide': 'Size M: 1m60-1m68 (54-63kg)',
                'variants': [
                    {'color': 'Đen', 'size': 'M', 'stock_quantity': 2},
                ],
                'total_stock': 2,
                'content': 'Áo Khoác Gió Áo Khoác Polyester Đi phượt',
                'term_weights': {
                    'ao': 3.0, 'khoac': 5.0, 'gio': 3.0,
                    'polyester': 1.5, 'phuot': 1.5,
                },
                'tokens': ['ao', 'khoac', 'gio'],
                'size_ranges': RAGEngine._parse_size_ranges(
                    'Size M: 1m60-1m68 (54-63kg)'
                ),
            },
        ]
        self.engine.document_frequency = {
            token: sum(token in doc['term_weights'] for doc in self.engine.knowledge_base)
            for doc in self.engine.knowledge_base
            for token in doc['term_weights']
        }

    def test_tokenizer_normalizes_vietnamese_and_preserves_measurements(self):
        self.assertEqual(
            self.engine._tokenize('Tôi cao 1m70, nặng 64kg tìm áo sơ mi'),
            ['cao', '1m70', 'nang', '64kg', 'ao', 'so', 'mi'],
        )

    def test_retrieval_prefers_matching_in_stock_size(self):
        results = self.engine.retrieve('áo sơ mi cao 1m70 nặng 64kg')

        self.assertEqual(results[0]['product_name'], 'Áo Sơ Mi Oxford')
        self.assertEqual(results[0]['recommended_size'], 'M')
        self.assertEqual(results[0]['available_sizes'], ['M'])

    def test_unavailable_size_is_not_recommended(self):
        results = self.engine.retrieve('áo sơ mi cao 1m75 nặng 70kg')

        self.assertEqual(results[0]['product_name'], 'Áo Sơ Mi Oxford')
        self.assertIsNone(results[0]['recommended_size'])
        self.assertEqual(
            [size['size'] for size in results[0]['matching_sizes']],
            ['L'],
        )

    def test_response_reports_size_and_stock_from_product_data(self):
        response = self.engine.generate_response('áo sơ mi cao 1m70 nặng 64kg')

        self.assertIn('size **M**', response['answer'])
        self.assertIn('Trắng - size M (còn 3)', response['answer'])
        self.assertEqual(
            response['rag_trace']['response_mode'],
            'deterministic_local_template',
        )
        self.assertEqual(response['rag_trace']['measurements']['height_cm'], 170)


if __name__ == '__main__':
    unittest.main()
